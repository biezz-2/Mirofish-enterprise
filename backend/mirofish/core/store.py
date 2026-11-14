"""Generic entity store backed by SQLite (stdlib ``sqlite3``).

Replaces OASIS's hard-coded schema with four generic tables:

- ``entities``     — typed key/value entities; ``data`` is a JSON document.
- ``relations``    — typed edges between entity endpoints; ``attrs`` is JSON.
- ``interactions`` — append-only log of agent actions.
- ``feed_items``   — per-owner materialized feed/inbox entries.

Two delivery paradigms share this store:

- **PULL** (public / semi-public): ``materialize_feed_items`` writes ranked
  candidates into an owner's feed at query time.
- **PUSH** (private): ``fanout_push`` replicates a message into each
  recipient's inbox at write time; ``inbox`` observes it ordered by
  pinned > unread > recency.

All timestamps are integer "ticks" produced by an injected clock callable
(default: wall-clock seconds since epoch), so simulations can run on a
logical clock.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

Clock = Callable[[], int]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    entity_type  TEXT NOT NULL,
    entity_id    TEXT NOT NULL,
    data         TEXT NOT NULL,               -- JSON object
    created_tick INTEGER NOT NULL,
    PRIMARY KEY (entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS relations (
    relation_type TEXT NOT NULL,
    from_type     TEXT NOT NULL,
    from_id       TEXT NOT NULL,
    to_type       TEXT NOT NULL,
    to_id         TEXT NOT NULL,
    attrs         TEXT NOT NULL DEFAULT '{}', -- JSON object
    created_tick  INTEGER NOT NULL,
    PRIMARY KEY (relation_type, from_type, from_id, to_type, to_id)
);

CREATE TABLE IF NOT EXISTS interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick            INTEGER NOT NULL,
    actor_id        TEXT NOT NULL,
    action_id       TEXT NOT NULL,
    target_ref      TEXT,
    payload         TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS feed_items (
    feed_item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_agent_id    TEXT NOT NULL,
    item_ref          TEXT NOT NULL,          -- "EntityType:entity_id" or opaque ref
    score             REAL,
    materialized_tick INTEGER NOT NULL,
    read_at           INTEGER,                -- NULL = unread
    delivered_at      INTEGER                 -- set for push fan-out / pull materialization
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_type, from_id);
CREATE INDEX IF NOT EXISTS idx_relations_to   ON relations(to_type, to_id);
CREATE INDEX IF NOT EXISTS idx_feed_owner     ON feed_items(owner_agent_id, read_at, materialized_tick);
"""


def _dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def _loads(text: Optional[str]) -> Any:
    if text is None:
        return None
    return json.loads(text)


def entity_key(entity_id: Any) -> str:
    """Canonical string form of an entity id.

    Composite primary keys (lists/tuples/dicts) are serialized as JSON so
    they can be stored in a single TEXT column deterministically.
    """
    if isinstance(entity_id, (list, tuple)):
        return json.dumps(list(entity_id), default=str)
    if isinstance(entity_id, Mapping):
        return json.dumps(dict(entity_id), sort_keys=True, default=str)
    return str(entity_id)


class EntityStore:
    """SQLite-backed generic entity/relation/feed store."""

    def __init__(
        self,
        path: "str | Path" = ":memory:",
        clock: Optional[Clock] = None,
    ) -> None:
        self._clock: Clock = clock or (lambda: int(time.time()))
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------
    # plumbing
    # ------------------------------------------------------------------
    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def tick(self) -> int:
        return int(self._clock())

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "EntityStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # entities
    # ------------------------------------------------------------------
    def put_entity(
        self,
        entity_type: str,
        entity_id: Any,
        data: Mapping[str, Any],
    ) -> None:
        """Insert or update an entity. ``created_tick`` is set once."""
        eid = entity_key(entity_id)
        tick = self.tick()
        self._conn.execute(
            """
            INSERT INTO entities (entity_type, entity_id, data, created_tick)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (entity_type, entity_id)
            DO UPDATE SET data = excluded.data
            """,
            (entity_type, eid, _dumps(dict(data)), tick),
        )
        self._conn.commit()

    def get_entity(
        self, entity_type: str, entity_id: Any
    ) -> Optional[dict]:
        """Return ``{"entity_type", "entity_id", "data", "created_tick"}`` or None."""
        row = self._conn.execute(
            "SELECT * FROM entities WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_key(entity_id)),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def query_entities(
        self,
        entity_type: str,
        filters: Optional[Mapping[str, Any]] = None,
    ) -> list[dict]:
        """Return all entities of ``entity_type`` matching ``filters``.

        ``filters`` keys are matched against the JSON ``data`` document
        (equality), plus the pseudo-key ``entity_id`` for the primary key.
        """
        filters = dict(filters or {})
        eid_filter = filters.pop("entity_id", None)
        sql = "SELECT * FROM entities WHERE entity_type = ?"
        params: list[Any] = [entity_type]
        if eid_filter is not None:
            sql += " AND entity_id = ?"
            params.append(entity_key(eid_filter))
        rows = self._conn.execute(sql, params).fetchall()
        out = []
        for row in rows:
            ent = self._row_to_entity(row)
            if filters and not all(
                ent["data"].get(k) == v for k, v in filters.items()
            ):
                continue
            out.append(ent)
        return out

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> dict:
        return {
            "entity_type": row["entity_type"],
            "entity_id": _loads(row["entity_id"])
            if row["entity_id"].startswith(("[", "{"))
            else row["entity_id"],
            "data": _loads(row["data"]),
            "created_tick": row["created_tick"],
        }

    # ------------------------------------------------------------------
    # relations
    # ------------------------------------------------------------------
    def put_relation(
        self,
        relation_type: str,
        from_type: str,
        from_id: Any,
        to_type: str,
        to_id: Any,
        attrs: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO relations
                (relation_type, from_type, from_id, to_type, to_id, attrs, created_tick)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (relation_type, from_type, from_id, to_type, to_id)
            DO UPDATE SET attrs = excluded.attrs
            """,
            (
                relation_type,
                from_type,
                entity_key(from_id),
                to_type,
                entity_key(to_id),
                _dumps(dict(attrs or {})),
                self.tick(),
            ),
        )
        self._conn.commit()

    def relations_of(
        self,
        agent_id: Any,
        relation_type: Optional[str] = None,
    ) -> list[dict]:
        """All relations where ``agent_id`` appears as either endpoint.

        Each row gains ``direction``: ``"out"`` when the agent is ``from_id``,
        ``"in"`` when it is ``to_id``.
        """
        aid = entity_key(agent_id)
        sql = "SELECT * FROM relations WHERE from_id = ? OR to_id = ?"
        params: list[Any] = [aid, aid]
        if relation_type is not None:
            sql += " AND relation_type = ?"
            params.append(relation_type)
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_relation(r) for r in rows]

    def relations_between(
        self,
        a_id: Any,
        b_id: Any,
        relation_type: Optional[str] = None,
    ) -> list[dict]:
        """Relations connecting two endpoint ids in either direction."""
        a, b = entity_key(a_id), entity_key(b_id)
        sql = """
            SELECT * FROM relations
            WHERE (from_id = ? AND to_id = ?) OR (from_id = ? AND to_id = ?)
        """
        params: list[Any] = [a, b, b, a]
        if relation_type is not None:
            sql += " AND relation_type = ?"
            params.append(relation_type)
        return [
            self._row_to_relation(r)
            for r in self._conn.execute(sql, params).fetchall()
        ]

    def has_relation(
        self,
        a_id: Any,
        b_id: Any,
        relation_type: Optional[str] = None,
    ) -> bool:
        return bool(self.relations_between(a_id, b_id, relation_type))

    @staticmethod
    def _row_to_relation(row: sqlite3.Row) -> dict:
        return {
            "relation_type": row["relation_type"],
            "from_type": row["from_type"],
            "from_id": row["from_id"],
            "to_type": row["to_type"],
            "to_id": row["to_id"],
            "attrs": _loads(row["attrs"]),
            "created_tick": row["created_tick"],
        }

    # ------------------------------------------------------------------
    # interactions (append-only action log)
    # ------------------------------------------------------------------
    def record_interaction(
        self,
        actor_id: Any,
        action_id: str,
        target_ref: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        tick: Optional[int] = None,
    ) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO interactions (tick, actor_id, action_id, target_ref, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self.tick() if tick is None else int(tick),
                entity_key(actor_id),
                action_id,
                target_ref,
                _dumps(dict(payload or {})),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    # ------------------------------------------------------------------
    # feed items — PULL materialization
    # ------------------------------------------------------------------
    def materialize_feed_items(
        self,
        owner_agent_id: Any,
        items: Iterable[Mapping[str, Any]],
    ) -> list[int]:
        """PULL path: write ranked feed candidates for one owner.

        Each item is a mapping with ``item_ref`` (required) and optional
        ``score``. Returns the new ``feed_item_id``s.
        """
        owner = entity_key(owner_agent_id)
        now = self.tick()
        ids: list[int] = []
        for item in items:
            cur = self._conn.execute(
                """
                INSERT INTO feed_items
                    (owner_agent_id, item_ref, score, materialized_tick, delivered_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    owner,
                    str(item["item_ref"]),
                    item.get("score"),
                    now,
                    now,
                ),
            )
            ids.append(int(cur.lastrowid))
        self._conn.commit()
        return ids

    # ------------------------------------------------------------------
    # feed items — PUSH fan-out
    # ------------------------------------------------------------------
    def fanout_push(
        self,
        message: Mapping[str, Any],
        recipients: Iterable[Any],
    ) -> list[dict]:
        """PUSH path: replicate ``message`` into each recipient's inbox.

        ``message`` must contain ``item_ref``; optional ``score`` and any
        other keys are preserved in the returned per-recipient records.
        Returns one record per recipient with ``feed_item_id`` and the
        recipient's current ``unread_count`` (push unread aggregation).
        """
        item_ref = str(message["item_ref"])
        score = message.get("score")
        now = self.tick()
        results: list[dict] = []
        for recipient in recipients:
            owner = entity_key(recipient)
            cur = self._conn.execute(
                """
                INSERT INTO feed_items
                    (owner_agent_id, item_ref, score, materialized_tick, delivered_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (owner, item_ref, score, now, now),
            )
            results.append(
                {
                    "owner_agent_id": owner,
                    "feed_item_id": int(cur.lastrowid),
                    "item_ref": item_ref,
                    "score": score,
                    "unread_count": self.unread_count(owner),
                }
            )
        self._conn.commit()
        return results

    # ------------------------------------------------------------------
    # inbox observation & read state
    # ------------------------------------------------------------------
    def inbox(
        self,
        agent_id: Any,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Return an agent's feed ordered pinned > unread > recency.

        "Pinned" is detected from the underlying entity's ``is_pinned`` /
        ``pinned`` attribute when ``item_ref`` is of the form
        ``EntityType:entity_id``; unresolvable refs are treated unpinned.
        """
        owner = entity_key(agent_id)
        rows = self._conn.execute(
            "SELECT * FROM feed_items WHERE owner_agent_id = ?",
            (owner,),
        ).fetchall()
        items = [self._row_to_feed_item(r) for r in rows]
        for it in items:
            it["pinned"] = self._is_pinned(it["item_ref"])
        items.sort(
            key=lambda it: (
                0 if it["pinned"] else 1,      # pinned first
                1 if it["read_at"] is not None else 0,  # unread before read
                -(it["materialized_tick"] or 0),        # recency desc
                -(it["feed_item_id"] or 0),
            )
        )
        return items[:limit] if limit else items

    def unread_count(self, agent_id: Any) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM feed_items "
            "WHERE owner_agent_id = ? AND read_at IS NULL",
            (entity_key(agent_id),),
        ).fetchone()
        return int(row["n"])

    def mark_read(
        self,
        agent_id: Any,
        feed_item_id: Optional[int] = None,
        item_ref: Optional[str] = None,
        up_to_tick: Optional[int] = None,
    ) -> int:
        """Mark feed items read. With no selector, marks the agent's whole inbox."""
        owner = entity_key(agent_id)
        now = self.tick()
        sql = (
            "UPDATE feed_items SET read_at = ? "
            "WHERE owner_agent_id = ? AND read_at IS NULL"
        )
        params: list[Any] = [now, owner]
        if feed_item_id is not None:
            sql += " AND feed_item_id = ?"
            params.append(feed_item_id)
        if item_ref is not None:
            sql += " AND item_ref = ?"
            params.append(str(item_ref))
        if up_to_tick is not None:
            sql += " AND materialized_tick <= ?"
            params.append(int(up_to_tick))
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return int(cur.rowcount)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _is_pinned(self, item_ref: str) -> bool:
        """Best-effort pin detection: ``EntityType:entity_id`` → entity attrs."""
        if ":" not in item_ref:
            return False
        etype, _, eid = item_ref.partition(":")
        ent = self.get_entity(etype, eid)
        if not ent:
            return False
        data = ent.get("data") or {}
        return bool(data.get("is_pinned") or data.get("pinned"))

    @staticmethod
    def _row_to_feed_item(row: sqlite3.Row) -> dict:
        return {
            "feed_item_id": row["feed_item_id"],
            "owner_agent_id": row["owner_agent_id"],
            "item_ref": row["item_ref"],
            "score": row["score"],
            "materialized_tick": row["materialized_tick"],
            "read_at": row["read_at"],
            "delivered_at": row["delivered_at"],
        }


__all__ = ["EntityStore", "entity_key", "Clock"]
