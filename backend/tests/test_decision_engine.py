"""
Unit and Integration Tests for MiroFish Enterprise Decision Engine (Agent 10: Divisi C)
Mencakup:
1. Kenneth Train Nested Logit (GEV model): Backward compatibility & 3-level hierarchy.
2. Relaksasi IIA (Independence of Irrelevant Alternatives) lintas nest.
3. Inclusive Value (Logsum) numerik stabil & skala mu.
4. Ratcliff Drift Diffusion Model (DDM): Solusi analitik closed-form vs simulasi stokastik.
5. Modulasi psikologis DDM (afek, drift rate, dwell time).
6. Kahneman-Tversky Cumulative Prospect Theory: Loss aversion (lambda = 2.25) & S-curve.
7. Pembobotan probabilitas non-linear (overweighting risiko backlash kecil).
8. Mekanisme Sensor-Diri (Self-Censorship / Chilling Effect) pada konten berisiko.
9. Integrasi End-to-End dengan Agent 08 (Psychometrics) & Agent 09 (Humanoid Needs ODE).
10. Swarm Predictive Sandbox: Validasi Pareto 90:10 lurker-to-contributor rule.
11. Deteksi Anomali (Chilling Effect Spiral, Impulsive Polarization) & Handoff ke Agent 11 RecSys Funnel.
"""

import math
import pytest
from app.services.decision_engine import (
    DecisionContext,
    DDMResult,
    SelfCensorshipResult,
    HierarchicalChoiceProbabilities,
    DecisionOutcome,
    DecisionAnomaly,
    SwarmDecisionResult,
    DecisionEngine,
)
from app.services.psychometrics import PsychometricsEngine, BigFiveTrait
from app.services.humanoid_needs import HumanoidNeedsEngine, HumanoidNeedsState, EkmanEmotions


# 1. Test Backward Compatibility of evaluate_nested_logit
def test_nested_logit_backward_compatibility():
    engine = DecisionEngine(nest_mu_consume=0.7)
    utilities = {"like": 0.8, "retweet": 0.6, "reply": 0.4}
    probs = engine.evaluate_nested_logit(utility_active=1.0, utility_lurker=0.5, utilities_actions=utilities)

    assert "like" in probs
    assert "retweet" in probs
    assert "reply" in probs
    assert "lurker_dwell" in probs
    total_p = sum(probs.values())
    assert abs(total_p - 1.0) < 0.05
    # Like has highest utility, should have highest active probability
    assert probs["like"] > probs["retweet"] > probs["reply"]


# 2. Test 3-Level Hierarchical Nested Logit (Train GEV Architecture)
def test_hierarchical_nested_logit_3_levels():
    engine = DecisionEngine(nest_mu_active=0.8, nest_mu_consume=0.7, nest_mu_produce=0.75)
    u_consume = {"like": 0.9, "retweet": 0.6, "browse": 0.7}
    u_produce = {"reply": 0.5, "quote": 0.4, "post": 0.3}

    res = engine.evaluate_hierarchical_nested_logit(
        utility_active=0.8,
        utility_lurker=0.6,
        utilities_consume=u_consume,
        utilities_produce=u_produce
    )

    assert isinstance(res, HierarchicalChoiceProbabilities)
    assert 0.0 < res.prob_active < 1.0
    assert 0.0 < res.prob_lurker < 1.0
    assert abs(res.prob_active + res.prob_lurker - 1.0) < 1e-4

    assert 0.0 < res.prob_consume_given_active < 1.0
    assert 0.0 < res.prob_produce_given_active < 1.0
    assert abs(res.prob_consume_given_active + res.prob_produce_given_active - 1.0) < 1e-4

    # All actions present in unconditional probabilities
    all_actions = ["like", "retweet", "browse", "reply", "quote", "post", "lurker_dwell"]
    for act in all_actions:
        assert act in res.unconditional_actions
        assert res.unconditional_actions[act] >= 0.0

    # Total unconditional probability must sum exactly to 1.0
    total_prob = sum(res.unconditional_actions.values())
    assert abs(total_prob - 1.0) < 1e-3


# 3. Test IIA Relaxation Across Nests (GEV Property vs MNL)
def test_iia_relaxation_across_nests():
    engine = DecisionEngine(nest_mu_active=0.8, nest_mu_consume=0.7, nest_mu_produce=0.75)

    u_consume_1 = {"like": 0.8, "retweet": 0.5}
    u_produce_1 = {"reply": 0.7, "quote": 0.4}

    res1 = engine.evaluate_hierarchical_nested_logit(0.5, 0.5, u_consume_1, u_produce_1)
    ratio_within_1 = res1.unconditional_actions["like"] / res1.unconditional_actions["retweet"]
    ratio_across_1 = res1.unconditional_actions["like"] / res1.unconditional_actions["reply"]

    # Add a new alternative 'bookmark' ONLY into the consume nest
    u_consume_2 = {"like": 0.8, "retweet": 0.5, "bookmark": 0.9}
    res2 = engine.evaluate_hierarchical_nested_logit(0.5, 0.5, u_consume_2, u_produce_1)
    ratio_within_2 = res2.unconditional_actions["like"] / res2.unconditional_actions["retweet"]
    ratio_across_2 = res2.unconditional_actions["like"] / res2.unconditional_actions["reply"]

    # 1) IIA holds WITHIN the same nest: relative odds of like to retweet remain invariant
    assert abs(ratio_within_1 - ratio_within_2) < 1e-4

    # 2) IIA is RELAXED ACROSS nests: relative odds of like to reply changes because consume nest expanded
    assert abs(ratio_across_1 - ratio_across_2) > 0.01


# 4. Test Logsum Inclusive Value Monotonicity
def test_logsum_inclusive_values_monotonicity():
    engine = DecisionEngine()
    u1 = {"like": 0.5, "retweet": 0.5}
    iv1, _, _ = engine._calculate_inclusive_value(u1, mu=0.7)

    # Increasing utility of one option must increase Inclusive Value
    u2 = {"like": 0.9, "retweet": 0.5}
    iv2, _, _ = engine._calculate_inclusive_value(u2, mu=0.7)
    assert iv2 > iv1

    # Adding an option must increase Inclusive Value
    u3 = {"like": 0.5, "retweet": 0.5, "browse": 0.5}
    iv3, _, _ = engine._calculate_inclusive_value(u3, mu=0.7)
    assert iv3 > iv1


# 5. Test Ratcliff DDM Analytical vs Simulation
def test_ratcliff_ddm_analytical_vs_simulation():
    engine = DecisionEngine(random_seed=123)

    drift = 0.4
    threshold_a = 0.8
    s = 0.1
    t_er = 300.0

    p_up, mean_rt, var_rt = engine.analytical_ddm(
        drift_rate=drift,
        threshold_a=threshold_a,
        s=s,
        non_decision_time_ms=t_er
    )

    # Strong positive drift: P(upper) approaches 1.0
    assert p_up > 0.95
    # Theoretical mean RT around t_er + (a/v)*1000 = 300 + 2000 = 2300 ms
    assert 2000.0 <= mean_rt <= 2500.0
    assert var_rt > 0.0

    # Monte Carlo simulation check
    sim_results = [
        engine.simulate_ddm(drift_rate=drift, threshold_a=threshold_a, non_decision_time_ms=t_er)
        for _ in range(50)
    ]
    avg_sim_dwell = sum(r.dwell_time_ms for r in sim_results) / len(sim_results)
    # Simulation mean dwell should be within 20% of analytical mean
    assert abs(avg_sim_dwell - mean_rt) / mean_rt < 0.20


# 6. Test DDM Psychological State Modulation
def test_ddm_psychological_modulation():
    engine = DecisionEngine()

    # High exploration / high confidence: high drift rate -> faster decision
    p_fast, rt_fast, _ = engine.analytical_ddm(drift_rate=0.08, threshold_a=0.2, s=0.1)
    # Low exploration / fearful hesitation: low drift rate -> slower deliberation
    p_slow, rt_slow, _ = engine.analytical_ddm(drift_rate=0.01, threshold_a=0.2, s=0.1)

    assert rt_fast < rt_slow
    assert p_fast > p_slow


# 7. Test Kahneman-Tversky Prospect Theory & Weighting Function
def test_prospect_theory_loss_aversion():
    engine = DecisionEngine(loss_aversion_lambda=2.25)

    # 1) Equal nominal gain and loss: value function is asymmetric due to loss aversion
    val_gain_only = engine.calculate_prospect_value(gain=1.0, loss=0.0)
    val_loss_only = engine.calculate_prospect_value(gain=0.0, loss=1.0)
    assert val_gain_only > 0.0
    assert val_loss_only < 0.0
    # Loss of 1.0 is felt approximately 2.25x worse than gain of 1.0
    assert abs(abs(val_loss_only) / val_gain_only - 2.25) < 0.10

    # 2) Probability weighting: overweighting small probabilities
    w_small = engine.probability_weighting(0.05, gamma=0.69)
    assert w_small > 0.05  # 5% backlash risk is amplified to > 10%

    # Underweighting large probabilities
    w_large = engine.probability_weighting(0.85, gamma=0.69)
    assert w_large < 0.85


# 8. Test Self-Censorship Mechanism (Sensor-Diri)
def test_self_censorship_mechanism():
    engine = DecisionEngine(loss_aversion_lambda=2.25)

    # Non-controversial context: no censorship
    ctx_safe = DecisionContext(
        is_controversial=False,
        controversy_level=0.0,
        audience_hostility=0.0,
        risk_tolerance=0.5
    )
    res_safe = engine.evaluate_self_censorship("post", ctx_safe)
    assert not res_safe.is_censored
    assert res_safe.executed_action == "post"

    # High controversy context with neurotic, low-risk-tolerance agent
    ctx_hot = DecisionContext(
        is_controversial=True,
        controversy_level=0.90,
        audience_hostility=0.80,
        topic_polarization=0.75,
        risk_tolerance=0.15,  # Very risk averse
        potential_loss=2.5,
        loss_aversion_lambda=3.0
    )
    res_hot = engine.evaluate_self_censorship("reply", ctx_hot)
    assert res_hot.is_censored
    assert res_hot.executed_action == "lurker_dwell"
    assert res_hot.censorship_probability > 0.50

    # High risk tolerance agent under same controversy: resists censorship
    ctx_brave = DecisionContext(
        is_controversial=True,
        controversy_level=0.90,
        audience_hostility=0.80,
        topic_polarization=0.75,
        risk_tolerance=0.95,  # High risk tolerance
        potential_loss=1.0,
        loss_aversion_lambda=1.5
    )
    res_brave = engine.evaluate_self_censorship("reply", ctx_brave)
    assert not res_brave.is_censored
    assert res_brave.executed_action == "reply"


# 9. Test End-to-End Integration with Agent 08 & Agent 09
def test_agent_08_09_end_to_end_orchestration():
    psy_engine = PsychometricsEngine(random_seed=42)
    needs_engine = HumanoidNeedsEngine(random_seed=42)
    decision_engine = DecisionEngine(random_seed=42)

    trait = BigFiveTrait(neuroticism=0.75, extraversion=0.25, conscientiousness=0.80)
    p_state = psy_engine.sample_state(trait)
    rec = psy_engine.get_downstream_recommendation(p_state, agent_id="agent-test-1")
    n_state = HumanoidNeedsState(energy=0.7, social_drive=0.4, achievement=0.5)

    ctx = DecisionContext(
        is_controversial=True,
        controversy_level=0.5,
        audience_hostility=0.4
    )

    outcome = decision_engine.decide_agent_action(
        context=ctx,
        agent_id="agent-test-1",
        needs_state=n_state,
        psy_rec=rec,
        hour=14
    )

    assert isinstance(outcome, DecisionOutcome)
    assert outcome.agent_id == "agent-test-1"
    assert outcome.action in ["like", "retweet", "browse", "reply", "quote", "post", "lurker_dwell"]
    assert outcome.dwell_time_ms > 0.0
    assert outcome.chosen_probability > 0.0
    assert len(outcome.all_probabilities) == 7


# 10. Test Swarm Simulation: Pareto 90:10 Lurker Ratio & Controversy Shock
def test_swarm_simulation_pareto_and_shock():
    decision_engine = DecisionEngine(random_seed=42)

    # Run 50 agents across 15 rounds with controversy shock at round 6
    sim_res = decision_engine.run_swarm_decision_simulation(
        agents_count=50,
        rounds=15,
        controversy_shock_round=6,
        shock_controversy_level=0.85,
        base_controversy_level=0.15,
        random_seed=42
    )

    assert isinstance(sim_res, SwarmDecisionResult)
    assert sim_res.total_agents == 50
    assert sim_res.total_rounds == 15

    # Validate Pareto lurker ratio ~90:10 rule (expecting 0.82 to 0.96)
    assert 0.80 <= sim_res.pareto_lurker_ratio <= 0.98
    # Validate 90-9-1 consumption vs production rule
    assert sim_res.consumption_ratio > sim_res.production_ratio
    assert sim_res.production_ratio <= 0.10

    # Dwell time metrics
    assert sim_res.mean_dwell_time_ms > 500.0
    assert sim_res.std_dwell_time_ms > 0.0


# 11. Test Anomaly Detection & RecSys Downstream Handoff
def test_anomaly_detection_and_recsys_handoff():
    decision_engine = DecisionEngine(random_seed=42)

    sim_res = decision_engine.run_swarm_decision_simulation(
        agents_count=60,
        rounds=16,
        controversy_shock_round=6,
        shock_controversy_level=0.90,
        base_controversy_level=0.10,
        random_seed=42
    )

    # Under 0.90 shock controversy, Chilling Effect Spiral should be flagged
    anomaly_types = [a.anomaly_type for a in sim_res.anomalies]
    assert "CHILLING_EFFECT_SPIRAL" in anomaly_types

    # Verify downstream parameters generated for Agent 11 RecSys Funnel
    recsys_params = decision_engine.get_recsys_downstream_recommendation(sim_res)
    assert "recommended_damping_factor" in recsys_params
    assert "recommended_candidate_limit" in recsys_params
    assert "recommended_epsilon" in recsys_params
    assert 0.40 <= recsys_params["recommended_damping_factor"] <= 0.85
    assert 30 <= recsys_params["recommended_candidate_limit"] <= 100
    assert 0.01 <= recsys_params["recommended_epsilon"] <= 0.20
