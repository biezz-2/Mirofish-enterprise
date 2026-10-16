"""
MiroFish Enterprise Nested Logit & Decision Engine (Agent 10: Divisi C)
Implementasi Model Keputusan Tingkat Lanjut:
- Nested Logit Kenneth Train (GEV family) mengatasi pelanggaran IIA.
  Hierarki 3 Tingkat: [Root: Aktif vs Lurker] -> [Sub-Nest: Konsumsi vs Produksi] -> [Aksi: Like/RT/Browse vs Reply/Quote/Post]
- Ratcliff Drift Diffusion Model (DDM): estimasi dwell time dan latency keputusan (solusi analitik + simulasi stokastik).
- Kahneman-Tversky Prospect Theory: fungsi nilai asimetris loss-aversion (lambda = 2.25)
  dan pembobotan probabilitas Tversky-Kahneman / Prelec untuk sensor-diri (self-censorship).
- Swarm Predictive Sandbox: simulasi 100 agen swarm, validasi Pareto 90:10 lurker-to-contributor,
  deteksi anomali (Chilling Effect Spiral, Impulsive Polarization, Lurker Lock), dan rekomendasi kalibrasi downstream RecSys.
"""

import math
import random
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field


class DecisionContext(BaseModel):
    user_utility_like: float = 0.5
    user_utility_rt: float = 0.4
    user_utility_reply: float = 0.3
    user_utility_quote: float = 0.2
    user_utility_post: float = 0.2
    user_utility_browse: float = 0.6
    user_utility_active: float = 0.8
    user_utility_lurker: float = 0.5
    activation_barrier: float = 3.6
    production_barrier: float = 2.2
    is_controversial: bool = False
    controversy_level: float = 0.0
    audience_hostility: float = 0.0
    topic_polarization: float = 0.0
    potential_gain: float = 1.0
    potential_loss: float = 1.5
    perceived_backlash_prob: Optional[float] = None
    ddm_drift_rate: Optional[float] = None
    ddm_threshold_a: Optional[float] = None
    loss_aversion_lambda: Optional[float] = None
    risk_tolerance: float = 0.5


class DDMResult(BaseModel):
    chosen_action: str
    dwell_time_ms: float
    confidence: float
    decision_time_ms: float = 0.0
    boundary_reached: str = "upper"
    trajectory_steps: int = 0
    p_upper: float = 0.5
    mean_decision_time_ms: float = 0.0


class SelfCensorshipResult(BaseModel):
    is_censored: bool
    candidate_action: str
    executed_action: str
    prospect_value: float
    backlash_probability: float
    weighted_backlash_prob: float
    censorship_probability: float
    reason: str


class HierarchicalChoiceProbabilities(BaseModel):
    prob_active: float
    prob_lurker: float
    prob_consume_given_active: float
    prob_produce_given_active: float
    conditional_consume: Dict[str, float]
    conditional_produce: Dict[str, float]
    unconditional_actions: Dict[str, float]
    inclusive_values: Dict[str, float]


class DecisionOutcome(BaseModel):
    agent_id: str
    action: str
    is_active: bool
    is_production: bool
    is_consumption: bool
    is_lurker: bool
    is_censored: bool
    censorship_details: Optional[SelfCensorshipResult] = None
    ddm_result: Optional[DDMResult] = None
    dwell_time_ms: float = 0.0
    chosen_probability: float = 0.0
    all_probabilities: Dict[str, float] = Field(default_factory=dict)


class DecisionAnomaly(BaseModel):
    anomaly_type: str
    severity: str
    description: str
    trigger_metrics: Dict[str, float] = Field(default_factory=dict)


class SwarmDecisionResult(BaseModel):
    total_agents: int
    total_rounds: int
    pareto_lurker_ratio: float
    consumption_ratio: float
    production_ratio: float
    self_censorship_rate: float
    mean_dwell_time_ms: float
    std_dwell_time_ms: float
    anomalies: List[DecisionAnomaly] = Field(default_factory=list)
    has_deadlock: bool = False
    homeostasis_recovery_rounds: int = 0
    downstream_recsys_parameters: Dict[str, Any] = Field(default_factory=dict)


class DecisionEngine:
    """
    Kenneth Train Nested Logit, Ratcliff Drift Diffusion Model,
    dan Kahneman-Tversky Prospect Theory Engine.
    """

    def __init__(
        self,
        nest_mu_consume: float = 0.7,
        nest_mu_produce: float = 0.75,
        nest_mu_active: float = 0.8,
        loss_aversion_lambda: float = 2.25,
        random_seed: Optional[int] = None
    ):
        # Scale parameter untuk sub-nest (0 < mu <= 1)
        self.mu_consume = max(0.01, min(1.0, nest_mu_consume))
        self.mu_produce = max(0.01, min(1.0, nest_mu_produce))
        self.mu_active = max(0.01, min(1.0, nest_mu_active))
        self.lambda_loss = max(1.0, loss_aversion_lambda)
        if random_seed is not None:
            random.seed(random_seed)

    @staticmethod
    def _calculate_inclusive_value(utilities: Dict[str, float], mu: float) -> Tuple[float, float, Dict[str, float]]:
        """
        Menghitung Inclusive Value (Logsum) numerik stabil:
        IV = mu * (u_max / mu + ln(sum(exp((u - u_max) / mu))))
        Mengembalikan (IV, sum_exp, conditional_probs)
        """
        if not utilities:
            return 0.0, 1.0, {}
        u_max = max(utilities.values())
        exp_terms = {}
        for k, u in utilities.items():
            diff = (u - u_max) / mu
            diff_clamped = max(-60.0, min(60.0, diff))
            exp_terms[k] = math.exp(diff_clamped)

        sum_exp = sum(exp_terms.values())
        logsum = (u_max / mu + math.log(max(1e-12, sum_exp))) * mu

        cond_probs = {k: exp_v / max(1e-12, sum_exp) for k, exp_v in exp_terms.items()}
        return logsum, sum_exp, cond_probs

    # 1. Kenneth Train Nested Logit: Backward-Compatible 2-Level
    def evaluate_nested_logit(
        self,
        utility_active: float,
        utility_lurker: float,
        utilities_actions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        GEV Model: P(action) = P(action | Active) * P(Active).
        Inclusive value (logsum) untuk nest action:
        IV = mu * ln(sum(exp(U_j / mu)))
        """
        if not utilities_actions:
            return {"lurker_dwell": 1.0}

        sum_exp_actions = sum(math.exp(u / self.mu_consume) for u in utilities_actions.values())
        iv_consume = self.mu_consume * math.log(max(1e-12, sum_exp_actions))

        # Level 1: Active vs Lurker
        total_top_exp = math.exp(utility_active + iv_consume) + math.exp(utility_lurker)
        prob_active = math.exp(utility_active + iv_consume) / max(1e-12, total_top_exp)
        prob_lurker = math.exp(utility_lurker) / max(1e-12, total_top_exp)

        # Conditional action probabilities
        action_probs = {}
        for action, u in utilities_actions.items():
            cond_prob = math.exp(u / self.mu_consume) / max(1e-12, sum_exp_actions)
            action_probs[action] = round(cond_prob * prob_active, 4)

        action_probs["lurker_dwell"] = round(prob_lurker, 4)
        return action_probs

    # 1.b Kenneth Train Hierarchical Nested Logit (3-Level Architecture)
    def evaluate_hierarchical_nested_logit(
        self,
        utility_active: float,
        utility_lurker: float,
        utilities_consume: Dict[str, float],
        utilities_produce: Dict[str, float],
        mu_active: Optional[float] = None,
        mu_consume: Optional[float] = None,
        mu_produce: Optional[float] = None
    ) -> HierarchicalChoiceProbabilities:
        """
        Hierarki 3 Tingkat Kenneth Train (GEV):
        Root Level: Active vs Lurker
        Sub-Nest Level (Active): Consume vs Produce
        Elemental Level:
          - Consume: e.g. like, retweet, browse
          - Produce: e.g. reply, quote, post
        """
        m_act = mu_active or self.mu_active
        m_cons = mu_consume or self.mu_consume
        m_prod = mu_produce or self.mu_produce

        # Level 3 Logsums
        iv_consume, _, cond_consume = self._calculate_inclusive_value(utilities_consume, m_cons)
        iv_produce, _, cond_produce = self._calculate_inclusive_value(utilities_produce, m_prod)

        # Level 2 Logsums (Consume vs Produce under Active)
        v_branches = {
            "consume": iv_consume,
            "produce": iv_produce
        }
        iv_active, _, cond_branches = self._calculate_inclusive_value(v_branches, m_act)

        # Level 1: Active vs Lurker (Kenneth Train GEV: V_active = U_active + mu_active * IV_active)
        v_active_total = utility_active + (m_act * iv_active)
        v_max_top = max(v_active_total, utility_lurker)
        exp_active = math.exp(max(-60.0, min(60.0, v_active_total - v_max_top)))
        exp_lurker = math.exp(max(-60.0, min(60.0, utility_lurker - v_max_top)))
        denom_top = exp_active + exp_lurker

        prob_active = exp_active / denom_top
        prob_lurker = exp_lurker / denom_top

        prob_consume_given_active = cond_branches.get("consume", 0.5)
        prob_produce_given_active = cond_branches.get("produce", 0.5)

        # Unconditional Joint Probabilities
        unconditional = {}
        for action, p_cond in cond_consume.items():
            unconditional[action] = round(p_cond * prob_consume_given_active * prob_active, 5)

        for action, p_cond in cond_produce.items():
            unconditional[action] = round(p_cond * prob_produce_given_active * prob_active, 5)

        unconditional["lurker_dwell"] = round(prob_lurker, 5)

        # Renormalize slightly if rounding caused minor delta
        total_p = sum(unconditional.values())
        if total_p > 0 and abs(total_p - 1.0) > 1e-5:
            unconditional = {k: round(v / total_p, 5) for k, v in unconditional.items()}

        inclusive_values = {
            "iv_consume": round(iv_consume, 4),
            "iv_produce": round(iv_produce, 4),
            "iv_active": round(iv_active, 4)
        }

        return HierarchicalChoiceProbabilities(
            prob_active=round(prob_active, 5),
            prob_lurker=round(prob_lurker, 5),
            prob_consume_given_active=round(prob_consume_given_active, 5),
            prob_produce_given_active=round(prob_produce_given_active, 5),
            conditional_consume={k: round(v, 5) for k, v in cond_consume.items()},
            conditional_produce={k: round(v, 5) for k, v in cond_produce.items()},
            unconditional_actions=unconditional,
            inclusive_values=inclusive_values
        )

    # 2. Kahneman-Tversky Prospect Theory: Value Function & Weighting
    def calculate_prospect_value(
        self,
        gain: float,
        loss: float,
        alpha: float = 0.88,
        beta: float = 0.88,
        lambda_param: Optional[float] = None
    ) -> float:
        """
        v(x) = x^alpha untuk gain, -lambda * (-x)^beta untuk loss.
        Menghitung apakah agen menahan diri dari posting karena risiko backlash.
        """
        lam = lambda_param if lambda_param is not None else self.lambda_loss
        v_gain = math.pow(max(0.0, float(gain)), alpha)
        v_loss = -lam * math.pow(max(0.0, float(loss)), beta)
        return round(v_gain + v_loss, 4)

    def probability_weighting(
        self,
        p: float,
        gamma: float = 0.61,
        method: str = "tversky_kahneman"
    ) -> float:
        """
        Pembobotan probabilitas non-linear:
        - Tversky-Kahneman (1992): w(p) = p^gamma / (p^gamma + (1-p)^gamma)^(1/gamma)
        - Prelec (1998): w(p) = exp(-(-ln(p))^gamma)
        Menjelaskan overweighting probabilitas kecil ancaman backlash.
        """
        p_clamped = max(0.0, min(1.0, float(p)))
        if p_clamped <= 1e-6:
            return 0.0
        if p_clamped >= 1.0 - 1e-6:
            return 1.0

        if method == "prelec":
            return math.exp(-((-math.log(p_clamped)) ** gamma))

        # Default: Tversky & Kahneman (1992)
        p_g = math.pow(p_clamped, gamma)
        om_p_g = math.pow(1.0 - p_clamped, gamma)
        denom = math.pow(p_g + om_p_g, 1.0 / gamma)
        return p_g / max(1e-12, denom)

    # 2.b Sensor-Diri (Self-Censorship Mechanism)
    def evaluate_self_censorship(
        self,
        candidate_action: str,
        context: DecisionContext,
        lambda_param: Optional[float] = None,
        risk_tolerance: float = 0.5
    ) -> SelfCensorshipResult:
        """
        Model Sensor-Diri Berdasarkan Cumulative Prospect Theory:
        Agen mengevaluasi potensi keuntungan sosial vs potensi kerugian backlash publik.
        Jika nilai prospek jatuh di bawah ambang batas toleransi risiko, aksi dibatalkan/didowngrade.
        """
        lam = lambda_param if lambda_param is not None else (context.loss_aversion_lambda or self.lambda_loss)
        r_tol = context.risk_tolerance if context.risk_tolerance is not None else risk_tolerance

        is_produce = candidate_action in ["post", "reply", "quote"]
        if not is_produce or (not context.is_controversial and context.controversy_level <= 0.05):
            return SelfCensorshipResult(
                is_censored=False,
                candidate_action=candidate_action,
                executed_action=candidate_action,
                prospect_value=0.0,
                backlash_probability=0.0,
                weighted_backlash_prob=0.0,
                censorship_probability=0.0,
                reason="Tindakan aman atau non-produksi tanpa kontroversi"
            )

        if context.perceived_backlash_prob is not None:
            p_backlash = max(0.01, min(0.99, context.perceived_backlash_prob))
        else:
            c = max(0.0, min(1.0, context.controversy_level))
            h = max(0.0, min(1.0, context.audience_hostility))
            pol = max(0.0, min(1.0, context.topic_polarization))
            p_backlash = max(0.01, min(0.99, c * (0.35 + 0.40 * h + 0.25 * pol)))

        p_gain = 1.0 - p_backlash
        w_gain = self.probability_weighting(p_gain, gamma=0.61)
        w_loss = self.probability_weighting(p_backlash, gamma=0.69)

        v_gain = math.pow(max(0.0, context.potential_gain), 0.88)
        v_loss = -lam * math.pow(max(0.0, context.potential_loss), 0.88)

        prospect_val = w_gain * v_gain + w_loss * v_loss

        # Ambang batas sensor diri: semakin rendah risk_tolerance, semakin tinggi ambang batas
        threshold = 0.50 - 3.0 * r_tol

        # Logit probability of self-censorship
        temp = 0.35
        logit_arg = max(-30.0, min(30.0, (threshold - prospect_val) / temp))
        prob_censor = 1.0 / (1.0 + math.exp(-logit_arg))

        is_censored = prob_censor >= 0.50

        if is_censored:
            # Downgrade: mundur menjadi lurker membaca atau tidak bicara
            executed = "lurker_dwell"
            reason = f"Nilai prospek {prospect_val:.3f} di bawah ambang {threshold:.3f} (prob sensor: {prob_censor:.2f})"
        else:
            executed = candidate_action
            reason = f"Nilai prospek {prospect_val:.3f} diterima sesuai toleransi risiko {r_tol:.2f}"

        return SelfCensorshipResult(
            is_censored=is_censored,
            candidate_action=candidate_action,
            executed_action=executed,
            prospect_value=round(prospect_val, 4),
            backlash_probability=round(p_backlash, 4),
            weighted_backlash_prob=round(w_loss, 4),
            censorship_probability=round(prob_censor, 4),
            reason=reason
        )

    # 3. Ratcliff Drift Diffusion Model (DDM) for Dwell Time: Simulation & Analytical
    def simulate_ddm(
        self,
        drift_rate: float = 0.3,
        threshold_a: float = 1.0,
        non_decision_time_ms: float = 300.0,
        s: float = 0.1,
        dt: float = 0.01,
        max_steps: int = 1000
    ) -> DDMResult:
        """
        Simulasi DDM Wiener process (Euler-Maruyama):
        dx = v * dt + s * dW
        """
        x = 0.0
        steps = 0

        while abs(x) < threshold_a and steps < max_steps:
            dx = drift_rate * dt + s * math.sqrt(dt) * random.gauss(0, 1)
            x += dx
            steps += 1

        decision_time_ms = steps * dt * 1000.0
        dwell_time = non_decision_time_ms + decision_time_ms
        action = "engage" if x >= threshold_a else ("pass" if x <= -threshold_a else "dwell_timeout")
        boundary = "upper" if x >= threshold_a else ("lower" if x <= -threshold_a else "timeout")
        confidence = round(min(1.0, abs(x) / threshold_a), 2)

        # Analytical probability of hitting upper boundary
        p_up, _, _ = self.analytical_ddm(drift_rate, threshold_a, s, non_decision_time_ms)

        return DDMResult(
            chosen_action=action,
            dwell_time_ms=round(dwell_time, 1),
            confidence=confidence,
            decision_time_ms=round(decision_time_ms, 1),
            boundary_reached=boundary,
            trajectory_steps=steps,
            p_upper=p_up,
            mean_decision_time_ms=round(decision_time_ms, 1)
        )

    def analytical_ddm(
        self,
        drift_rate: float,
        threshold_a: float = 1.0,
        s: float = 0.1,
        non_decision_time_ms: float = 300.0
    ) -> Tuple[float, float, float]:
        """
        Solusi analitik closed-form untuk two-boundary DDM:
        - P(upper) = 1 / (1 + exp(-2*v*a/s^2))
        - E[T] = T_er + (a/v) * tanh(v*a/s^2)
        - Var[T] = (a*s^2 / v^3)*tanh(v*a/s^2) - (a^2 / (v^2 * cosh^2(v*a/s^2)))
        Mengembalikan (P_upper, mean_rt_ms, var_rt_ms)
        """
        a = max(0.01, threshold_a)
        s_sq = max(1e-6, s * s)

        if abs(drift_rate) < 1e-6:
            p_upper = 0.5
            mean_dt_sec = (a * a) / s_sq
            var_dt_sec = (2.0 / 3.0) * (a ** 4) / (s_sq ** 2)
        else:
            arg = max(-60.0, min(60.0, 2.0 * drift_rate * a / s_sq))
            p_upper = 1.0 / (1.0 + math.exp(-arg))

            th_arg = max(-30.0, min(30.0, drift_rate * a / s_sq))
            mean_dt_sec = (a / drift_rate) * math.tanh(th_arg)

            cosh_val = math.cosh(th_arg)
            var_dt_sec = (a * s_sq / (drift_rate ** 3)) * math.tanh(th_arg) - (a * a / ((drift_rate ** 2) * (cosh_val ** 2)))

        mean_rt_ms = non_decision_time_ms + (mean_dt_sec * 1000.0)
        var_rt_ms = max(0.0, var_dt_sec * (1000.0 ** 2))

        return round(p_upper, 4), round(mean_rt_ms, 2), round(var_rt_ms, 2)

    # 4. Orchestrasi Keputusan Agen Tunggal (Agent 08 & 09 Adapter)
    def decide_agent_action(
        self,
        context: DecisionContext,
        agent_id: str = "agent-0",
        needs_state: Optional[Any] = None,
        psy_rec: Optional[Any] = None,
        hour: int = 12
    ) -> DecisionOutcome:
        """
        Menjalankan alur keputusan holistik:
        1. Adaptasi utilitas dari Agent 08 (Psychometrics) & Agent 09 (Needs ODE).
        2. Evaluasi 3-Level Hierarchical Nested Logit.
        3. Sampling kandidat aksi.
        4. Evaluasi Sensor-Diri (Kahneman-Tversky Prospect Theory).
        5. Simulasi DDM Dwell Time & konfidensi.
        """
        u_active = context.user_utility_active
        u_lurker = context.user_utility_lurker
        u_consume = {
            "like": context.user_utility_like,
            "retweet": context.user_utility_rt,
            "browse": context.user_utility_browse
        }
        u_produce = {
            "reply": context.user_utility_reply,
            "quote": context.user_utility_quote,
            "post": context.user_utility_post
        }
        drift_rate = context.ddm_drift_rate or 0.30
        threshold_a = context.ddm_threshold_a or 1.0
        lam = context.loss_aversion_lambda or self.lambda_loss
        r_tol = context.risk_tolerance

        # Ekstraksi rekomendasi downstream Agent 08
        if psy_rec is not None:
            rec_dict = psy_rec if isinstance(psy_rec, dict) else (psy_rec.model_dump() if hasattr(psy_rec, "model_dump") else psy_rec.__dict__)
            a10_rec = rec_dict.get("agent_10_decision", {})
            u_lurker = a10_rec.get("adjusted_utility_lurker", u_lurker)
            drift_rate = a10_rec.get("ddm_drift_rate", drift_rate)
            lam = a10_rec.get("prospect_lambda_loss", lam)
            r_tol = a10_rec.get("risk_tolerance", r_tol)

        # Ekstraksi utilitas dinamis Agent 09
        if needs_state is not None:
            from app.services.humanoid_needs import HumanoidNeedsEngine
            n_eng = HumanoidNeedsEngine()
            n_utils = n_eng.get_decision_utilities(needs_state, hour=hour)
            u_active = n_utils.get("utility_active", u_active)
            if psy_rec is None:
                u_lurker = n_utils.get("utility_lurker", u_lurker)
            drift_rate += n_utils.get("ddm_drift_modifier", 0.0)
            lam *= (1.0 + n_utils.get("prospect_loss_modifier", 0.0))

            act_u = n_utils.get("action_utilities", {})
            if "like" in act_u:
                u_consume["like"] = act_u["like"]
            if "retweet" in act_u:
                u_consume["retweet"] = act_u["retweet"]
            if "reply" in act_u:
                u_produce["reply"] = act_u["reply"]
            if "quote" in act_u:
                u_produce["quote"] = act_u["quote"]

        # Terapkan cognitive friction & production barrier
        u_active_net = u_active - context.activation_barrier
        u_produce_net = {k: v - context.production_barrier for k, v in u_produce.items()}

        # Evaluasi Hierarchical Nested Logit
        hier_probs = self.evaluate_hierarchical_nested_logit(
            utility_active=u_active_net,
            utility_lurker=u_lurker,
            utilities_consume=u_consume,
            utilities_produce=u_produce_net
        )

        # Sampling aksi
        actions = list(hier_probs.unconditional_actions.keys())
        weights = [hier_probs.unconditional_actions[a] for a in actions]
        chosen_action = random.choices(actions, weights=weights, k=1)[0]
        chosen_p = hier_probs.unconditional_actions[chosen_action]

        # Evaluasi Sensor Diri
        censorship_res = None
        executed_action = chosen_action
        is_censored = False

        if chosen_action in ["post", "reply", "quote"] and (context.is_controversial or context.controversy_level > 0.05):
            censorship_res = self.evaluate_self_censorship(
                candidate_action=chosen_action,
                context=context,
                lambda_param=lam,
                risk_tolerance=r_tol
            )
            is_censored = censorship_res.is_censored
            executed_action = censorship_res.executed_action

        # Simulasi DDM Dwell Time
        ddm_res = self.simulate_ddm(
            drift_rate=max(0.05, drift_rate),
            threshold_a=threshold_a,
            non_decision_time_ms=300.0
        )

        # Dwell time reading untuk lurker vs active
        if executed_action == "lurker_dwell":
            reading_dwell = 800.0 + random.uniform(200.0, 1500.0)
            total_dwell = round(ddm_res.dwell_time_ms + reading_dwell, 1)
        else:
            total_dwell = ddm_res.dwell_time_ms

        return DecisionOutcome(
            agent_id=agent_id,
            action=executed_action,
            is_active=executed_action != "lurker_dwell",
            is_production=executed_action in ["post", "reply", "quote"],
            is_consumption=executed_action in ["like", "retweet", "browse"],
            is_lurker=executed_action == "lurker_dwell",
            is_censored=is_censored,
            censorship_details=censorship_res,
            ddm_result=ddm_res,
            dwell_time_ms=total_dwell,
            chosen_probability=round(chosen_p, 5),
            all_probabilities=hier_probs.unconditional_actions
        )

    # 5. Swarm Simulation & Predictive Sandbox (Divisi SIM)
    def run_swarm_decision_simulation(
        self,
        agents_count: int = 100,
        rounds: int = 25,
        controversy_shock_round: Optional[int] = 10,
        shock_controversy_level: float = 0.85,
        base_controversy_level: float = 0.15,
        random_seed: int = 42
    ) -> SwarmDecisionResult:
        """
        Simulasi Swarm 100 Agen (Validasi Pareto 90:10 & Deteksi Anomali):
        - Menguji respons swarm terhadap lonjakan kontroversi (*Controversy Shock*).
        - Memverifikasi rasio pareto lurker vs kontributor aktif.
        - Mendeteksi anomali: Chilling Effect Spiral, Impulsive Polarization, Lurker Lock.
        - Menghitung waktu pemulihan homeostasis (*recovery rounds*).
        """
        random.seed(random_seed)
        from app.services.psychometrics import PsychometricsEngine
        from app.services.humanoid_needs import HumanoidNeedsEngine

        psy_engine = PsychometricsEngine(random_seed=random_seed)
        needs_engine = HumanoidNeedsEngine(random_seed=random_seed)

        pop_traits = psy_engine.generate_archetype_population(n_agents=agents_count)
        pop_needs = needs_engine.generate_population(n_agents=agents_count)

        all_actions: List[str] = []
        dwell_times: List[float] = []
        censored_count = 0
        produce_attempts = 0

        round_metrics = []

        for r in range(rounds):
            # Penentuan level kontroversi per round (adanya shock pada round tertentu)
            if controversy_shock_round is not None and controversy_shock_round <= r <= controversy_shock_round + 2:
                c_level = shock_controversy_level
                is_controversial = True
                hostility = 0.70
                polarization = 0.65
            elif controversy_shock_round is not None and r > controversy_shock_round + 2:
                # Decay pemulihan kontroversi pasca shock
                decay = math.exp(-0.4 * (r - (controversy_shock_round + 2)))
                c_level = base_controversy_level + (shock_controversy_level - base_controversy_level) * decay
                is_controversial = c_level > 0.40
                hostility = 0.40 * decay
                polarization = 0.35 * decay
            else:
                c_level = base_controversy_level
                is_controversial = False
                hostility = 0.10
                polarization = 0.10

            hour = (8 + r) % 24
            r_lurk = 0
            r_consume = 0
            r_produce = 0
            r_censored = 0
            r_attempts = 0
            r_dwells = []

            for i in range(agents_count):
                trait = pop_traits[i]
                p_state = psy_engine.sample_state(trait)
                rec = psy_engine.get_downstream_recommendation(p_state, agent_id=f"agent-{i}")
                n_state = pop_needs[i]

                ctx = DecisionContext(
                    is_controversial=is_controversial,
                    controversy_level=c_level,
                    audience_hostility=hostility,
                    topic_polarization=polarization,
                    potential_gain=1.0,
                    potential_loss=1.8,
                    # Calibrate lurker baseline to match 90:10 Pareto ratio
                    user_utility_active=0.15,
                    user_utility_lurker=0.95
                )

                outcome = self.decide_agent_action(
                    context=ctx,
                    agent_id=f"agent-{i}",
                    needs_state=n_state,
                    psy_rec=rec,
                    hour=hour
                )

                all_actions.append(outcome.action)
                dwell_times.append(outcome.dwell_time_ms)
                r_dwells.append(outcome.dwell_time_ms)

                if outcome.is_lurker:
                    r_lurk += 1
                elif outcome.is_consumption:
                    r_consume += 1
                elif outcome.is_production:
                    r_produce += 1

                if outcome.is_censored:
                    censored_count += 1
                    r_censored += 1

                if outcome.censorship_details is not None or outcome.is_production:
                    produce_attempts += 1
                    r_attempts += 1

            round_metrics.append({
                "round": r,
                "controversy": c_level,
                "lurk_ratio": r_lurk / agents_count,
                "consume_ratio": r_consume / agents_count,
                "produce_ratio": r_produce / agents_count,
                "censor_rate": (r_censored / max(1, r_attempts)),
                "mean_dwell": sum(r_dwells) / len(r_dwells)
            })

        total_decisions = len(all_actions)
        lurker_count = sum(1 for a in all_actions if a == "lurker_dwell")
        consume_count = sum(1 for a in all_actions if a in ["like", "retweet", "browse"])
        produce_count = sum(1 for a in all_actions if a in ["post", "reply", "quote"])

        pareto_lurker_ratio = round(lurker_count / total_decisions, 3)
        consumption_ratio = round(consume_count / total_decisions, 3)
        production_ratio = round(produce_count / total_decisions, 3)
        self_censorship_rate = round(censored_count / max(1, produce_attempts), 3)

        mean_dwell = round(sum(dwell_times) / len(dwell_times), 1)
        variance_dwell = sum((d - mean_dwell) ** 2 for d in dwell_times) / len(dwell_times)
        std_dwell = round(math.sqrt(variance_dwell), 1)

        # Deteksi Anomali
        anomalies: List[DecisionAnomaly] = []

        # 1. Chilling Effect Spiral (Spiral of Silence)
        shock_rounds = [m for m in round_metrics if m["controversy"] >= 0.70]
        if shock_rounds:
            avg_shock_censor = sum(m["censor_rate"] for m in shock_rounds) / len(shock_rounds)
            avg_shock_produce = sum(m["produce_ratio"] for m in shock_rounds) / len(shock_rounds)
            if avg_shock_censor >= 0.70 or avg_shock_produce < 0.02:
                anomalies.append(DecisionAnomaly(
                    anomaly_type="CHILLING_EFFECT_SPIRAL",
                    severity="warning",
                    description=f"Lonjakan kontroversi memicu spiral sensor-diri (censor rate {avg_shock_censor:.1%}, produksi anjlok ke {avg_shock_produce:.1%}).",
                    trigger_metrics={
                        "avg_shock_censor_rate": round(avg_shock_censor, 3),
                        "avg_shock_produce_ratio": round(avg_shock_produce, 3)
                    }
                ))

        # 2. Impulsive Polarization (Ultra-fast reaction tanpa sensor-diri di konten kontroversial)
        low_latency_impulsive = [m for m in round_metrics if m["controversy"] > 0.50 and m["mean_dwell"] < 400.0 and m["censor_rate"] < 0.10]
        if low_latency_impulsive:
            anomalies.append(DecisionAnomaly(
                anomaly_type="IMPULSIVE_POLARIZATION",
                severity="critical",
                description="Terdeteksi reaktivitas impulsif ultra-cepat tanpa deliberasi atau sensor diri pada topik terpolarisasi.",
                trigger_metrics={"impulsive_rounds_count": len(low_latency_impulsive)}
            ))

        # 3. Lurker Lock / Total Apathy (Lurker > 98%)
        if pareto_lurker_ratio >= 0.98 or production_ratio == 0.0:
            anomalies.append(DecisionAnomaly(
                anomaly_type="LURKER_LOCK",
                severity="critical",
                description="Populasi swarm terjebak dalam total apati / lurker lock (produksi 0%).",
                trigger_metrics={"pareto_lurker_ratio": pareto_lurker_ratio}
            ))

        # Hitung Homeostasis Recovery Rounds
        recovery_rounds = 0
        if controversy_shock_round is not None:
            baseline_produce = sum(m["produce_ratio"] for m in round_metrics[:controversy_shock_round]) / max(1, controversy_shock_round)
            post_shock_start = controversy_shock_round + 3
            for r_idx in range(post_shock_start, len(round_metrics)):
                curr_produce = round_metrics[r_idx]["produce_ratio"]
                if curr_produce >= baseline_produce * 0.80:
                    recovery_rounds = r_idx - post_shock_start + 1
                    break
            if recovery_rounds == 0 and post_shock_start < len(round_metrics):
                recovery_rounds = len(round_metrics) - post_shock_start

        # Parameter Rekomendasi Downstream untuk RecSys Funnel (Agent 11)
        recsys_params = self._generate_recsys_downstream_recommendation(
            chilling_effect=any(a.anomaly_type == "CHILLING_EFFECT_SPIRAL" for a in anomalies),
            lurker_ratio=pareto_lurker_ratio,
            censor_rate=self_censorship_rate
        )

        has_deadlock = any(a.severity == "critical" for a in anomalies)

        return SwarmDecisionResult(
            total_agents=agents_count,
            total_rounds=rounds,
            pareto_lurker_ratio=pareto_lurker_ratio,
            consumption_ratio=consumption_ratio,
            production_ratio=production_ratio,
            self_censorship_rate=self_censorship_rate,
            mean_dwell_time_ms=mean_dwell,
            std_dwell_time_ms=std_dwell,
            anomalies=anomalies,
            has_deadlock=has_deadlock,
            homeostasis_recovery_rounds=recovery_rounds,
            downstream_recsys_parameters=recsys_params
        )

    def _generate_recsys_downstream_recommendation(
        self,
        chilling_effect: bool,
        lurker_ratio: float,
        censor_rate: float
    ) -> Dict[str, Any]:
        """
        Menghasilkan parameter terkalibrasi untuk downstream RecSys Funnel (Agent 11):
        - damping_factor: peredam echo-chamber
        - candidate_limit: jumlah kandidat Stage 1
        - epsilon: probabilitas eksplorasi
        """
        if chilling_effect:
            # Perlu diversifikasi moderat untuk mencairkan chilling effect
            damping = 0.75
            epsilon = 0.10
            candidate_limit = 60
            reason = "Chilling effect terdeteksi: naikkan damping dan epsilon untuk mendiversifikasi feed tanpa memicu polarisasi."
        elif lurker_ratio > 0.95:
            # Apati tinggi: dorong konten konsumsi berdaya tarik tinggi
            damping = 0.50
            epsilon = 0.08
            candidate_limit = 40
            reason = "Apati lurker tinggi: gunakan damping moderat dengan ranking relevansi kuat."
        else:
            # Kondisi stabil seimbang
            damping = 0.60
            epsilon = 0.05
            candidate_limit = 50
            reason = "Parameter seimbang standar untuk feed stabil."

        return {
            "recommended_damping_factor": damping,
            "recommended_candidate_limit": candidate_limit,
            "recommended_epsilon": epsilon,
            "rationale": reason
        }

    def get_recsys_downstream_recommendation(self, swarm_result: SwarmDecisionResult) -> Dict[str, Any]:
        """Accessor publik untuk downstream recommendation."""
        return swarm_result.downstream_recsys_parameters
