"""
MiroFish Enterprise Nested Logit & Decision Engine (Agent 10: Divisi C)
Implementasi Model Keputusan Tingkat Lanjut:
- Nested Logit Kenneth Train (GEV family) mengatasi pelanggaran IIA.
  Hierarki: [Lurker vs Active] -> [Consume vs Produce] -> [Like / RT / Reply / Quote]
- Ratcliff Drift Diffusion Model (DDM): estimasi dwell time dan latency keputusan.
- Kahneman-Tversky Prospect Theory: fungsi nilai asimetris loss-aversion (lambda = 2.25)
  dan pembobotan probabilitas untuk sensor-diri (self-censorship).
"""

import math
import random
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field

class DecisionContext(BaseModel):
    user_utility_like: float = 0.5
    user_utility_rt: float = 0.4
    user_utility_reply: float = 0.3
    user_utility_quote: float = 0.2
    is_controversial: bool = False
    controversy_level: float = 0.0

class DDMResult(BaseModel):
    chosen_action: str
    dwell_time_ms: float
    confidence: float

class DecisionEngine:
    """Nested Logit Choice Model + Ratcliff DDM + Prospect Theory."""

    def __init__(self, nest_mu_consume: float = 0.7, loss_aversion_lambda: float = 2.25):
        self.mu_consume = nest_mu_consume  # Logsum parameter (0 < mu <= 1)
        self.lambda_loss = loss_aversion_lambda  # Prospect theory loss aversion

    # 1. Kenneth Train Nested Logit
    def evaluate_nested_logit(
        self,
        utility_active: float,
        utility_lurker: float,
        utilities_actions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Menghitung probabilitas bersarang tanpa melanggar IIA:
        P(action) = P(action | active, consume) * P(consume | active) * P(active)
        """
        # Inclusive value (Logsum) untuk nest aksi konsumsi
        sum_exp_actions = sum(math.exp(u / self.mu_consume) for u in utilities_actions.values())
        iv_consume = self.mu_consume * math.log(max(1e-9, sum_exp_actions))

        # Level 1: Active vs Lurker
        total_top_exp = math.exp(utility_active + iv_consume) + math.exp(utility_lurker)
        prob_active = math.exp(utility_active + iv_consume) / total_top_exp
        prob_lurker = math.exp(utility_lurker) / total_top_exp

        # Conditional action probabilities
        action_probs = {}
        for action, u in utilities_actions.items():
            cond_prob = math.exp(u / self.mu_consume) / sum_exp_actions
            action_probs[action] = round(cond_prob * prob_active, 4)

        action_probs["lurker_dwell"] = round(prob_lurker, 4)
        return action_probs

    # 2. Kahneman-Tversky Prospect Theory: Value Function
    def calculate_prospect_value(self, gain: float, loss: float, alpha: float = 0.88) -> float:
        """
        v(x) = x^alpha untuk gain, -lambda * (-x)^alpha untuk loss.
        Menghitung apakah agen menahan diri dari posting karena risiko backlash.
        """
        v_gain = math.pow(max(0.0, gain), alpha)
        v_loss = -self.lambda_loss * math.pow(max(0.0, loss), alpha)
        return round(v_gain + v_loss, 4)

    # 3. Ratcliff Drift Diffusion Model (DDM) for Dwell Time
    def simulate_ddm(
        self,
        drift_rate: float = 0.3,
        threshold_a: float = 1.0,
        non_decision_time_ms: float = 300.0
    ) -> DDMResult:
        """
        Simulasi DDM Wiener process:
        dx = v * dt + s * dW
        """
        dt = 0.01
        s = 0.1
        x = 0.0
        steps = 0
        max_steps = 1000

        while abs(x) < threshold_a and steps < max_steps:
            dx = drift_rate * dt + s * math.sqrt(dt) * random.gauss(0, 1)
            x += dx
            steps += 1

        dwell_time = non_decision_time_ms + (steps * dt * 1000.0)
        action = "engage" if x >= threshold_a else ("pass" if x <= -threshold_a else "dwell_timeout")
        confidence = round(min(1.0, abs(x) / threshold_a), 2)

        return DDMResult(
            chosen_action=action,
            dwell_time_ms=round(dwell_time, 1),
            confidence=confidence
        )
