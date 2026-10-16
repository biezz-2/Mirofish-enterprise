"""
Unit tests for MiroFish Enterprise Psychometrics Service (Agent 08 - Divisi C)
Verifies:
1. Fleeson Whole Trait Theory density distribution (s = trait + noise)
2. Trait boundedness [0.0, 1.0] under extreme perturbation
3. DeYoung Cybernetic Big Five 10 aspects & functional drive mappings
4. Situational press modulation (threat, novelty, social, reward, structure)
5. Temporal state inertia (AR-1 autoregressive dynamic)
6. Intra-individual long-term convergence & identity retention
7. Multi-agent swarm population simulation
8. Cybernetic deadlock / freezing detection under extreme threat shock
9. Homeostasis recovery tracking
10. Calibrated downstream recommendations for Agent 09 (ODE) & Agent 10 (Decision)
"""

import pytest
from app.services.psychometrics import (
    BigFiveTrait,
    SituationalPress,
    CyberneticAspects,
    PersonalityState,
    PsychometricsEngine,
    AnomalyReport,
    TrajectoryResult,
    SwarmSimulationResult,
    DownstreamRecommendation,
)


def test_big_five_trait_initialization():
    """Verify default and custom BigFiveTrait fields and constraints."""
    default_trait = BigFiveTrait()
    assert default_trait.openness == 0.5
    assert default_trait.conscientiousness == 0.5
    assert default_trait.extraversion == 0.5
    assert default_trait.agreeableness == 0.5
    assert default_trait.neuroticism == 0.5

    custom_trait = BigFiveTrait(
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.75,
        neuroticism=0.25
    )
    assert custom_trait.openness == 0.8
    assert custom_trait.neuroticism == 0.25

    with pytest.raises(Exception):
        BigFiveTrait(openness=1.5)

    with pytest.raises(Exception):
        BigFiveTrait(neuroticism=-0.2)


def test_sample_state_fleeson_distribution():
    """Verify Fleeson Whole Trait sampling produces states within valid bounds."""
    engine = PsychometricsEngine(sigma_noise=0.08, random_seed=42)
    trait = BigFiveTrait(openness=0.7, conscientiousness=0.6, extraversion=0.5, agreeableness=0.8, neuroticism=0.3)

    state = engine.sample_state(trait)
    assert isinstance(state, PersonalityState)
    assert 0.0 <= state.state_openness <= 1.0
    assert 0.0 <= state.state_conscientiousness <= 1.0
    assert 0.0 <= state.state_extraversion <= 1.0
    assert 0.0 <= state.state_agreeableness <= 1.0
    assert 0.0 <= state.state_neuroticism <= 1.0

    # Check cybernetic drives
    assert state.exploration_drive > 0.0
    assert state.goal_persistence > 0.0
    assert state.reward_sensitivity > 0.0
    assert state.social_trust > 0.0
    assert state.threat_sensitivity > 0.0

    # Metatraits
    assert 0.0 <= state.stability <= 1.0
    assert 0.0 <= state.plasticity <= 1.0


def test_deyoung_cybernetic_aspects_calculation():
    """Verify 10 DeYoung aspects are properly derived from momentary states."""
    engine = PsychometricsEngine(sigma_noise=0.05, random_seed=42)
    trait = BigFiveTrait(openness=0.8, conscientiousness=0.7, extraversion=0.6, agreeableness=0.85, neuroticism=0.2)
    state = engine.sample_state(trait)

    assert state.aspects is not None
    aspects = state.aspects
    assert isinstance(aspects, CyberneticAspects)

    # Verify Openness aspects
    assert 0.0 <= aspects.intellect <= 1.0
    assert 0.0 <= aspects.openness_to_experience <= 1.0
    # Intellect should reflect high openness and conscientiousness
    assert aspects.intellect >= 0.70

    # Verify Conscientiousness aspects
    assert 0.0 <= aspects.industriousness <= 1.0
    assert 0.0 <= aspects.orderliness <= 1.0

    # Verify Extraversion aspects
    assert 0.0 <= aspects.assertiveness <= 1.0
    assert 0.0 <= aspects.enthusiasm <= 1.0

    # Verify Agreeableness aspects
    assert 0.0 <= aspects.compassion <= 1.0
    assert 0.0 <= aspects.politeness <= 1.0

    # Verify Neuroticism aspects
    assert 0.0 <= aspects.volatility <= 1.0
    assert 0.0 <= aspects.withdrawal <= 1.0
    # For low neuroticism (0.2), volatility and withdrawal should be relatively low
    assert aspects.volatility < 0.45
    assert aspects.withdrawal < 0.45


def test_situational_press_modulation():
    """Verify external situational press appropriately shifts personality states."""
    engine = PsychometricsEngine(sigma_noise=0.02, random_seed=42)
    baseline = BigFiveTrait(openness=0.5, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5, neuroticism=0.5)

    # 1. High Threat Press (hostility, crisis, severe controversy)
    threat_press = SituationalPress(threat=0.9, novelty=0.1, social=0.1, reward=0.0, structure=0.2)
    threat_state = engine.sample_state(baseline, press=threat_press)

    # Neuroticism and threat sensitivity must rise
    assert threat_state.state_neuroticism > baseline.neuroticism
    assert threat_state.threat_sensitivity > 0.70
    # Agreeableness and trust should decrease under threat
    assert threat_state.state_agreeableness < baseline.agreeableness

    # 2. High Novelty & Cognitive Stimulation Press
    novelty_press = SituationalPress(threat=0.0, novelty=0.9, social=0.3, reward=0.5, structure=0.1)
    novelty_state = engine.sample_state(baseline, press=novelty_press)
    assert novelty_state.state_openness > baseline.openness
    assert novelty_state.exploration_drive > 0.60

    # 3. High Social & Reward Press
    social_press = SituationalPress(threat=0.0, novelty=0.2, social=0.9, reward=0.8, structure=0.3)
    social_state = engine.sample_state(baseline, press=social_press)
    assert social_state.state_extraversion > baseline.extraversion
    assert social_state.reward_sensitivity > 0.65


def test_state_inertia_autoregressive():
    """Verify temporal AR(1) state inertia dampens erratic jumps between rounds."""
    engine = PsychometricsEngine(sigma_noise=0.05, state_inertia=0.70, random_seed=42)
    trait = BigFiveTrait(openness=0.5, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5, neuroticism=0.5)

    # Previous state was calm (low neuroticism 0.2)
    prev_state = PersonalityState(
        state_openness=0.5,
        state_conscientiousness=0.5,
        state_extraversion=0.5,
        state_agreeableness=0.5,
        state_neuroticism=0.2,
        exploration_drive=0.6,
        goal_persistence=0.55,
        reward_sensitivity=0.65,
        social_trust=0.5,
        threat_sensitivity=0.28
    )

    # Sudden high threat shock in next round
    shock = SituationalPress(threat=1.0)
    new_state = engine.sample_state(trait, press=shock, previous_state=prev_state)

    # With high inertia (0.7), new_state should not jump immediately to max, demonstrating damping
    target_unconstrained = 0.5 + 0.25  # ~0.75
    assert new_state.state_neuroticism < target_unconstrained
    assert new_state.state_neuroticism > prev_state.state_neuroticism


def test_density_distribution_stability():
    """Verify sample_distribution maintains expected mean and stability flag."""
    engine = PsychometricsEngine(sigma_noise=0.06, random_seed=42)
    trait = BigFiveTrait(openness=0.75, conscientiousness=0.65, extraversion=0.55, agreeableness=0.70, neuroticism=0.30)

    dist = engine.sample_distribution(trait, n_samples=600)
    assert dist["is_stable"] is True
    assert dist["deviation"] < 0.05
    assert dist["std_dev"] > 0.0
    assert "all_traits" in dist
    assert dist["all_traits_stable"] is True


def test_trajectory_core_identity_retention():
    """
    Verify Fleeson's core finding: across 50 rounds, momentary states fluctuate
    but the within-person mean converges to the core trait baseline (identity preserved).
    """
    engine = PsychometricsEngine(sigma_noise=0.07, state_inertia=0.30, random_seed=42)
    trait = BigFiveTrait(openness=0.80, conscientiousness=0.70, extraversion=0.60, agreeableness=0.75, neuroticism=0.35)

    traj = engine.simulate_trajectory(trait, n_rounds=60)
    assert isinstance(traj, TrajectoryResult)
    assert traj.rounds == 60
    assert len(traj.states) == 60
    assert traj.identity_preserved is True
    assert traj.stability_score >= 0.90

    # Ensure variance is non-zero (dynamic, non-static)
    assert traj.variance_states["openness"] > 0.0005
    assert traj.variance_states["extraversion"] > 0.0005

    # Check long-term mean convergence
    assert abs(traj.mean_states["openness"] - trait.openness) < 0.05
    assert abs(traj.mean_states["conscientiousness"] - trait.conscientiousness) < 0.05


def test_swarm_population_simulation():
    """Verify multi-agent swarm simulation produces collective metrics and archetypes."""
    engine = PsychometricsEngine(sigma_noise=0.06, random_seed=42)
    population = engine.generate_archetype_population(n_agents=30)
    assert len(population) == 30

    res = engine.simulate_swarm_population(population, n_rounds=15)
    assert isinstance(res, SwarmSimulationResult)
    assert res.population_size == 30
    assert res.rounds == 15
    assert res.identity_retention_rate >= 0.90
    assert res.convergence_rate >= 0.85
    assert res.deadlock_detected is False
    assert res.collective_entropy > 0.0
    assert len(res.agent_summaries) > 0


def test_deadlock_detection_cybernetic_freezing():
    """Verify detection of cybernetic freezing when swarm faces overwhelming persistent threat."""
    engine = PsychometricsEngine(sigma_noise=0.05, random_seed=42)
    # High neuroticism agents
    stressed_pop = [BigFiveTrait(neuroticism=0.90, extraversion=0.10, agreeableness=0.20) for _ in range(10)]
    
    # Overwhelming threat press across all rounds
    extreme_press = [SituationalPress(threat=1.0) for _ in range(5)]
    res = engine.simulate_swarm_population(stressed_pop, n_rounds=5, press_sequence=extreme_press)

    assert res.deadlock_detected is True
    assert len(res.deadlock_details) > 0
    assert "Cybernetic Freezing" in res.deadlock_details[0]


def test_homeostasis_recovery_after_shock():
    """Verify swarm recovers toward baseline homeostasis after an acute one-round shock."""
    engine = PsychometricsEngine(sigma_noise=0.05, state_inertia=0.25, random_seed=42)
    pop = engine.generate_archetype_population(n_agents=20)

    # Acute shock at round 5
    res = engine.simulate_swarm_population(
        pop,
        n_rounds=15,
        shock_round=5,
        shock_press=SituationalPress(threat=1.0)
    )

    # Swarm should recover in subsequent rounds
    assert res.homeostasis_recovery_rounds > 0
    assert res.homeostasis_recovery_rounds <= 5


def test_downstream_recommendation():
    """Verify calibrated parameter generation for Agent 09 (ODE) & Agent 10 (Decision)."""
    engine = PsychometricsEngine(random_seed=42)
    trait = BigFiveTrait(openness=0.85, conscientiousness=0.75, extraversion=0.70, agreeableness=0.80, neuroticism=0.25)
    state = engine.sample_state(trait)

    rec = engine.get_downstream_recommendation(state, agent_id="agent-oasis-007")
    assert isinstance(rec, DownstreamRecommendation)
    assert rec.agent_id == "agent-oasis-007"

    # Agent 09 parameters
    a09 = rec.agent_09_needs
    assert "effective_lambda_energy" in a09
    assert "effective_lambda_social" in a09
    assert "baseline_ekman_emotions" in a09
    assert "circadian_sleep_resilience" in a09

    emotions = a09["baseline_ekman_emotions"]
    assert len(emotions) == 7
    assert emotions["joy"] > 0.40
    assert emotions["fear"] < 0.40

    # Agent 10 parameters
    a10 = rec.agent_10_decision
    assert "adjusted_utility_lurker" in a10
    assert "ddm_drift_rate" in a10
    assert "prospect_lambda_loss" in a10
    assert "risk_tolerance" in a10
    assert a10["risk_tolerance"] > 0.60
