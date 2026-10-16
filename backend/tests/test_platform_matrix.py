"""Unit and Integration Tests for MiroFish Enterprise 7-Platform Calibration Matrix (Agent 12)."""
import pytest
import math
from app import create_app
from app.services.platform_matrix import (
    PlatformMatrixService,
    PlatformWeights,
    PlatformParetoMetrics,
    SwarmPlatformSimulationResult,
    PLATFORM_CALIBRATION_DB,
    CANONICAL_7_PLATFORMS,
)

@pytest.fixture
def service():
    return PlatformMatrixService()

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_canonical_7_platforms_uniqueness(service):
    platforms = service.list_supported_platforms(canonical_only=True)
    assert len(platforms) == 7
    assert len(set(platforms)) == 7
    expected = {'x', 'reddit', 'tiktok', 'instagram', 'youtube', 'linkedin', 'threads'}
    assert set(platforms) == expected
    assert 'twitter' not in platforms
    assert 'x' in platforms

def test_platform_aliases(service):
    aliases = service.get_aliases()
    assert aliases['twitter'] == 'x'
    assert aliases['ig'] == 'instagram'
    assert aliases['fb'] == 'facebook'
    assert aliases['yt'] == 'youtube'
    assert aliases['li'] == 'linkedin'
    assert aliases['th'] == 'threads'
    w_twitter = service.get_platform_weights('twitter')
    w_x = service.get_platform_weights('x')
    assert w_twitter.platform_name == w_x.platform_name == 'X (Twitter)'
    assert w_twitter.virality_decay_rate == w_x.virality_decay_rate
    w_fb = service.get_platform_weights('fb')
    assert w_fb.platform_name == 'Facebook'

def test_extended_platforms(service):
    all_platforms = service.list_all_platforms()
    assert 'facebook' in all_platforms
    assert len(all_platforms) >= 8
    w_fb = service.get_platform_weights('facebook')
    assert w_fb.platform_name == 'Facebook'
    assert 0.85 <= w_fb.lurker_ratio <= 0.95
    assert w_fb.echo_chamber_vulnerability >= 0.80

def test_pareto_90_9_1_ratios_sum_to_one(service):
    all_keys = service.list_all_platforms()
    for key in all_keys:
        w = service.get_platform_weights(key)
        total = w.lurker_ratio + w.contributor_ratio + w.creator_ratio
        assert abs(total - 1.0) < 1e-4, f'Platform {key} ratio sum {total} != 1.0'
        assert 0.84 <= w.lurker_ratio <= 0.95
        assert 0.05 <= w.contributor_ratio <= 0.15
        assert 0.01 <= w.creator_ratio <= 0.03

def test_sample_user_roles_population(service):
    res = service.sample_user_roles_population('x', n_users=1000, seed=42)
    assert res['total_users'] == 1000
    assert res['pareto_compliance'] is True
    assert 0.85 <= res['lurker_ratio'] <= 0.92
    assert 0.07 <= res['contributor_ratio'] <= 0.13
    assert 0.005 <= res['creator_ratio'] <= 0.035

def test_pareto_power_law_metrics_formula(service):
    for key in CANONICAL_7_PLATFORMS:
        m = service.calculate_platform_pareto_metrics(key)
        alpha = m.pareto_alpha
        expected_gini = round(1.0 / (2.0 * alpha - 1.0), 4)
        assert abs(m.gini_coefficient - expected_gini) < 1e-3
        factor = 1.0 - 1.0 / alpha
        expected_top_1 = round(math.pow(0.01, factor), 4)
        assert abs(m.top_1_percent_share - expected_top_1) < 1e-3
        expected_top_10 = round(math.pow(0.10, factor), 4)
        assert abs(m.top_10_percent_share - expected_top_10) < 1e-3

def test_cross_platform_inequality_ranking(service):
    m_tiktok = service.calculate_platform_pareto_metrics('tiktok')
    m_reddit = service.calculate_platform_pareto_metrics('reddit')
    m_x = service.calculate_platform_pareto_metrics('x')
    assert m_tiktok.gini_coefficient > m_x.gini_coefficient > m_reddit.gini_coefficient
    assert m_tiktok.top_1_percent_share > 0.50
    assert m_reddit.top_1_percent_share < 0.20

def test_sample_pareto_reach_convergence(service):
    reach_res = service.sample_pareto_reach('x', n_samples=500, seed=123)
    assert reach_res['sample_count'] == 500
    assert reach_res['empirical_mean'] > reach_res['empirical_median']
    assert reach_res['empirical_max'] > reach_res['empirical_mean']
    theo = reach_res['theoretical_gini']
    emp = reach_res['empirical_gini']
    assert abs(theo - emp) < 0.15

def test_feed_scoring_visual_affinity(service):
    text_item = {'stance': 0.0, 'base_score': 0.5, 'quality_score': 0.8, 'controversy_score': 0.2, 'visual_richness': 0.1, 'created_at_hours_ago': 1.0}
    video_item = {'stance': 0.0, 'base_score': 0.5, 'quality_score': 0.8, 'controversy_score': 0.2, 'visual_richness': 1.0, 'created_at_hours_ago': 1.0}
    score_tt_text = service.score_platform_feed_item('tiktok', text_item)
    score_tt_video = service.score_platform_feed_item('tiktok', video_item)
    assert score_tt_video > score_tt_text
    score_rd_text = service.score_platform_feed_item('reddit', text_item)
    score_rd_video = service.score_platform_feed_item('reddit', video_item)
    tt_ratio = score_tt_video / score_tt_text
    rd_ratio = score_rd_video / score_rd_text
    assert tt_ratio > rd_ratio

def test_feed_scoring_virality_decay(service):
    fresh_item = {'stance': 0.0, 'base_score': 0.6, 'quality_score': 0.8, 'created_at_hours_ago': 0.5}
    stale_item = {'stance': 0.0, 'base_score': 0.6, 'quality_score': 0.8, 'created_at_hours_ago': 48.0}
    score_x_fresh = service.score_platform_feed_item('x', fresh_item)
    score_x_stale = service.score_platform_feed_item('x', stale_item)
    assert score_x_stale < score_x_fresh * 0.35
    score_yt_fresh = service.score_platform_feed_item('youtube', fresh_item)
    score_yt_stale = service.score_platform_feed_item('youtube', stale_item)
    assert (score_yt_stale / score_yt_fresh) > (score_x_stale / score_x_fresh)

def test_swarm_simulation_all_7_platforms(service):
    test_platforms = CANONICAL_7_PLATFORMS + ['facebook']
    for plat in test_platforms:
        sim = service.simulate_platform_sandbox(platform_key=plat, n_agents=50, n_rounds=15, corpus_size=100, seed=42)
        assert isinstance(sim, SwarmPlatformSimulationResult)
        assert sim.platform_key == plat
        assert sim.deadlock_detected is False
        assert sim.status == 'CALIBRATED'
        assert sim.total_actions_evaluated == 50 * 15
        assert sim.execution_time_seconds < 1.5
        assert sim.pareto_compliance_pass is True
        assert sim.empirical_gini_coefficient > 0.0
        assert sim.mean_echo_damping_applied > 0.0

def test_downstream_recommendations(service):
    recs = service.get_downstream_recommendations()
    assert recs['calibration_status'] == 'READY_FOR_PROPAGATION'
    assert recs['supported_canonical_platforms'] == CANONICAL_7_PLATFORMS
    a13 = recs['agent_13']
    assert 'cascade_damping_factor' in a13
    assert 'recommended_hawkes_alpha' in a13
    assert 'platform_hawkes_matrix' in a13
    for plat in CANONICAL_7_PLATFORMS:
        h_plat = a13['platform_hawkes_matrix'][plat]
        assert 'hawkes_mu' in h_plat
        assert 'hawkes_alpha' in h_plat
        assert 'hawkes_beta' in h_plat
        assert 'granovetter_barrier' in h_plat
    a14 = recs['agent_14']
    assert a14['bsp_superstep_barrier_interval'] == 1
    assert a14['sqlite_wal_checkpoint_frequency_rounds'] == 5
    assert a14['state_hash_algorithm'] == 'SHA-256'
    assert 'platform_batch_sizing' in a14
    for plat in CANONICAL_7_PLATFORMS:
        assert plat in a14['platform_batch_sizing']

def test_api_get_platforms(client):
    res = client.get('/api/enterprise/platforms')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['platforms']) == 7
    assert 'x' in data['platforms']
    assert 'matrix' in data
    assert len(data['matrix']) == 7

def test_api_get_platform_detail(client):
    res = client.get('/api/enterprise/platforms/tiktok')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['weights']['platform_name'] == 'TikTok'
    assert data['weights']['visual_affinity'] == 1.0
    assert data['pareto_metrics']['pareto_alpha'] == 1.15
    assert abs(data['pareto_metrics']['gini_coefficient'] - 0.7692) < 1e-3

def test_api_get_pareto_metrics(client):
    res = client.get('/api/enterprise/platforms/pareto-metrics')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['pareto_metrics']) == 7
    assert 'reddit' in data['pareto_metrics']

def test_api_simulate_pareto(client):
    payload = {'platform': 'x', 'n_agents': 30, 'n_rounds': 10, 'seed': 42}
    res = client.post('/api/enterprise/platforms/simulate-pareto', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    sim = data['simulation']
    assert sim['platform_key'] == 'x'
    assert sim['deadlock_detected'] is False
    assert sim['total_actions_evaluated'] == 300

def test_api_downstream_recommendations(client):
    res = client.get('/api/enterprise/platforms/downstream-recommendations')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'agent_13' in data['recommendations']
    assert 'agent_14' in data['recommendations']
