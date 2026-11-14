"""Tests for mirofish.agent.memory — MemoryStream retrieval, TemporalKG, reflection."""

import pytest


def _mem():
    return pytest.importorskip("mirofish.agent.memory", reason="mirofish.agent.memory not implemented yet")


def test_memory_stream_retrieval_ranking():
    mod = _mem()
    cls = getattr(mod, "MemoryStream", None)
    if cls is None:
        pytest.skip("MemoryStream not implemented")
    mem = cls(agent_id="a1")
    # Two memories: one relevant+important, one irrelevant.
    mem.add_observation("user loves adopting cats from shelters", tick=10, importance=0.9)
    mem.add_observation("user once saw a documentary about birds", tick=11, importance=0.2)
    hits = mem.retrieve("cats shelter", at_tick=12, k=5)
    assert hits, "retrieve returned nothing"
    scores, records = zip(*hits)
    assert list(scores) == sorted(scores, reverse=True), "results must be score-descending"
    assert "cats" in records[0].content


def test_temporal_kg_interval_invalidation():
    mod = _mem()
    cls = getattr(mod, "TemporalKG", None)
    if cls is None:
        pytest.skip("TemporalKG not implemented")
    kg = cls()
    # Edge valid [0, 10): agent:1 EXPOSED topic:cats
    kg.add_edge("agent:1", "topic:cats", "EXPOSED", t_start=0, t_end=10)
    inside = kg.query({"src": "agent:1", "dst": "topic:cats"}, at_tick=5)
    outside = kg.query({"src": "agent:1", "dst": "topic:cats"}, at_tick=20)
    assert inside, "edge should be active at t=5"
    assert not outside, "edge must be inactive at t=20 (interval [0,10))"

    # Supersession: a new edge on the same triple closes the old interval.
    kg2 = cls()
    e1 = kg2.add_edge("agent:2", "topic:dogs", "INTERACT", t_start=0)
    kg2.add_edge("agent:2", "topic:dogs", "INTERACT", t_start=5)
    assert e1.t_end == 5, f"superseded edge should close at t=5, got {e1.t_end}"
    still = kg2.query({"src": "agent:2"}, at_tick=3)
    gone = kg2.query({"src": "agent:2"}, at_tick=7)
    assert len(still) == 1 and len(gone) == 1  # history preserved, intervals differ
    assert still[0].t_start == 0 and gone[0].t_start == 5


def test_reflection_trigger():
    mod = _mem()
    cls = getattr(mod, "MemoryStream", None)
    if cls is None:
        pytest.skip("MemoryStream not implemented")
    mem = cls(agent_id="a2", theta_r=5.0)
    # Push enough importance-weighted mass to cross theta_r.
    for i in range(8):
        mem.add_observation(f"memorable event number {i} about cats", tick=i, importance=0.9)
    reflections = [
        r for r in mem.records
        if str(getattr(r.type, "value", r.type)) == "reflection"
    ]
    assert reflections, "expected an automatic reflection record after crossing theta_r"
