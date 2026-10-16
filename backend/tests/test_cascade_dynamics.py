"""
MiroFish Enterprise - Test Suite untuk Agent 13 (Divisi D: SIM)
Hawkes Process & Rescorla-Wagner Viral Cascade Modeler

Pengujian komprehensif:
1. Rescorla-Wagner Reward Prediction Error, dopamin, habituasi, dan burnout.
2. Marked Hawkes Self-Exciting Point Process, branching ratio eta, dan Ogata thinning.
3. Mark Granovetter (1978) Threshold Model, topologi jaringan, dan tipping point.
4. Swarm Predictive Sandbox Simulation (50 agen x 15 ronde x 8 platform = 6,000 aksi).
5. Downstream Parameter Handoff Matrix untuk Agent 14 (BSP Parallel Runner).
6. Enterprise REST API endpoints integrasi.
"""

import pytest
import math
from backend.app.services.cascade_dynamics import (
    CascadeDynamicsEngine,
    HawkesEvent,
    HawkesPlatformParams,
    RescorlaWagnerState,
    GranovetterAgentState,
    CascadeSimulationMetrics,
    SwarmCascadeSimulationResult,
    DEFAULT_PLATFORM_HAWKES_MATRIX,
    CANONICAL_7_PLATFORMS,
    EXTENDED_PLATFORMS,
)
from backend.app import create_app


@pytest.fixture
def engine():
    return CascadeDynamicsEngine()


@pytest.fixture
def app_client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# =============================================================================
# 1. Rescorla-Wagner Dopamine & Behavioral Reinforcement Tests
# =============================================================================

def test_rescorla_wagner_acquisition(engine):
    """Verifikasi peningkatan ekspektasi dopamin V saat reward positif diperoleh."""
    v_init = 0.20
    reward = 1.0
    v_new, err = engine.update_rescorla_wagner(current_v=v_init, received_reward=reward)
    assert v_new > v_init
    assert err == pytest.approx(0.80, abs=1e-4)
    assert v_new == pytest.approx(0.20 + 0.25 * 0.80, abs=1e-4)


def test_rescorla_wagner_extinction(engine):
    """Verifikasi peluruhan eksponensial V menuju 0 saat reward dihentikan (R=0)."""
    schedule_res = engine.simulate_dopamine_schedule(
        initial_v=0.80,
        reward_sequence=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        alpha=0.25
    )
    assert schedule_res["final_v"] < 0.15
    assert schedule_res["extinction_achieved"] is True
    assert all(rpe < 0 for rpe in schedule_res["rpe_trajectory"])


def test_rescorla_wagner_stateful_agent_and_burnout(engine):
    """Verifikasi pembaruan state agen dan pemicuan burnout akibat kekecewaan beruntun."""
    agent_state = RescorlaWagnerState(agent_id="test_001", v_dopamine=0.50, alpha_learning_rate=0.25)
    
    # 4 ronde berturut-turut reward 0 memicu burnout
    for _ in range(4):
        agent_state = engine.step_agent_dopamine(agent_state, received_reward=0.0)
    
    assert agent_state.consecutive_frustrations >= 4
    assert agent_state.is_burnout is True
    assert len(agent_state.rpe_history) == 4

    # Reward besar memulihkan status burnout
    agent_state = engine.step_agent_dopamine(agent_state, received_reward=3.0)
    assert agent_state.is_burnout is False
    assert agent_state.consecutive_frustrations == 0


def test_rescorla_wagner_post_frequency(engine):
    """Verifikasi bahwa frekuensi posting meningkat dengan dopamin dan turun saat burnout."""
    freq_creator_high_v = engine.compute_post_frequency(v_dopamine=1.0, is_burnout=False, role="creator")
    freq_creator_low_v = engine.compute_post_frequency(v_dopamine=0.1, is_burnout=False, role="creator")
    freq_creator_burnout = engine.compute_post_frequency(v_dopamine=1.0, is_burnout=True, role="creator")
    freq_lurker = engine.compute_post_frequency(v_dopamine=0.5, is_burnout=False, role="lurker")

    assert freq_creator_high_v > freq_creator_low_v
    assert freq_creator_burnout < freq_creator_high_v
    assert freq_creator_high_v > freq_lurker


# =============================================================================
# 2. Marked Hawkes Self-Exciting Point Process Tests
# =============================================================================

def test_hawkes_intensity_baseline_and_decay(engine):
    """Verifikasi bahwa intensitas Hawkes meluruh kembali ke baseline mu seiring berjalannya waktu."""
    events = [HawkesEvent(timestamp=1.0, user_influence_mark=1.5)]
    
    # Sesaat setelah event: intensitas tinggi
    int_near = engine.calculate_hawkes_intensity(current_time=1.1, history_events=events)
    # Waktu lama setelah event: intensitas mendekati mu (0.1)
    int_far = engine.calculate_hawkes_intensity(current_time=25.0, history_events=events)

    assert int_near > int_far
    assert int_far == pytest.approx(0.1, abs=0.01)


def test_hawkes_influence_mark_weighting(engine):
    """Verifikasi mark pengaruh pengguna yang lebih tinggi memicu lonjakan intensitas lebih besar."""
    ev_influential = [HawkesEvent(timestamp=1.0, user_influence_mark=3.5)]
    ev_ordinary = [HawkesEvent(timestamp=1.0, user_influence_mark=0.5)]

    int_influential = engine.calculate_hawkes_intensity(current_time=1.2, history_events=ev_influential)
    int_ordinary = engine.calculate_hawkes_intensity(current_time=1.2, history_events=ev_ordinary)

    assert int_influential > int_ordinary


def test_hawkes_platform_matrices_and_criticality(engine):
    """Verifikasi kalkulasi parameter Hawkes dan regim kritisitas pada seluruh 8 platform."""
    for p_key in EXTENDED_PLATFORMS:
        params = engine.get_platform_hawkes_params(p_key)
        assert params.branching_ratio > 0
        assert params.halflife_time > 0
        assert params.time_to_extinction_95 > params.halflife_time
        
        # Cek konsistensi matematis regim kritisitas
        if params.branching_ratio < 0.999:
            assert params.criticality_regime == "subcritical"
        elif params.branching_ratio > 1.001:
            assert params.criticality_regime == "supercritical"
        else:
            assert params.criticality_regime == "critical"

    # Verifikasi kasus spesifik platform
    x_params = engine.get_platform_hawkes_params("x")
    assert x_params.branching_ratio == pytest.approx(0.75 / 0.85, abs=1e-4)
    assert x_params.criticality_regime == "subcritical"

    reddit_params = engine.get_platform_hawkes_params("reddit")
    assert reddit_params.branching_ratio == pytest.approx(0.60 / 0.50, abs=1e-4)
    assert reddit_params.criticality_regime == "supercritical"


def test_hawkes_continuous_simulation_ogata(engine):
    """Verifikasi simulasi proses titik kontinu Ogata thinning."""
    sim_res = engine.simulate_hawkes_cascade(
        platform="x",
        time_horizon=12.0,
        max_events=100,
        random_seed=42
    )
    assert sim_res["total_events_generated"] >= 1
    assert sim_res["peak_intensity"] >= 0.12
    assert "events_sample" in sim_res
    assert sim_res["platform"] == "x"


# =============================================================================
# 3. Mark Granovetter (1978) Threshold Model Tests
# =============================================================================

def test_granovetter_basic_activation(engine):
    """Verifikasi kompatibilitas dasar aturan ambang batas Granovetter."""
    assert engine.evaluate_granovetter_activation(individual_threshold=0.30, active_peer_ratio=0.35) is True
    assert engine.evaluate_granovetter_activation(individual_threshold=0.30, active_peer_ratio=0.25) is False
    assert engine.evaluate_granovetter_activation(individual_threshold=0.30, active_peer_ratio=0.30) is True


def test_granovetter_dynamic_effective_threshold(engine):
    """Verifikasi bahwa dopamin tinggi dan intensitas viral menurunkan resistensi ambang batas."""
    base_thresh = 0.40
    eff_neutral = engine.calculate_effective_threshold(base_threshold=base_thresh, v_dopamine=0.0, hawkes_intensity=0.0)
    eff_hyped = engine.calculate_effective_threshold(base_threshold=base_thresh, v_dopamine=0.8, hawkes_intensity=2.5)

    assert eff_neutral == base_thresh
    assert eff_hyped < eff_neutral
    assert eff_hyped >= 0.01


def test_granovetter_cascade_simulation_small_world(engine):
    """Verifikasi propagasi kaskade adopsi pada topologi Small-World."""
    cascade_res = engine.simulate_granovetter_cascade(
        num_agents=50,
        platform="x",
        seed_ratio=0.06,
        network_type="small_world",
        max_rounds=10,
        random_seed=42
    )
    assert cascade_res["num_agents"] == 50
    assert cascade_res["initial_seeds"] >= 2
    assert cascade_res["final_adoption_rate"] >= 0.06
    assert len(cascade_res["adoption_timeline"]) >= 2
    assert cascade_res["rounds_to_converge"] >= 1


# =============================================================================
# 4. Swarm Predictive Sandbox Simulation Tests (50 Agents x 15 Rounds x 8 Platforms)
# =============================================================================

def test_swarm_cascade_sandbox_full_run(engine):
    """
    Eksekusi simulasi swarm sandbox komprehensif 50 agen x 15 ronde pada seluruh 8 platform
    (6,000 aksi evaluasi). Memvalidasi konvergensi, kestabilan, dan zero deadlock.
    """
    result = engine.run_swarm_cascade_simulation(
        agents_count=50,
        rounds=15,
        platforms=EXTENDED_PLATFORMS,
        random_seed=42
    )

    assert isinstance(result, SwarmCascadeSimulationResult)
    assert result.agents_count_per_platform == 50
    assert result.rounds_count_per_platform == 15
    assert result.total_platforms_simulated == 8
    assert result.total_actions_evaluated == 6000  # 50 * 15 * 8
    assert result.deadlock_detected is False
    assert result.global_cascade_stability is True

    # Periksa kelengkapan setiap platform
    for p_key in EXTENDED_PLATFORMS:
        assert p_key in result.platform_results
        metrics = result.platform_results[p_key]
        assert isinstance(metrics, CascadeSimulationMetrics)
        assert metrics.final_adoption_rate > 0.0
        assert metrics.peak_intensity > 0.0
        assert metrics.deadlock_detected is False
        assert metrics.branching_ratio_eta > 0.0

    # Periksa handoff parameters untuk Agent 14
    downstream = result.downstream_parameters_agent_14
    assert downstream["bsp_superstep_barrier_interval"] == 1
    assert downstream["sqlite_wal_checkpoint_frequency_rounds"] == 5
    assert downstream["state_hash_algorithm"] == "SHA-256"
    assert downstream["cascade_stability_certified"] is True
    assert "platform_sync_intervals_ms" in downstream
    assert downstream["platform_sync_intervals_ms"]["tiktok"] == 100
    assert downstream["platform_sync_intervals_ms"]["youtube"] == 300


# =============================================================================
# 5. Enterprise REST API Endpoints Tests
# =============================================================================

def test_api_cascade_hawkes_endpoint(app_client):
    """Verifikasi endpoint POST /api/enterprise/cascade/hawkes (backward compatible)."""
    payload = {
        "current_time": 5.0,
        "events": [
            {"t": 1.0, "mark": 1.5},
            {"t": 3.0, "mark": 2.0}
        ]
    }
    resp = app_client.post('/api/enterprise/cascade/hawkes', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["intensity"] > 0.1


def test_api_cascade_rescorla_wagner_endpoint(app_client):
    """Verifikasi endpoint POST /api/enterprise/cascade/rescorla-wagner."""
    # Single update
    resp = app_client.post('/api/enterprise/cascade/rescorla-wagner', json={
        "current_v": 0.40,
        "received_reward": 1.20,
        "alpha": 0.25
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["new_v"] == pytest.approx(0.60, abs=1e-3)
    assert data["prediction_error"] == pytest.approx(0.80, abs=1e-3)

    # Schedule simulation
    resp_sched = app_client.post('/api/enterprise/cascade/rescorla-wagner', json={
        "current_v": 0.50,
        "reward_sequence": [1.0, 1.0, 0.0, 0.0]
    })
    assert resp_sched.status_code == 200
    sched_data = resp_sched.get_json()
    assert sched_data["success"] is True
    assert "v_trajectory" in sched_data["data"]


def test_api_cascade_granovetter_endpoint(app_client):
    """Verifikasi endpoint POST /api/enterprise/cascade/granovetter."""
    # Individual evaluation
    resp = app_client.post('/api/enterprise/cascade/granovetter', json={
        "threshold": 0.35,
        "active_peer_ratio": 0.40
    })
    assert resp.status_code == 200
    assert resp.get_json()["is_active"] is True

    # Network simulation
    resp_sim = app_client.post('/api/enterprise/cascade/granovetter', json={
        "simulate": True,
        "num_agents": 30,
        "platform": "x"
    })
    assert resp_sim.status_code == 200
    sim_data = resp_sim.get_json()
    assert sim_data["success"] is True
    assert "final_adoption_rate" in sim_data["data"]


def test_api_cascade_hawkes_simulate_endpoint(app_client):
    """Verifikasi endpoint POST /api/enterprise/cascade/hawkes/simulate."""
    resp = app_client.post('/api/enterprise/cascade/hawkes/simulate', json={
        "platform": "tiktok",
        "time_horizon": 10.0,
        "max_events": 50
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["platform"] == "tiktok"
    assert "peak_intensity" in data["data"]


def test_api_cascade_swarm_simulate_endpoint(app_client):
    """Verifikasi endpoint POST /api/enterprise/cascade/swarm/simulate."""
    resp = app_client.post('/api/enterprise/cascade/swarm/simulate', json={
        "agents_count": 20,
        "rounds": 5,
        "platforms": ["x", "tiktok"]
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["deadlock_detected"] is False
    assert "x" in data["data"]["platform_results"]
    assert "tiktok" in data["data"]["platform_results"]


def test_api_platform_matrices_and_downstream(app_client):
    """Verifikasi endpoint GET platform-matrices & downstream-recommendations."""
    resp_mat = app_client.get('/api/enterprise/cascade/platform-matrices')
    assert resp_mat.status_code == 200
    mat_data = resp_mat.get_json()
    assert mat_data["success"] is True
    assert "x" in mat_data["platforms"]
    assert "reddit" in mat_data["platforms"]

    resp_down = app_client.get('/api/enterprise/cascade/downstream-recommendations')
    assert resp_down.status_code == 200
    down_data = resp_down.get_json()
    assert down_data["success"] is True
    assert down_data["recommendations"]["bsp_superstep_barrier_interval"] == 1
    assert down_data["recommendations"]["cascade_stability_certified"] is True
