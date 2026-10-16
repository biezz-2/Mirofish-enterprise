"""
Test Suite for Agent 09: Humanoid ODE Basic Needs & Ekman Engine (Divisi SIM)
Validates:
1. Ekman 7 basic emotions and Russell Circumplex (PAD) mapping
2. System 1 Needs ODE analytical solutions, RK2 midpoint, and replenishment
3. Somatic coupling and emotional homeostatic decay
4. Bimodal 24-hour circadian clock and chronotype variation
5. Downstream parameter handoffs for Agent 10 (Nested Logit & DDM)
6. Swarm predictive sandbox simulation, acute shock response, and anomaly detection
7. Pydantic v2 legacy alias remapping and integration with Agent 08 recommendations
"""

import math
import pytest
from app.services.humanoid_needs import (
    EkmanEmotions,
    HumanoidNeedsState,
    AppraisalEvent,
    HumanoidAnomalyReport,
    SwarmHumanoidSimulationResult,
    HumanoidNeedsEngine,
)
from app.services.psychometrics import (
    PsychometricsEngine,
    PersonalityState,
    BigFiveTrait,
)


def test_ekman_emotions_initialization_and_pad_mapping():
    """Memverifikasi inisialisasi default emosi Ekman dan pemetaan Circumplex Russell (PAD)."""
    emotions = EkmanEmotions(
        joy=0.8,
        sadness=0.1,
        anger=0.05,
        fear=0.05,
        disgust=0.02,
        surprise=0.3,
        trust=0.75
    )

    pad = emotions.valence_arousal()
    assert "valence" in pad
    assert "arousal" in pad
    assert "dominance" in pad

    # Dominan positif (joy & trust tinggi) -> Valensi harus positif
    assert pad["valence"] > 0.3
    # Arousal dan Dominansi berada dalam batas valid
    assert 0.0 <= pad["arousal"] <= 1.0
    assert -1.0 <= pad["dominance"] <= 1.0

    # Uji primary_emotion
    top_name, top_val = emotions.primary_emotion()
    assert top_name == "joy"
    assert top_val == 0.8


def test_humanoid_needs_state_alias_remapping():
    """Memverifikasi Pydantic v2 model_validator remapping alias legacy (social -> social_drive, entertainment -> stimulation)."""
    legacy_payload = {
        "energy": 0.9,
        "social": 0.65,
        "entertainment": 0.75,
        "social_closeness": 12.0
    }
    state = HumanoidNeedsState.model_validate(legacy_payload)
    assert state.energy == 0.9
    assert state.social_drive == 0.65
    assert state.stimulation == 0.75
    assert state.achievement == 0.5  # default
    assert state.social_closeness == 12.0


def test_needs_ode_analytical_decay():
    """Memverifikasi solusi analitik peluruhan eksponensial ODE dN/dt = -lambda * N."""
    engine = HumanoidNeedsEngine(lambda_energy=0.10, lambda_social=0.05)
    s0 = HumanoidNeedsState(energy=1.0, social_drive=1.0, stimulation=1.0)

    # 1 jam peluruhan tanpa replenishment
    s1 = engine.step_ode_decay(s0, dt_hours=1.0, current_hour=14)

    expected_energy = round(1.0 * math.exp(-0.10 * 1.0), 4)
    expected_social = round(1.0 * math.exp(-0.05 * 1.0), 4)

    assert abs(s1.energy - expected_energy) < 1e-4
    assert abs(s1.social_drive - expected_social) < 1e-4
    assert s1.energy < s0.energy
    assert s1.social_drive < s0.social_drive


def test_needs_ode_rk2_vs_analytical():
    """Membandingkan solusi analitik dengan solusi numerik Runge-Kutta Orde-2 (Midpoint)."""
    engine = HumanoidNeedsEngine(lambda_energy=0.08, lambda_social=0.04)
    s0 = HumanoidNeedsState(energy=0.9, social_drive=0.85, stimulation=0.8)

    dt = 0.5
    s_analytical = engine.step_ode_decay(s0, dt_hours=dt, current_hour=14)
    s_rk2 = engine.step_ode_rk2(s0, dt_hours=dt)

    # Kedua metode harus konvergen sangat dekat (selisih < 0.005)
    assert abs(s_analytical.energy - s_rk2.energy) < 0.005
    assert abs(s_analytical.social_drive - s_rk2.social_drive) < 0.005
    assert abs(s_analytical.stimulation - s_rk2.stimulation) < 0.005


def test_needs_replenishment_and_clipping():
    """Memverifikasi pemulihan (replenishment) kebutuhan dan batas atas [0.01, 1.0]."""
    engine = HumanoidNeedsEngine(lambda_energy=0.05, lambda_social=0.03)
    s0 = HumanoidNeedsState(energy=0.4, social_drive=0.3)

    replenishment = {
        "energy": 0.5,
        "social_drive": 0.6,
        "achievement": 0.3,
        "social_closeness": 5.0
    }

    s1 = engine.step_ode_decay(s0, dt_hours=1.0, replenishment=replenishment, current_hour=14)

    assert s1.energy > s0.energy
    assert s1.social_drive > s0.social_drive
    assert s1.achievement > s0.achievement
    assert s1.social_closeness > s0.social_closeness
    assert 19.8 <= s1.social_closeness <= 20.0

    # Uji clipping batas atas jika replenishment sangat besar
    s_huge = engine.step_ode_decay(s0, dt_hours=1.0, replenishment={"energy": 5.0}, current_hour=14)
    assert s_huge.energy == 1.0


def test_cognitive_appraisal_events():
    """Memverifikasi pengaruh evaluasi kognitif peristiwa terhadap pergeseran emosi Ekman."""
    engine = HumanoidNeedsEngine()
    s0 = HumanoidNeedsState(
        emotions=EkmanEmotions(joy=0.5, sadness=0.1, anger=0.1, fear=0.1, trust=0.6)
    )

    # 1. Threat Shock
    threat_event = AppraisalEvent(event_type="threat_shock", intensity=0.8)
    s_threat = engine.appraise_event(s0, threat_event)
    assert s_threat.emotions.fear > s0.emotions.fear
    assert s_threat.emotions.anger > s0.emotions.anger
    assert s_threat.emotions.trust < s0.emotions.trust
    assert s_threat.emotions.joy < s0.emotions.joy

    # 2. Social Positive
    pos_event = AppraisalEvent(event_type="social_positive", intensity=0.7)
    s_pos = engine.appraise_event(s0, pos_event)
    assert s_pos.emotions.joy > s0.emotions.joy
    assert s_pos.emotions.trust > s0.emotions.trust

    # 3. Content Toxic
    toxic_event = AppraisalEvent(event_type="content_toxic", intensity=0.9)
    s_toxic = engine.appraise_event(s0, toxic_event)
    assert s_toxic.emotions.disgust > s0.emotions.disgust
    assert s_toxic.emotions.anger > s0.emotions.anger


def test_somatic_coupling_and_fatigue_distress():
    """Memverifikasi bahwa defisit energi kritis (< 0.20) memicu distres somatis pada emosi."""
    engine = HumanoidNeedsEngine(lambda_energy=0.50)
    # Energi sangat rendah
    s_exhausted = HumanoidNeedsState(
        energy=0.10,
        social_drive=0.80,
        emotions=EkmanEmotions(joy=0.5, anger=0.1, sadness=0.1)
    )

    s_decayed = engine.step_ode_decay(s_exhausted, dt_hours=1.0, current_hour=14)
    # Kelelahan akut harus meningkatkan anger/sadness dan menekan joy
    assert s_decayed.emotions.anger > s_exhausted.emotions.anger
    assert s_decayed.emotions.sadness > s_exhausted.emotions.sadness
    assert s_decayed.emotions.joy < s_exhausted.emotions.joy


def test_bimodal_circadian_clock_and_chronotype():
    """Memverifikasi kurva sirkadian 24-jam bimodal dan pergeseran kronotipe."""
    engine = HumanoidNeedsEngine()

    # Waktu tidur (03:00) vs Puncak siang (10:00) vs Puncak malam (20:00)
    c_sleep = engine.compute_circadian_factor(3, chronotype_offset=0.0)
    c_morning = engine.compute_circadian_factor(10, chronotype_offset=0.0)
    c_evening = engine.compute_circadian_factor(20, chronotype_offset=0.0)

    assert c_sleep <= 0.15
    assert c_morning >= 0.70
    assert c_evening >= 0.70
    assert c_morning > c_sleep
    assert c_evening > c_sleep

    # Uji kronotipe Night Owl (+3 jam)
    # Pukul 01:00 masih aktif bagi night owl dibandingkan normal
    c_owl = engine.compute_circadian_factor(1, chronotype_offset=2.5)
    c_norm = engine.compute_circadian_factor(1, chronotype_offset=0.0)
    assert c_owl > c_norm


def test_downstream_decision_utilities_handoff():
    """Memverifikasi payload kalibrasi utilitas untuk Agent 10 (Nested Logit & DDM)."""
    engine = HumanoidNeedsEngine()
    state = HumanoidNeedsState(
        energy=0.85,
        social_drive=0.90,
        stimulation=0.75,
        achievement=0.60,
        emotions=EkmanEmotions(joy=0.7, trust=0.8, fear=0.05, anger=0.05)
    )

    utils = engine.get_decision_utilities(state, hour=14)

    assert "utility_active" in utils
    assert "utility_lurker" in utils
    assert "action_utilities" in utils
    assert "ddm_drift_modifier" in utils
    assert "prospect_loss_modifier" in utils
    assert "action_probabilities" in utils

    # Agen bugar dan ramah -> utility_active harus jauh lebih tinggi daripada utility_lurker
    assert utils["utility_active"] > utils["utility_lurker"]

    # Probabilitas aksi diskrit harus berjumlah ~1.0
    act_probs = utils["action_probabilities"]
    assert abs(sum(act_probs.values()) - 1.0) < 0.01
    assert act_probs["post"] > 0.0
    assert act_probs["reply"] > 0.0


def test_factory_from_agent_08_psychometrics():
    """Memverifikasi integrasi dari DownstreamRecommendation Agent 08 ke Agent 09."""
    psy_engine = PsychometricsEngine(random_seed=42)
    trait = BigFiveTrait(openness=0.85, conscientiousness=0.75, extraversion=0.80, agreeableness=0.80, neuroticism=0.20)
    p_state = psy_engine.sample_state(trait)
    rec = psy_engine.get_downstream_recommendation(p_state, agent_id="agent-humanoid-01")

    engine, state = HumanoidNeedsEngine.from_psychometrics_recommendation(rec, chronotype_offset=1.0)

    assert isinstance(engine, HumanoidNeedsEngine)
    assert isinstance(state, HumanoidNeedsState)
    assert state.chronotype_offset == 1.0
    assert state.emotions.joy >= 0.50
    assert engine.lambda_energy > 0.0
    assert engine.lambda_social > 0.0


def test_swarm_predictive_sandbox_and_shock_recovery():
    """Memverifikasi simulasi sandbox prediktif swarm humanoid dengan injeksi shock dan deteksi pemulihan."""
    engine = HumanoidNeedsEngine(random_seed=42)
    pop = engine.generate_population(n_agents=30, chronotype_diversity=True)
    assert len(pop) == 30

    shock = AppraisalEvent(event_type="threat_shock", intensity=0.9, description="Viral Misinformation Crisis")

    res = engine.simulate_humanoid_swarm(
        population_states=pop,
        n_hours=36,
        shock_hour=12,
        shock_event=shock,
        ambient_interaction_rate=0.4
    )

    assert isinstance(res, SwarmHumanoidSimulationResult)
    assert res.total_agents == 30
    assert res.total_hours == 36
    assert len(res.collective_energy_trajectory) == 36
    assert len(res.collective_valence_trajectory) == 36
    assert len(res.collective_emotions_trajectory["fear"]) == 36

    # Pada jam 12 (saat shock), fear kolektif harus melonjak tajam
    fear_before = res.collective_emotions_trajectory["fear"][11]
    fear_shock = res.collective_emotions_trajectory["fear"][12]
    assert fear_shock > fear_before

    # Anomali report harus terisi
    assert isinstance(res.anomalies, HumanoidAnomalyReport)
    assert res.circadian_sync_index >= 0.0
