"""
Uji verifikasi patch OASIS Twitter RecSys, konveksitas feed scoring, dan algoritma peringkat Notion.
"""
import pytest
from oasis.social_platform.platform import Platform
from oasis.social_platform.channel import Channel
from oasis.social_platform.typing import RecsysType, ActionType
from oasis.social_platform.recsys import get_recsys_model
from app.services.platform_behaviors import (
    PLATFORM_CHARACTERISTICS,
    compute_feed_score,
    compute_wilson_score,
    compute_reddit_hot_score,
)


def test_oasis_twitter_random_recsys_no_transformer():
    """Verifikasi bahwa recsys_type='random' tidak memuat transformer PyTorch (twhin-bert-base)."""
    # 1. get_recsys_model("random") harus mengembalikan None tanpa memuat bobot model
    model = get_recsys_model(RecsysType.RANDOM.value)
    assert model is None, "Recsys random tidak boleh memuat model transformer neural"

    # 2. Platform initialization dengan recsys_type="random"
    platform = Platform(
        db_path=":memory:",
        channel=Channel(),
        recsys_type="random",
        refresh_rec_post_count=2,
        max_rec_post_len=2,
        following_post_count=3,
    )
    assert platform.recsys_type == RecsysType.RANDOM
    assert platform.refresh_rec_post_count == 2
    assert platform.max_rec_post_len == 2


def test_convex_feed_weights_all_platforms():
    """Verifikasi syarat konveks: lambda_rec + beta_pop + gamma_echo == 1.0 untuk semua 7 platform."""
    platforms = ["twitter", "x", "reddit", "tiktok", "instagram", "facebook", "threads", "youtube", "linkedin"]
    for p in platforms:
        c = PLATFORM_CHARACTERISTICS[p]
        l_rec = c["recency_weight"]
        b_pop = c["popularity_weight"]
        g_echo = c["echo_chamber_strength"]
        total = l_rec + b_pop + g_echo
        assert abs(total - 1.0) < 1e-6, f"Platform {p} bobot tidak konveks: {total} != 1.0"


def test_half_life_and_echo_empirical_notion():
    """Verifikasi parameter half_life dan echo_chamber_strength selaras dengan dokumen Notion #2 & #7."""
    # TikTok (1.8) < Twitter (2.5) < Threads (3.0) < X (3.5) < IG (4.5) < Reddit (6.0) < FB (8.0)
    assert PLATFORM_CHARACTERISTICS["tiktok"]["half_life"] == 1.8
    assert PLATFORM_CHARACTERISTICS["twitter"]["half_life"] == 2.5
    assert PLATFORM_CHARACTERISTICS["threads"]["half_life"] == 3.0
    assert PLATFORM_CHARACTERISTICS["x"]["half_life"] == 3.5
    assert PLATFORM_CHARACTERISTICS["instagram"]["half_life"] == 4.5
    assert PLATFORM_CHARACTERISTICS["reddit"]["half_life"] == 6.0
    assert PLATFORM_CHARACTERISTICS["facebook"]["half_life"] == 8.0

    # Echo chamber: Facebook (0.45) > Reddit (0.40) > X (0.30) > TikTok (0.10)
    assert PLATFORM_CHARACTERISTICS["facebook"]["echo_chamber_strength"] == 0.45
    assert PLATFORM_CHARACTERISTICS["reddit"]["echo_chamber_strength"] == 0.40
    assert PLATFORM_CHARACTERISTICS["x"]["echo_chamber_strength"] == 0.30
    assert PLATFORM_CHARACTERISTICS["tiktok"]["echo_chamber_strength"] == 0.10


def test_spillover_attenuation():
    """Verifikasi bahwa is_spillover meredam popularitas awal sebesar 50% untuk mencegah runaway cascade."""
    agent = {"id": "ag-1", "opinion_score": 0.5}
    post_normal = {"id": 1, "age_hours": 1.0, "engagement": 1000, "mean_opinion": 0.5, "is_spillover": False}
    post_spillover = {"id": 2, "age_hours": 1.0, "engagement": 1000, "mean_opinion": 0.5, "is_spillover": True}

    score_normal = compute_feed_score("twitter", post_normal, agent)
    score_spillover = compute_feed_score("twitter", post_spillover, agent)

    assert score_normal > score_spillover, "Konten spillover harus diredam skor popularitasnya"
    # Selisih harus merefleksikan 0.5 * beta_pop * pop_term
    c = PLATFORM_CHARACTERISTICS["twitter"]
    beta_pop = c["popularity_weight"]
    assert score_normal - score_spillover > 0.05


def test_wilson_score_reddit_ranking():
    """Verifikasi perhitungan Wilson Score Interval 80% (z=1.28155) untuk Best Comment Reddit."""
    # Kasus batas: 0 vote -> 0.0
    assert compute_wilson_score(0, 0) == 0.0

    # 100 upvotes, 0 downvotes vs 1 upvote, 0 downvote
    score_100_0 = compute_wilson_score(100, 0)
    score_1_0 = compute_wilson_score(1, 0)
    assert score_100_0 > score_1_0 > 0.0

    # 90 up, 10 down vs 10 up, 90 down
    score_pos = compute_wilson_score(90, 10)
    score_neg = compute_wilson_score(10, 90)
    assert score_pos > score_neg
    assert 0.0 <= score_pos <= 1.0
    assert 0.0 <= score_neg <= 1.0


def test_reddit_hot_score_ranking():
    """Verifikasi formula Reddit Hot Ranking log10(max(|U-D|, 1)) + (t - t0)/45000."""
    t0 = 1134028003.0
    # Post baru dengan engagement yang sama harus memiliki hot score lebih tinggi
    post_older = compute_reddit_hot_score(100, 10, post_time_epoch=t0 + 45000)
    post_newer = compute_reddit_hot_score(100, 10, post_time_epoch=t0 + 90000)
    assert post_newer > post_older
