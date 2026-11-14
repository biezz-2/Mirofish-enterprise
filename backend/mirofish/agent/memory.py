"""Memory engine for MiroFish agents.

Hybrid of Generative Agents memory streams (Park et al. 2023) and a
temporal knowledge graph with validity intervals (paper §12).

Design notes:
- Pure stdlib + optional numpy (numpy is *not* required; similarity and
  retrieval are implemented with plain Python so the module works without
  third-party packages). All randomness is seeded via ``random.Random``.
- ``MemoryStream`` is append-only. Retrieval score:
      score(m, q, t) = alpha * exp(-(t - t_m) / tau)
                     + beta  * importance(m)
                     + gamma * sim(m, q)
- ``Reflection`` records are generated automatically when the
  recency-weighted mass of a stream exceeds ``theta_R``.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class RecordType(str, Enum):
    OBSERVATION = "observation"
    UTTERANCE = "utterance"
    REFLECTION = "reflection"


class EdgeKind(str, Enum):
    INTERACT = "INTERACT"      # agent <-> agent / agent <-> content
    EXPOSED = "EXPOSED"        # agent was exposed to content/topic
    ASSERTS = "ASSERTS"        # agent asserts a claim/topic relation


class Provenance(str, Enum):
    OBSERVED = "observed"      # edge derived from real simulation events
    GENERATED = "generated"    # edge produced by reflection/inference


@dataclass(slots=True)
class MemoryRecord:
    """A single append-only memory entry."""

    type: RecordType
    content: str
    timestamp_tick: int
    importance: float = 0.5
    embedding_id: str | None = None
    provenance: Provenance = Provenance.OBSERVED
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            self.type = RecordType(self.type)
        if isinstance(self.provenance, str):
            self.provenance = Provenance(self.provenance)
        self.importance = max(0.0, min(1.0, float(self.importance)))


# ---------------------------------------------------------------------------
# Similarity functions (injectable)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def token_overlap_cosine(a: str, b: str) -> float:
    """Cosine similarity over token-count vectors. No external deps."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    from collections import Counter

    ca, cb = Counter(ta), Counter(tb)
    dot = sum(v * cb.get(k, 0) for k, v in ca.items())
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# Type alias: similarity(query, record) -> float in [0, 1]-ish
SimilarityFn = Callable[[str, MemoryRecord], float]


def default_similarity(query: str, record: MemoryRecord) -> float:
    return token_overlap_cosine(query, record.content)


# ---------------------------------------------------------------------------
# MemoryStream
# ---------------------------------------------------------------------------


@dataclass
class MemoryStream:
    """Append-only per-agent memory stream with recency/importance/relevance
    retrieval and automatic reflection generation."""

    agent_id: str
    alpha: float = 1.0          # recency weight
    beta: float = 1.0           # importance weight
    gamma: float = 1.0          # relevance weight
    tau: float = 50.0           # recency decay constant (ticks)
    theta_r: float = 10.0       # reflection trigger: recency-weighted mass
    reflect_window: int = 20    # records considered for a reflection
    similarity: SimilarityFn = default_similarity
    records: list[MemoryRecord] = field(default_factory=list)
    _since_reflection_mass: float = 0.0

    # -- append -----------------------------------------------------------

    def add(
        self,
        record_type: RecordType | str,
        content: str,
        timestamp_tick: int,
        importance: float = 0.5,
        embedding_id: str | None = None,
        provenance: Provenance | str = Provenance.OBSERVED,
        meta: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        rec = MemoryRecord(
            type=RecordType(record_type),
            content=content,
            timestamp_tick=int(timestamp_tick),
            importance=float(importance),
            embedding_id=embedding_id,
            provenance=Provenance(provenance),
            meta=dict(meta or {}),
        )
        self.records.append(rec)
        # Recency-weighted mass accumulated since last reflection.
        self._since_reflection_mass += rec.importance * self._recency(
            rec.timestamp_tick, rec.timestamp_tick)
        self._maybe_reflect(rec.timestamp_tick)
        return rec

    def add_observation(self, content: str, tick: int, **kw: Any) -> MemoryRecord:
        return self.add(RecordType.OBSERVATION, content, tick, **kw)

    def add_utterance(self, content: str, tick: int, **kw: Any) -> MemoryRecord:
        return self.add(RecordType.UTTERANCE, content, tick, **kw)

    # -- retrieval --------------------------------------------------------

    def _recency(self, t_m: int, t: int) -> float:
        """exp(-(t - t_m)/tau); t_m in the future decays as exp(negative)."""
        return math.exp(-(t - t_m) / self.tau) if self.tau > 0 else 1.0

    def score(self, record: MemoryRecord, query: str, at_tick: int) -> float:
        return (
            self.alpha * self._recency(record.timestamp_tick, at_tick)
            + self.beta * record.importance
            + self.gamma * self.similarity(query, record)
        )

    def retrieve(
        self,
        query: str,
        at_tick: int,
        k: int = 10,
        min_score: float = -math.inf,
        record_types: Iterable[RecordType | str] | None = None,
    ) -> list[tuple[float, MemoryRecord]]:
        """Top-k records by hybrid score, most recent tiebreak."""
        wanted = {RecordType(t) for t in record_types} if record_types else None
        scored = [
            (self.score(r, query, at_tick), r)
            for r in self.records
            if wanted is None or r.type in wanted
        ]
        scored = [(s, r) for s, r in scored if s >= min_score]
        scored.sort(key=lambda sr: (sr[0], sr[1].timestamp_tick), reverse=True)
        return scored[:k]

    def recent(self, n: int = 10, at_tick: int | None = None) -> list[MemoryRecord]:
        """Most recent n records, optionally weighted by recency at ``at_tick``."""
        if at_tick is None:
            return self.records[-n:]
        return [r for _, r in sorted(
            ((self._recency(r.timestamp_tick, at_tick), r) for r in self.records),
            key=lambda x: x[0], reverse=True,
        )[:n]]

    # -- reflection -------------------------------------------------------

    def _maybe_reflect(self, tick: int) -> MemoryRecord | None:
        if self._since_reflection_mass < self.theta_r:
            return None
        window = self.records[-self.reflect_window:]
        # Importance-weighted centroid content: top terms by frequency.
        freq: dict[str, int] = {}
        for r in window:
            w = 1.0 + r.importance
            for tok in set(_tokens(r.content)):
                freq[tok] = freq.get(tok, 0) + w
        top = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:12]
        summary = (
            f"Reflection over {len(window)} recent memories "
            f"(mass={self._since_reflection_mass:.1f}): "
            + ", ".join(t for t, _ in top)
        )
        rec = MemoryRecord(
            type=RecordType.REFLECTION,
            content=summary,
            timestamp_tick=tick,
            importance=min(1.0, 0.5 + self._since_reflection_mass / (4 * self.theta_r)),
            provenance=Provenance.GENERATED,
            meta={"mass": self._since_reflection_mass, "window": len(window)},
        )
        self.records.append(rec)
        self._since_reflection_mass = 0.0
        return rec

    @property
    def mass(self) -> float:
        return self._since_reflection_mass

    def __len__(self) -> int:
        return len(self.records)


# ---------------------------------------------------------------------------
# TemporalKG
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class KGNode:
    node_id: str
    kind: str  # agent | topic | content | event
    label: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KGEdge:
    src: str
    dst: str
    kind: EdgeKind
    t_start: int
    t_end: int | None = None          # None = still valid (open interval)
    provenance: Provenance = Provenance.OBSERVED
    weight: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return self.t_end is None

    def active_at(self, tick: int) -> bool:
        """Validity interval is [t_start, t_end)."""
        if tick < self.t_start:
            return False
        return self.t_end is None or tick < self.t_end


class TemporalKG:
    """Temporal knowledge graph.

    Nodes: agent, topic, content, event.
    Edges: INTERACT, EXPOSED, ASSERTS with validity intervals [t_start, t_end).
    ``add_edge`` auto-invalidates a superseded edge of the same
    (src, dst, kind) triple by closing its interval at the new t_start.
    Every edge carries a provenance tag (observed vs generated).
    """

    def __init__(self) -> None:
        self.nodes: dict[str, KGNode] = {}
        self.edges: list[KGEdge] = []
        # index: (src, dst, kind) -> list of edge indices (history preserved)
        self._by_triple: dict[tuple[str, str, EdgeKind], list[int]] = {}

    # -- nodes ------------------------------------------------------------

    def add_node(self, node_id: str, kind: str, label: str = "",
                 meta: dict[str, Any] | None = None) -> KGNode:
        node = KGNode(node_id=node_id, kind=kind, label=label or node_id,
                      meta=dict(meta or {}))
        self.nodes[node_id] = node
        return node

    def node(self, node_id: str) -> KGNode | None:
        return self.nodes.get(node_id)

    # -- edges ------------------------------------------------------------

    def add_edge(
        self,
        src: str,
        dst: str,
        kind: EdgeKind | str,
        t_start: int,
        t_end: int | None = None,
        provenance: Provenance | str = Provenance.OBSERVED,
        weight: float = 1.0,
        meta: dict[str, Any] | None = None,
        supersede: bool = True,
    ) -> KGEdge:
        """Add an edge; optionally close the currently-valid edge on the same
        (src, dst, kind) triple at ``t_start`` (supersession)."""
        kind = EdgeKind(kind)
        prov = Provenance(provenance)
        if supersede:
            for idx in self._by_triple.get((src, dst, kind), []):
                e = self.edges[idx]
                if e.valid and e.t_start <= t_start:
                    e.t_end = t_start
        edge = KGEdge(
            src=src, dst=dst, kind=kind, t_start=int(t_start),
            t_end=None if t_end is None else int(t_end),
            provenance=prov, weight=float(weight), meta=dict(meta or {}),
        )
        idx = len(self.edges)
        self.edges.append(edge)
        self._by_triple.setdefault((src, dst, kind), []).append(idx)
        # Ensure endpoint nodes exist (default kind guessed).
        self.nodes.setdefault(src, KGNode(src, "agent" if src.startswith("agent:") else "entity"))
        self.nodes.setdefault(dst, KGNode(dst, "topic" if dst.startswith("topic:") else "entity"))
        return edge

    # -- queries ----------------------------------------------------------

    def query(
        self,
        pattern: dict[str, Any],
        at_tick: int | None = None,
        provenance: Provenance | str | None = None,
    ) -> list[KGEdge]:
        """Filter edges by attributes and optional temporal validity.

        ``pattern`` keys may include: src, dst, kind, weight (exact match or
        callable), plus any ``meta`` key. ``at_tick`` keeps only edges whose
        validity interval contains the tick ([t_start, t_end)).
        """
        prov = Provenance(provenance) if provenance is not None else None
        out: list[KGEdge] = []
        for e in self.edges:
            if at_tick is not None and not e.active_at(at_tick):
                continue
            if prov is not None and e.provenance is not prov:
                continue
            ok = True
            for key, want in pattern.items():
                if key == "kind":
                    got: Any = e.kind.value if isinstance(e.kind, EdgeKind) else e.kind
                    want_v = want.value if isinstance(want, EdgeKind) else want
                    if got != want_v:
                        ok = False
                        break
                    continue
                got = getattr(e, key, None)
                if got is None and key in e.meta:
                    got = e.meta[key]
                if callable(want):
                    if not want(got):
                        ok = False
                        break
                elif got != want:
                    ok = False
                    break
            if ok:
                out.append(e)
        return out

    def neighbors(self, node_id: str, at_tick: int | None = None,
                  direction: str = "both") -> list[tuple[KGEdge, str]]:
        """Edges incident to ``node_id``; returns (edge, other_node_id)."""
        res: list[tuple[KGEdge, str]] = []
        for e in self.edges:
            if at_tick is not None and not e.active_at(at_tick):
                continue
            if direction in ("out", "both") and e.src == node_id:
                res.append((e, e.dst))
            if direction in ("in", "both") and e.dst == node_id:
                res.append((e, e.src))
        return res

    def timeline(self, src: str | None = None, dst: str | None = None,
                 kind: EdgeKind | str | None = None) -> list[KGEdge]:
        """All edges (including closed ones) sorted by t_start."""
        return sorted(
            (e for e in self.edges
             if (src is None or e.src == src)
             and (dst is None or e.dst == dst)
             and (kind is None or e.kind == EdgeKind(kind))),
            key=lambda e: (e.t_start, e.t_end or math.inf),
        )


# ---------------------------------------------------------------------------
# MemoryStore
# ---------------------------------------------------------------------------


class MemoryStore:
    """Ties per-agent :class:`MemoryStream`\\ s to a global :class:`TemporalKG`.

    Convenience helpers record observations/utterances into both the agent's
    stream and the KG (as EXPOSED/INTERACT/ASSERTS edges) so that memory and
    graph stay consistent.
    """

    def __init__(
        self,
        stream_kwargs: dict[str, Any] | None = None,
        kg: TemporalKG | None = None,
    ) -> None:
        self.streams: dict[str, MemoryStream] = {}
        self.kg = kg or TemporalKG()
        self._stream_kwargs = dict(stream_kwargs or {})

    # -- streams ----------------------------------------------------------

    def stream(self, agent_id: str) -> MemoryStream:
        if agent_id not in self.streams:
            self.streams[agent_id] = MemoryStream(agent_id=agent_id,
                                                  **self._stream_kwargs)
            self.kg.add_node(f"agent:{agent_id}", "agent", label=agent_id)
        return self.streams[agent_id]

    def add_observation(self, agent_id: str, content: str, tick: int,
                        importance: float = 0.5, **kw: Any) -> MemoryRecord:
        rec = self.stream(agent_id).add_observation(
            content, tick, importance=importance, **kw)
        # Mirror high-importance observations into the KG as EXPOSED edges
        # against an auto topic node derived from the first tokens.
        if rec.importance >= 0.7:
            topic = " ".join(_tokens(content)[:3]) or "general"
            self.kg.add_edge(f"agent:{agent_id}", f"topic:{topic}",
                             EdgeKind.EXPOSED, tick,
                             provenance=rec.provenance)
        return rec

    def add_utterance(self, agent_id: str, content: str, tick: int,
                      target_id: str | None = None,
                      importance: float = 0.5, **kw: Any) -> MemoryRecord:
        rec = self.stream(agent_id).add_utterance(
            content, tick, importance=importance, **kw)
        if target_id is not None:
            self.kg.add_edge(f"agent:{agent_id}", f"agent:{target_id}",
                             EdgeKind.INTERACT, tick, weight=rec.importance,
                             provenance=rec.provenance)
        return rec

    def add_reflection_hint(self, agent_id: str, content: str, tick: int,
                            topic: str, **kw: Any) -> MemoryRecord:
        """Record a generated (inferred) assertion into stream + KG."""
        rec = self.stream(agent_id).add(
            RecordType.REFLECTION, content, tick,
            provenance=Provenance.GENERATED, **kw)
        self.kg.add_edge(f"agent:{agent_id}", f"topic:{topic}",
                         EdgeKind.ASSERTS, tick,
                         provenance=Provenance.GENERATED)
        return rec

    # -- queries ----------------------------------------------------------

    def recall(self, agent_id: str, query: str, at_tick: int, k: int = 10
               ) -> list[tuple[float, MemoryRecord]]:
        return self.stream(agent_id).retrieve(query, at_tick, k=k)

    def kg_query(self, pattern: dict[str, Any], at_tick: int | None = None,
                 provenance: Provenance | str | None = None
                 ) -> list[KGEdge]:
        return self.kg.query(pattern, at_tick=at_tick, provenance=provenance)

    def agents(self) -> list[str]:
        return sorted(s.agent_id for s in self.streams.values())
