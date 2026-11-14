"""Tests for mirofish.core.store — EntityStore, fan-out, inbox ordering."""

import pytest


def _store_cls():
    mod = pytest.importorskip("mirofish.core.store", reason="mirofish.core.store not implemented yet")
    cls = getattr(mod, "EntityStore", None)
    if cls is None:
        pytest.skip("EntityStore not implemented")
    return cls


@pytest.fixture
def store():
    cls = _store_cls()
    return cls(":memory:")


def test_put_get_query(store):
    store.put_entity("User", "u1", {"name": "Ada"})
    got = store.get_entity("User", "u1")
    assert got is not None
    assert got["data"]["name"] == "Ada"
    results = store.query_entities("User")
    assert len(results) == 1
    assert results[0]["entity_id"] == "u1"


def test_fanout_push_creates_per_recipient_feed_items(store):
    msg = {"item_ref": "Message:m1", "score": 0.7, "body": "hi"}
    out = store.fanout_push(msg, recipients=["bob", "carol"])
    assert len(out) == 2
    owners = {r["owner_agent_id"] for r in out}
    assert owners == {"bob", "carol"}
    for owner in ("bob", "carol"):
        inbox = store.inbox(owner)
        assert any(i["item_ref"] == "Message:m1" for i in inbox)


def test_inbox_ordering_pinned_unread_recency(store):
    # Controllable clock so materialized_tick ordering is deterministic.
    tick_box = {"t": 100}
    store2 = _store_cls()(":memory:", clock=lambda: tick_box["t"])

    # Pinned entity backing one item_ref.
    store2.put_entity("Post", "pin1", {"pinned": True})
    store2.put_entity("Post", "norm1", {"pinned": False})

    # Three feed items for the same owner at different ticks.
    store2.materialize_feed_items("u1", [{"item_ref": "Post:norm1", "score": 1.0}])  # t=100 (old read later)
    tick_box["t"] = 200
    store2.materialize_feed_items("u1", [{"item_ref": "Post:pin1", "score": 0.5}])   # t=200 pinned
    tick_box["t"] = 300
    store2.materialize_feed_items("u1", [{"item_ref": "Post:norm1", "score": 2.0}])  # t=300 newest unread

    # Mark the oldest item read.
    first = store2.inbox("u1")
    oldest_id = min(i["feed_item_id"] for i in first)
    store2.mark_read("u1", feed_item_id=oldest_id)

    inbox = store2.inbox("u1")
    refs = [i["item_ref"] for i in inbox]
    pinned_flags = [i["pinned"] for i in inbox]
    # Pinned item must sort first.
    assert inbox[0]["item_ref"] == "Post:pin1", f"pinned not first: {refs}"
    assert pinned_flags[0] is True
    # Among unpinned: unread before read; the read one is the oldest.
    unpinned = [i for i in inbox if not i["pinned"]]
    assert unpinned[0]["read_at"] is None
    assert unpinned[-1]["read_at"] is not None
    store2.close()
