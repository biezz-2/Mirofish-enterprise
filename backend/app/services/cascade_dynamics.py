"""
MiroFish Enterprise Cascade Dynamics Service (Agent 13: Divisi D)
Model Transmisi Informasi dan Dinamika Viral:
- Rescorla-Wagner Reward Prediction Error: V <- V + alpha * (R - V)
- Marked Hawkes Self-Exciting Point Process: lambda(t) = mu + sum(alpha * mark * exp(-beta * dt))
- Granovetter 1978 Threshold Model untuk aktivasi perilaku kolektif.
"""

import math
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field

class HawkesEvent(BaseModel):
    timestamp: float
    user_influence_mark: float = 1.0  # Bobot mark (pengaruh pengguna)

class CascadeDynamicsEngine:
    """Simulates viral cascades, reward conditioning, and behavioral thresholds."""

    def __init__(self, rescorla_alpha: float = 0.25, hawkes_mu: float = 0.1, hawkes_beta: float = 0.5):
        self.alpha_rw = rescorla_alpha
        self.mu_hawkes = hawkes_mu
        self.beta_hawkes = hawkes_beta

    # 1. Rescorla-Wagner Reward Prediction Error
    def update_rescorla_wagner(self, current_v: float, received_reward: float) -> Tuple[float, float]:
        """
        Delta V = alpha * (R - V)
        V_new = V + Delta V
        Mengembalikan (V_new, prediction_error)
        """
        error = received_reward - current_v
        new_v = current_v + self.alpha_rw * error
        return round(new_v, 4), round(error, 4)

    # 2. Marked Hawkes Point Process Intensity
    def calculate_hawkes_intensity(
        self,
        current_time: float,
        history_events: List[HawkesEvent],
        alpha_decay: float = 0.8
    ) -> float:
        """
        lambda(t) = mu + sum_{t_i < t} alpha * mark_i * exp(-beta * (t - t_i))
        """
        intensity = self.mu_hawkes
        for ev in history_events:
            dt = current_time - ev.timestamp
            if dt > 0:
                intensity += alpha_decay * ev.user_influence_mark * math.exp(-self.beta_hawkes * dt)
        return round(intensity, 4)

    # 3. Mark Granovetter (1978) Threshold Model
    def evaluate_granovetter_activation(
        self,
        individual_threshold: float,
        active_peer_ratio: float
    ) -> bool:
        """
        Aktor mengadopsi perilaku jika rasio peers yang aktif >= ambang batas individual.
        """
        return active_peer_ratio >= individual_threshold
