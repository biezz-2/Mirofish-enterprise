"""Tests for mirofish.core.feed — feed item scoring/ordering/masking."""

import pytest


def _module():
    return pytest.importorskip("mirofish.core.feed", reason="mirofish.core.feed not implemented yet")


def _call(fn_name, *args, **kwargs):
    mod = _module()
    fn = getattr(mod, fn_name, None)
    if fn is None:
        pytest.skip(f"{fn_name} not implemented in mirofish.core.feed")
    return fn(*args, **kwargs)


def _engagement_ranked(*args, **kwargs):
    """Resolve the engagement-ranked scorer under a few plausible names."""
    mod = _module()
    for name in ("engagement_ranked", "score_engagement_ranked", "EngagementRankedScorer"):
        fn = getattr(mod, name, None)
        if fn is not None:
            return fn
    pytest.skip("no engagement_ranked scorer found in mirofish.core.feed")


def test_engagement_ranked_orders_by_weighted_signals():
    scorer = _engagement_ranked()
    # Items designed so weighted-sum ordering is unambiguous:
    # high engagement should beat low engagement when weights are positive.
    items = [
        {"item_id": "low", "signals": {"engagement": 1.0, "recency": 0.0}},
        {"item_id": "high", "signals": {"engagement": 100.0, "recency": 0.0}},
        {"item_id": "mid", "signals": {"engagement": 50.0, "recency": 0.0}},
    ]
    weights = {"engagement": 1.0, "recency": 0.0}
    try:
        ranked = scorer.score_and_rank(items, weights) if hasattr(scorer, "score_and_rank") else scorer(items, weights)
    except TypeError:
        ranked = scorer(items)
    ids = [getattr(r, "item_id", None) or (r.get("item_id") if isinstance(r, dict) else r[0]) for r in ranked]
    assert ids[0] == "high"
    assert ids[-1] == "low"


def test_chronological_ignores_scores():
    fn = None
    mod = _module()
    for name in ("chronological", "chronological_order", "ChronologicalScorer"):
        fn = getattr(mod, name, None)
        if fn is not None:
            break
    if fn is None:
        pytest.skip("no chronological scorer found in mirofish.core.feed")
    items = [
        {"item_id": "new", "ts": 300, "score": 0.0},
        {"item_id": "old", "ts": 100, "score": 999.0},
        {"item_id": "mid", "ts": 200, "score": 1.0},
    ]
    try:
        ranked = fn(items)
    except TypeError:
        ranked = fn(items, key="ts")
    ts = [r.get("ts") if isinstance(r, dict) else getattr(r, "ts", None) for r in ranked]
    assert ts == sorted(ts, reverse=True), "chronological must order by time, not score"


def test_observation_mask_zeroes_masked_families():
    mod = _module()
    fn = getattr(mod, "apply_observation_mask", None) or getattr(mod, "mask_unobserved_signals", None)
    if fn is None:
        pytest.skip("no observation mask helper in mirofish.core.feed")
    signals = {"recency": 0.5, "secret_family": 10.0, "engagement": 2.0}
    observed = {"recency", "engagement"}
    masked = fn(signals, observed)
    masked = masked if isinstance(masked, dict) else dict(masked)
    assert masked.get("secret_family", 0) == 0 or masked.get("secret_family") is None
    assert masked.get("recency") == 0.5


def test_author_diversity_cap():
    mod = _module()
    fn = getattr(mod, "author_diversity_cap", None) or getattr(mod, "dedupe_authors", None)
    if fn is None:
        pytest.skip("no author diversity cap in mirofish.core.feed")
    items = [
        {"item_id": f"i{k}", "author": "alice", "score": 100 - k}
        for k in range(5)
    ] + [{"item_id": "b1", "author": "bob", "score": 50}]
    out = fn(items, max_per_author=2)
    authors = [
        r.get("author") if isinstance(r, dict) else getattr(r, "author", None)
        for r in out
    ]
    from collections import Counter

    assert Counter(authors)["alice"] <= 2
    assert "bob" in authors
