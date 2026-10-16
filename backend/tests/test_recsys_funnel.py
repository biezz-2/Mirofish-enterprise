"""
Unit and Integration Tests for Agent 11: 3-Stage RecSys Funnel Engineer
Validates:
1. Stage 1 Candidate Generation (Graph Homophily, Semantic Cosine Similarity, Stance Proximity)
2. Stage 2 Heavy Ranking (Multi-task engagement scoring across 7 platforms)
3. Stage 3 Re-Ranking with Echo Chamber Damping (0.40 - 0.80), Time Decay, Diversity Penalty & Epsilon-Greedy
4. Shannon Entropy and Stance Diversity Metrics
5. Swarm Predictive Sandbox Simulation & Downstream Calibration Handoffs (Agent 12 & 13)
6. Enterprise API Endpoint Integration
"""

import math
import pytest
from flask import Flask
from app.services.recsys_funnel import (
    FeedItem,
    UserProfile,
    FunnelResult,
    SwarmRecSysSimulationResult,
    RecSysFunnel,
    PLATFORM_RECSYS_WEIGHTS,
    cosine_similarity,
    sigmoid,
)
from app.api.enterprise import enterprise_bp


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def sample_corpus():
    return [
        FeedItem(
            item_id="item_01",
            author_id="auth_a",
            topic="ai",
            stance=0.8,
            base_score=0.7,
            author_in_network=True,
            embedding=[0.8, 0.6, 0.0, 0.0],
            quality_score=0.85,
            controversy_score=0.2,
            arousal_score=0.4,
            visual_richness=0.6,
            created_at_hours_ago=1.0
        ),
        FeedItem(
            item_id="item_02",
            author_id="auth_b",
            topic="ai",
            stance=0.85,
            base_score=0.65,
            author_in_network=False,
            embedding=[0.75, 0.65, 0.0, 0.0],
            quality_score=0.80,
            controversy_score=0.15,
            arousal_score=0.3,
            visual_richness=0.5,
            created_at_hours_ago=2.0
        ),
        FeedItem(
            item_id="item_03",
            author_id="auth_c",
            topic="economy",
            stance=-0.6,
            base_score=0.6,
            author_in_network=False,
            embedding=[0.0, 0.1, 0.9, 0.4],
            quality_score=0.75,
            controversy_score=0.7,
            arousal_score=0.8,
            visual_richness=0.4,
            created_at_hours_ago=5.0
        ),
        FeedItem(
            item_id="item_04",
            author_id="auth_d",
            topic="tech",
            stance=0.2,
            base_score=0.5,
            author_in_network=False,
            embedding=[0.5, 0.5, 0.2, 0.1],
            quality_score=0.70,
            controversy_score=0.3,
            arousal_score=0.5,
            visual_richness=0.7,
            created_at_hours_ago=12.0
        ),
        FeedItem(
            item_id="item_05",
            author_id="auth_e",
            topic="climate",
            stance=-0.1,
            base_score=0.8,
            author_in_network=True,
            embedding=[0.1, 0.2, 0.8, 0.5],
            quality_score=0.90,
            controversy_score=0.4,
            arousal_score=0.6,
            visual_richness=0.8,
            created_at_hours_ago=24.0
        ),
    ]


@pytest.fixture
def sample_user():
    return UserProfile(
        user_id="user_test_01",
        stance=0.8,
        preferred_topics={"ai": 0.9, "tech": 0.6, "economy": 0.3},
        embedding=[0.8, 0.6, 0.0, 0.0],
        network_authors=["auth_a", "auth_e"],
        risk_tolerance=0.6,
        openness=0.75
    )


@pytest.fixture
def flask_test_client():
    app = Flask(__name__)
    app.register_blueprint(enterprise_bp, url_prefix='/api/enterprise')
    app.config['TESTING'] = True
    return app.test_client()


# =============================================================================
# UNIT TESTS
# =============================================================================
def test_feed_item_instantiation_and_defaults():
    """Memastikan FeedItem kompatibel backward dan mendukung atribut extended."""
    item = FeedItem(item_id="test_01", topic="politics", stance=0.5)
    assert item.item_id == "test_01"
    assert item.author_id == "anon"
    assert item.topic == "politics"
    assert item.stance == 0.5
    assert item.base_score == 0.5
    assert item.final_score == 0.0
    assert item.predicted_p_like == 0.0
    assert item.is_serendipity_exploration is False


def test_cosine_similarity_and_sigmoid():
    """Validasi numerik kosinus embedding dan aktivasi sigmoid."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert math.isclose(cosine_similarity(v1, v2), 1.0, rel_tol=1e-3)

    v_orth = [0.0, 1.0, 0.0]
    # Orthogonal cosine = 0.0 -> normalized to 0.5
    assert math.isclose(cosine_similarity(v1, v_orth), 0.5, rel_tol=1e-3)

    assert sigmoid(0.0) == 0.5
    assert sigmoid(100.0) == 1.0
    assert sigmoid(-100.0) == 0.0


def test_stage1_candidate_generation(sample_corpus, sample_user):
    """Tahap 1: Validasi candidate retrieval dengan homofili graf & cosine similarity."""
    funnel = RecSysFunnel(candidate_limit=3)
    candidates = funnel.stage1_candidates(
        items=sample_corpus,
        user_stance=sample_user.stance,
        user_embedding=sample_user.embedding,
        user_network=set(sample_user.network_authors),
        preferred_topics=sample_user.preferred_topics,
        limit=3
    )

    assert len(candidates) == 3
    # item_01 (auth_a in network, same stance 0.8, matching embedding) harus skor tertinggi
    assert candidates[0].item_id == "item_01"
    assert candidates[0].stage1_score > candidates[2].stage1_score


def test_stage2_heavy_ranking_multitask(sample_corpus, sample_user):
    """Tahap 2: Validasi multi-task scoring (like, share, reply, dwell) per platform."""
    funnel = RecSysFunnel(platform="x")
    ranked = funnel.stage2_heavy_rank(
        candidates=sample_corpus.copy(),
        user_stance=sample_user.stance,
        platform="x"
    )

    assert len(ranked) == len(sample_corpus)
    for it in ranked:
        assert 0.0 <= it.predicted_p_like <= 1.0
        assert 0.0 <= it.predicted_p_share <= 1.0
        assert 0.0 <= it.predicted_p_reply <= 1.0
        assert it.predicted_dwell_time_ms >= 300.0
        assert it.stage2_score > 0.0
        assert it.final_score == it.stage2_score

    # Memastikan terurut descending
    scores = [it.final_score for it in ranked]
    assert scores == sorted(scores, reverse=True)


def test_stage2_platform_weight_calibration(sample_corpus, sample_user):
    """Tahap 2: Membandingkan ranking X (virality/share) vs Reddit (reply) vs TikTok (dwell)."""
    funnel = RecSysFunnel()

    ranked_reddit = funnel.stage2_heavy_rank(sample_corpus.copy(), user_stance=0.8, platform="reddit")
    ranked_tiktok = funnel.stage2_heavy_rank(sample_corpus.copy(), user_stance=0.8, platform="tiktok")

    # Reddit memprioritaskan reply (diskusi/kontroversi tinggi)
    # item_03 memiliki kontroversi 0.7 dan stance friction tinggi terhadap user 0.8
    reddit_item3 = next(it for it in ranked_reddit if it.item_id == "item_03")
    assert reddit_item3.predicted_p_reply > 0.5

    # TikTok memprioritaskan dwell time (visual richness + quality)
    # item_05 memiliki visual_richness 0.8 dan quality 0.9
    tiktok_top_scores = [it.item_id for it in ranked_tiktok[:2]]
    assert "item_05" in tiktok_top_scores or "item_01" in tiktok_top_scores


def test_stage3_echo_chamber_damping_range():
    """Tahap 3: Validasi peredaman ruang gema dalam rentang 0.40 - 0.80."""
    funnel_low = RecSysFunnel(damping_factor=0.40, epsilon=0.0)
    funnel_high = RecSysFunnel(damping_factor=0.80, epsilon=0.0)

    # Item identik stance dengan user (stance_diff = 0.0 < 0.20)
    echo_item_low = FeedItem(item_id="e1", topic="ai", stance=0.8, base_score=0.9, stage2_score=0.9)
    echo_item_high = FeedItem(item_id="e2", topic="ai", stance=0.8, base_score=0.9, stage2_score=0.9)

    res_low = funnel_low.stage3_rerank([echo_item_low], user_stance=0.8, damping_factor=0.40)
    res_high = funnel_high.stage3_rerank([echo_item_high], user_stance=0.8, damping_factor=0.80)

    # Damping tinggi (0.80) harus meredam skor lebih besar daripada damping rendah (0.40)
    assert res_high[0].stage3_score < res_low[0].stage3_score


def test_stage3_time_decay_and_topic_diversity():
    """Tahap 3: Validasi time decay eksponensial dan penalti diversitas topik."""
    funnel = RecSysFunnel(time_decay_lambda=0.05, epsilon=0.0)

    fresh_item = FeedItem(item_id="f1", topic="ai", stance=0.2, stage2_score=0.8, created_at_hours_ago=0.5)
    stale_item = FeedItem(item_id="s1", topic="ai", stance=0.2, stage2_score=0.8, created_at_hours_ago=48.0)

    reranked = funnel.stage3_rerank([fresh_item, stale_item], user_stance=0.2)
    item_map = {it.item_id: it.stage3_score for it in reranked}

    assert item_map["f1"] > item_map["s1"]


def test_stage3_epsilon_greedy_exploration():
    """Tahap 3: Epsilon-greedy serendipity exploration swapping."""
    funnel = RecSysFunnel(epsilon=1.0)  # Always explore for testing
    items = [
        FeedItem(item_id=f"item_{i}", topic=f"topic_{i}", stance=0.0, stage2_score=1.0 - i * 0.1)
        for i in range(5)
    ]
    reranked = funnel.stage3_rerank(items, user_stance=0.0, epsilon=1.0)
    assert len(reranked) == 5
    # Pastikan setidaknya satu item ditandai serendipity
    assert any(it.is_serendipity_exploration for it in reranked)


def test_shannon_entropy_and_diversity_metrics():
    """Validasi kalkulasi Shannon Entropy dan metrik stance diversity."""
    # Feed seragam 1 topik -> Entropy = 0.0
    uniform_feed = [FeedItem(item_id=f"{i}", topic="ai", stance=0.5) for i in range(4)]
    assert RecSysFunnel.calculate_shannon_entropy(uniform_feed) == 0.0

    # Feed beragam 4 topik unik -> Entropy = 2.0 (log2(4))
    diverse_feed = [
        FeedItem(item_id="1", topic="ai", stance=0.8),
        FeedItem(item_id="2", topic="tech", stance=0.4),
        FeedItem(item_id="3", topic="economy", stance=-0.3),
        FeedItem(item_id="4", topic="culture", stance=-0.7),
    ]
    entropy = RecSysFunnel.calculate_shannon_entropy(diverse_feed)
    assert math.isclose(entropy, 2.0, rel_tol=1e-2)

    # Validasi metrik stance diversity
    metrics = RecSysFunnel.calculate_stance_diversity_metrics(diverse_feed, user_stance=0.8)
    assert metrics["topic_entropy"] > 1.5
    assert metrics["stance_variance"] > 0.2
    assert metrics["polar_spread"] >= 1.4
    assert metrics["echo_chamber_index"] == 0.25  # Hanya item 1 (|0.8 - 0.8| < 0.2)


def test_end_to_end_run_funnel(sample_corpus, sample_user):
    """End-to-End: Verifikasi corong 3 tahap penuh menghasilkan FunnelResult terstruktur."""
    funnel = RecSysFunnel(damping_factor=0.65, epsilon=0.05, candidate_limit=4)
    result = funnel.run_funnel(
        items=sample_corpus,
        user_profile=sample_user,
        platform="x",
        limit=3
    )

    assert isinstance(result, FunnelResult)
    assert result.user_id == sample_user.user_id
    assert result.stage1_candidates_count <= 4
    assert result.stage3_final_count == 3
    assert result.topic_entropy >= 0.0
    assert result.execution_time_ms > 0.0


def test_swarm_recsys_simulation():
    """Swarm Sandbox: Simulasi multi-agen (50 agen x 5 ronde) membuktikan mitigasi echo-chamber."""
    funnel = RecSysFunnel()
    sim_result = funnel.run_swarm_recsys_simulation(
        agents_count=50,
        corpus_size=100,
        rounds=5,
        damping_factor=0.75,
        epsilon=0.10,
        candidate_limit=30,
        platform="x"
    )

    assert isinstance(sim_result, SwarmRecSysSimulationResult)
    assert sim_result.agents_count == 50
    assert sim_result.deadlock_detected is False
    assert sim_result.mean_topic_entropy > 0.5
    assert sim_result.echo_chamber_reduction_percent >= 0.0
    assert sim_result.execution_time_seconds > 0.0

    # Downstream recommendations check
    p12_rec = sim_result.downstream_platform_recommendations
    assert p12_rec["calibrated_echo_damping"] == 0.75
    assert p12_rec["status"] == "CALIBRATED"

    a13_rec = sim_result.downstream_cascade_recommendations
    assert a13_rec["cascade_damping_factor"] == 0.75
    assert a13_rec["recommended_hawkes_alpha"] > 0.0


def test_upstream_agent_10_parameter_integration():
    """Memverifikasi parameter upstream dari Agent 10: limit=60, damping=0.75, eps=0.10."""
    upstream_params = {
        "recommended_candidate_limit": 60,
        "recommended_damping_factor": 0.75,
        "recommended_epsilon": 0.10
    }

    funnel = RecSysFunnel(
        candidate_limit=upstream_params["recommended_candidate_limit"],
        damping_factor=upstream_params["recommended_damping_factor"],
        epsilon=upstream_params["recommended_epsilon"],
    )

    assert funnel.candidate_limit == 60
    assert funnel.damping_factor == 0.75
    assert funnel.epsilon == 0.10


def test_edge_cases():
    """Penanganan edge case: korpus kosong, 1 item, nilai ekstrim."""
    funnel = RecSysFunnel()
    # Korpus kosong
    assert funnel.stage1_candidates([]) == []
    assert funnel.stage2_heavy_rank([]) == []
    assert funnel.stage3_rerank([]) == []
    assert funnel.calculate_shannon_entropy([]) == 0.0

    metrics_empty = funnel.calculate_stance_diversity_metrics([])
    assert metrics_empty["topic_entropy"] == 0.0

    # Single item
    single = [FeedItem(item_id="solo", topic="ai", stance=1.0, base_score=0.5)]
    ranked = funnel.stage2_heavy_rank(single)
    reranked = funnel.stage3_rerank(ranked, user_stance=-1.0)
    assert len(reranked) == 1
    assert reranked[0].item_id == "solo"


# =============================================================================
# API ENDPOINT INTEGRATION TESTS
# =============================================================================
def test_api_recsys_rank_backward_compatible(flask_test_client):
    """Verifikasi endpoint lama POST /api/enterprise/recsys/rank tetap berjalan 100%."""
    payload = {
        "items": [
            {"id": "1", "author_id": "u1", "topic": "ai", "stance": 0.8},
            {"id": "2", "author_id": "u2", "topic": "ai", "stance": 0.85},
            {"id": "3", "author_id": "u3", "topic": "economy", "stance": -0.5},
            {"id": "4", "author_id": "u4", "topic": "tech", "stance": 0.1},
        ],
        "user_stance": 0.8
    }
    resp = flask_test_client.post('/api/enterprise/recsys/rank', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["entropy"] > 0.0
    assert len(data["items"]) == 4


def test_api_recsys_funnel_and_weights(flask_test_client, sample_user):
    """Verifikasi endpoint baru POST /api/enterprise/recsys/funnel dan GET /recsys/weights."""
    # Test GET weights
    resp_w = flask_test_client.get('/api/enterprise/recsys/weights')
    assert resp_w.status_code == 200
    weights_data = resp_w.get_json()
    assert weights_data["success"] is True
    assert "x" in weights_data["weights"]
    assert "reddit" in weights_data["weights"]

    # Test POST funnel
    payload = {
        "items": [
            {"item_id": f"it_{i}", "topic": "ai" if i % 2 == 0 else "tech", "stance": 0.5 - i * 0.2}
            for i in range(6)
        ],
        "user_profile": sample_user.model_dump(),
        "platform": "x",
        "limit": 4,
        "damping_factor": 0.70,
        "epsilon": 0.08
    }
    resp_f = flask_test_client.post('/api/enterprise/recsys/funnel', json=payload)
    assert resp_f.status_code == 200
    data_f = resp_f.get_json()
    assert data_f["success"] is True
    assert data_f["result"]["stage3_final_count"] == 4
    assert data_f["result"]["topic_entropy"] >= 0.0
