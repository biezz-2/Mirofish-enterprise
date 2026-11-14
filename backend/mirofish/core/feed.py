"""Feed scoring layer — paper §6 model over PlatformSpec ``feed`` sections.

Pipeline: ``materialize_feed(spec, candidates, agent_ctx)`` resolves the
scorer plugin declared in ``feed.scorer.plugin`` (see ``PLUGIN_REGISTRY``),
canonicalizes each candidate's raw signals through the ``g_k`` family
canonicalizers, applies the observation mask, scores, and returns top-k.

Conventions (docs/SPEC_SCHEMA.md):
- The ten canonical signal families live in ``SIGNAL_FAMILIES``.
- Signals a platform does not expose are omitted from ``signal_schema``;
  per-item they are expressed via ``SignalVector.mask`` (masked signals
  contribute 0 and are renormalized out of the weight mass).
- ``feed.kind == "push"`` specs must NOT declare a scorer plugin; push
  delivery is handled by ``feed.delivery_model.inbox_rules`` at write time.
"""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Iterable, Mapping, Sequence

# ---------------------------------------------------------------------------
# Canonical signal families (paper §6.1 / SPEC_SCHEMA.md)
# ---------------------------------------------------------------------------

SIGNAL_FAMILIES: tuple[str, ...] = (
    "recency",
    "engagement_count",
    "attention_dwell",
    "shares_private",
    "author_affinity",
    "topic_graph",
    "negative_feedback",
    "popularity_velocity",
    "content_type_prior",
    "quality_satisfaction",
)


class FeedSpecError(ValueError):
    """Raised when a feed spec or scorer plugin cannot be resolved."""


# ---------------------------------------------------------------------------
# SignalVector — dict-like container with observation mask + item metadata
# ---------------------------------------------------------------------------


class SignalVector(dict):
    """Raw per-item signal values plus an observation mask.

    ``mask`` maps signal family -> bool (True = observed).  A family that is
    masked-out, or whose value is ``None``, is treated as unobserved: it
    contributes 0 to the weighted sum and its |weight| is removed from the
    renormalization mass.

    ``meta`` carries item-level context that is not itself a scored signal:
    ``timestamp``, ``author``/``author_id``, ``author_followers``,
    ``out_of_network``, ``is_trending``, ``graph_proximity``, ``item_duration``,
    ``item_id``.
    """

    def __init__(
        self,
        values: Mapping[str, Any] | None = None,
        *,
        mask: Mapping[str, bool] | None = None,
        meta: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(values or {})
        self.mask: dict[str, bool] = dict(mask or {})
        self.meta: dict[str, Any] = dict(meta or {})

    # -- mask semantics -----------------------------------------------------

    def observed(self, name: str) -> bool:
        """True iff ``name`` is observable for this item."""
        if name in self.mask:
            return bool(self.mask[name])
        return self.get(name) is not None

    def observed_items(self) -> Iterable[tuple[str, Any]]:
        for name, value in self.items():
            if self.observed(name):
                yield name, value

    def masked_view(self) -> dict[str, Any]:
        """Plain dict with unobserved families zeroed (SPEC mask semantics)."""
        return {k: (v if self.observed(k) else 0.0) for k, v in self.items()}


# ---------------------------------------------------------------------------
# Canonicalizers g_k
# ---------------------------------------------------------------------------


def recency_decay(age: float | None, half_life: float) -> float:
    """Exponential decay in [0, 1]; ``age`` in the same unit as ``half_life``.

    ``age=None`` -> 0.0 (no recency signal).  Fresh items (age <= 0) -> 1.0.
    """
    if age is None:
        return 0.0
    if half_life <= 0:
        return 1.0 if age <= 0 else 0.0
    if age <= 0:
        return 1.0
    return math.pow(2.0, -age / half_life)


def zscore_rate(x: float | None, mean: float | None, std: float | None) -> float:
    """Per-agent rate normalization: ``(x - mean) / std``.

    Returns 0.0 when ``x`` is missing or ``std`` is degenerate (<= 0), so a
    platform with no rate variance contributes no signal rather than noise.
    """
    if x is None or mean is None or std is None or std <= 0:
        return 0.0
    return (float(x) - float(mean)) / float(std)


def dwell_fraction(
    dwell: float | None,
    item_duration: float | None,
    skip_threshold: float = 0.0,
) -> float:
    """Attention dwell as a fraction of item duration, clipped to [0, 1].

    ``skip_threshold`` (also a fraction of duration) zeroes out skims/cuts.
    """
    if dwell is None or item_duration is None or item_duration <= 0:
        return 0.0
    if dwell < skip_threshold * item_duration:
        return 0.0
    return min(max(dwell / item_duration, 0.0), 1.0)


def identity(x: Any) -> float:
    """Pass-through canonicalizer: bools -> 1.0/0.0, numerics -> float."""
    if x is None:
        return 0.0
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


# Default g_k per canonical family; custom families always use ``identity``.
DEFAULT_CANONICALIZERS: dict[str, str] = {
    "recency": "recency",
    "engagement_count": "zscore_rate",
    "attention_dwell": "dwell_fraction",
}

_CANON_FN: dict[str, Callable[..., float]] = {
    "recency": recency_decay,
    "zscore_rate": zscore_rate,
    "dwell_fraction": dwell_fraction,
    "identity": identity,
}


def _canonicalize(name: str, value: Any, ctx: Mapping[str, Any]) -> float:
    """Dispatch one raw signal value through its family canonicalizer."""
    if value is None:
        return 0.0
    params = ctx.get("params") or {}
    canon_name = (params.get("canonicalizers") or {}).get(name) or DEFAULT_CANONICALIZERS.get(
        name, "identity"
    )
    if canon_name == "identity":
        return identity(value)
    if canon_name == "recency":
        raw = identity(value)
        now = ctx.get("now")
        # Heuristic: values > ~2001-09-09 in seconds are epoch timestamps.
        if now is not None and raw > 1e9:
            raw = max(now - raw, 0.0)
        half_life = float(
            params.get("recency_half_life", params.get("half_life", 7.0 * 86400.0))
        )
        return recency_decay(raw, half_life)
    if canon_name == "zscore_rate":
        stats = _signal_stats(ctx).get(name) or {}
        return zscore_rate(identity(value), stats.get("mean"), stats.get("std"))
    if canon_name == "dwell_fraction":
        meta = ctx.get("meta") or {}
        duration = meta.get("item_duration") or params.get("item_duration")
        skip = float(params.get("dwell_skip_fraction", params.get("skip_threshold", 0.0)))
        return dwell_fraction(identity(value), duration, skip)
    raise FeedSpecError(f"unknown canonicalizer {canon_name!r} for signal {name!r}")


def _signal_stats(ctx: Mapping[str, Any]) -> dict[str, Any]:
    """Per-agent rate stats: ``agent_ctx['signal_stats'][family] = {mean,std}``."""
    agent_ctx = ctx.get("agent_ctx")
    if isinstance(agent_ctx, Mapping):
        stats = agent_ctx.get("signal_stats") or agent_ctx.get("rate_stats") or {}
        if isinstance(stats, Mapping):
            return dict(stats)
    stats = ctx.get("signal_stats")
    return dict(stats) if isinstance(stats, Mapping) else {}


# ---------------------------------------------------------------------------
# FeedScorer protocol
# ---------------------------------------------------------------------------


class FeedScorer(ABC):
    """Scores one candidate item.  ``score`` returns a float (higher = better).

    Scorers are stateful across a single feed materialization (e.g. author
    diversity counters); ``materialize_feed`` calls :meth:`reset` per call.
    """

    name: ClassVar[str] = "base"

    def __init__(
        self,
        params: Mapping[str, Any] | None = None,
        agent_ctx: Any = None,
        rng: random.Random | None = None,
    ) -> None:
        self.params: dict[str, Any] = dict(params or {})
        self.agent_ctx = agent_ctx
        self.rng = rng if rng is not None else random.Random()

    def reset(self) -> None:
        """Clear per-feed state.  Called by ``materialize_feed`` per request."""

    @abstractmethod
    def score(self, item_signals: SignalVector, agent_ctx: Any, params: Mapping[str, Any]) -> float:
        """Score one item.  ``params`` is the fully merged scorer/feed param dict."""


# ---------------------------------------------------------------------------
# Built-in scorers
# ---------------------------------------------------------------------------


class ChronologicalScorer(FeedScorer):
    """Orders purely by timestamp desc — Mastodon/Following-style feeds."""

    name = "chronological"

    def score(self, item_signals: SignalVector, agent_ctx: Any, params: Mapping[str, Any]) -> float:
        return float(item_signals.meta.get("timestamp") or 0.0)


class EngagementRankedScorer(FeedScorer):
    """Generic ``sum_k w_k * g_k(x_k)`` over the signal schema, renormalized
    over observed families only, plus multiplicative platform adjustments:

    - ``author_diversity_decay`` / ``max_posts_per_author`` — down-weight or
      suppress repeat authors within one materialized feed.
    - ``oon_discount`` / ``out_of_network_discount`` — multiplicative penalty
      for out-of-network candidates.
    - ``new_author_boost`` — multiplicative boost for small/new authors.
    - ``negative_feedback`` — passthrough: its (typically negative) schema
      weight applies directly via ``identity`` canonicalization.
    - ``score_jitter`` — optional uniform noise half-width (uses ``self.rng``).
    """

    name = "engagement_ranked"

    def reset(self) -> None:
        self._author_counts: dict[tuple[str, str], int] = {}

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _author_key(agent_ctx: Any, signals: SignalVector) -> tuple[str, str]:
        agent_id = "default"
        if isinstance(agent_ctx, Mapping):
            agent_id = str(agent_ctx.get("agent_id") or agent_ctx.get("agent") or agent_id)
        author = signals.meta.get("author") or signals.meta.get("author_id")
        if author is None:
            author = signals.get("author") or signals.get("author_id") or "unknown"
        return (agent_id, str(author))

    def _weighted_sum(self, signals: SignalVector, agent_ctx: Any, params: Mapping[str, Any]) -> float:
        weights = params.get("weights") or self.params.get("weights") or {}
        if not isinstance(weights, Mapping):
            return 0.0
        num = 0.0
        den = 0.0
        ctx = {
            "params": params,
            "agent_ctx": agent_ctx,
            "now": params.get("now"),
            "meta": signals.meta,
        }
        for name, w in weights.items():
            if not signals.observed(name):
                continue  # masked/unobserved: contributes 0, weight renormalized out
            try:
                w = float(w)
            except (TypeError, ValueError):
                continue
            num += w * _canonicalize(name, signals.get(name), ctx)
            den += abs(w)
        return num / den if den > 0 else 0.0

    # -- scoring ------------------------------------------------------------

    def score(self, item_signals: SignalVector, agent_ctx: Any, params: Mapping[str, Any]) -> float:
        p = {**self.params, **dict(params)}
        score = self._weighted_sum(item_signals, agent_ctx, p)

        # --- multiplicative adjustments ------------------------------------
        author_key = self._author_key(agent_ctx, item_signals)
        diversity_on = bool(
            p.get("author_diversity_decay") or p.get("max_posts_per_author") or p.get("author_diversity_cap")
        )
        if diversity_on:
            count = self._author_counts.get(author_key, 0)
            self._author_counts[author_key] = count + 1
            max_per = p.get("max_posts_per_author") or p.get("author_diversity_cap")
            decay = float(p.get("author_diversity_decay_factor", p.get("author_decay", 0.5)))
            if max_per is not None and count >= int(max_per):
                score *= float(p.get("over_cap_factor", 0.0))
            elif count > 0:
                score *= decay**count

        if item_signals.meta.get("out_of_network"):
            score *= float(p.get("oon_discount", p.get("out_of_network_discount", 1.0)))

        boost = float(p.get("new_author_boost", 1.0))
        if boost != 1.0:
            followers = item_signals.meta.get("author_followers")
            if followers is None:
                followers = item_signals.get("author_followers")
            threshold = float(p.get("new_author_max_followers", 1000))
            if followers is not None and float(followers) <= threshold:
                score *= boost

        jitter = float(p.get("score_jitter", 0.0))
        if jitter > 0:
            score += self.rng.uniform(-jitter, jitter)
        return score

    # -- batch convenience (used by tests / simple callers) -----------------

    def score_and_rank(
        self,
        items: Sequence[Any],
        weights: Mapping[str, float] | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        """Score raw candidate items and return them sorted by score desc."""
        self.reset()
        params = dict(self.params)
        if weights is not None:
            params["weights"] = dict(weights)
        params.update(kwargs)
        scored = [
            (self.score(_item_to_signal_vector(it), self.agent_ctx, params), _item_ts(it), i, it)
            for i, it in enumerate(items)
        ]
        scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
        return [t[3] for t in scored]

    def __call__(self, items: Sequence[Any], weights: Mapping[str, float] | None = None, **kw: Any) -> list[Any]:
        return self.score_and_rank(items, weights=weights, **kw)


class PushInboxScorer(FeedScorer):
    """NOT a scorer — push feeds have no ranking step.

    Registering/instantiating this plugin raises :class:`FeedSpecError`: a
    ``feed.kind == "push"`` spec must omit ``feed.scorer`` entirely and rely on
    ``feed.delivery_model.inbox_rules`` for inbox ordering.
    """

    name = "push_inbox"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FeedSpecError(
            "push_inbox is not a scorer: push feeds (delivery_mode=push) must not "
            "declare feed.scorer.plugin; ordering lives in feed.delivery_model.inbox_rules"
        )

    def score(self, item_signals: SignalVector, agent_ctx: Any, params: Mapping[str, Any]) -> float:
        raise FeedSpecError("push_inbox cannot score items")  # pragma: no cover


class BlueskyDiscoverScorer(FeedScorer):
    """Placeholder Discover blend: trending + graph_proximity + engagement.

    ``score = w_engagement*g(engagement) + w_trending*trending
           + w_graph_proximity*proximity`` where weights come from
    ``params['weights']`` (keys ``engagement``, ``trending``,
    ``graph_proximity``) or flat ``*_weight`` params; defaults are
    ``{engagement: 0.5, trending: 0.3, graph_proximity: 0.2}``.

    ``graph_proximity`` raw values > 1 are treated as hop distance and mapped
    to ``1/(1+hops)``; values in [0, 1] are used directly.
    """

    name = "bluesky_discover"

    _DEFAULT_WEIGHTS: ClassVar[dict[str, float]] = {
        "engagement": 0.5,
        "trending": 0.3,
        "graph_proximity": 0.2,
    }

    def _weights(self, params: Mapping[str, Any]) -> dict[str, float]:
        w = dict(self._DEFAULT_WEIGHTS)
        nested = params.get("weights")
        if isinstance(nested, Mapping):
            for k in w:
                if k in nested:
                    w[k] = float(nested[k])
        for k in w:
            flat = params.get(f"{k}_weight") or params.get(f"w_{k}")
            if flat is not None:
                w[k] = float(flat)
        return w

    @staticmethod
    def _proximity(value: Any) -> float:
        if value is None or value is False:
            return 0.0
        if value is True:
            return 1.0
        v = identity(value)
        if v <= 1.0:
            return max(v, 0.0)
        return 1.0 / (1.0 + v)  # interpret as hop distance

    def score(self, item_signals: SignalVector, agent_ctx: Any, params: Mapping[str, Any]) -> float:
        p = {**self.params, **dict(params)}
        w = self._weights(p)
        ctx = {"params": p, "agent_ctx": agent_ctx, "now": p.get("now"), "meta": item_signals.meta}

        eng_raw = item_signals.get("engagement_count")
        if eng_raw is None:
            eng_raw = item_signals.get("engagement")
        engagement = _canonicalize("engagement_count", eng_raw, ctx) if eng_raw is not None else 0.0

        trending_raw = item_signals.get("trending_score")
        if trending_raw is None:
            trending_raw = 1.0 if item_signals.meta.get("is_trending") else item_signals.get("is_trending")
        trending = identity(trending_raw)

        prox_raw = item_signals.get("graph_proximity")
        if prox_raw is None:
            prox_raw = item_signals.meta.get("graph_proximity")
        proximity = self._proximity(prox_raw)

        return w["engagement"] * engagement + w["trending"] * trending + w["graph_proximity"] * proximity


# ---------------------------------------------------------------------------
# Plugin registry — platform plugins register via register_scorer_plugin()
# ---------------------------------------------------------------------------

PLUGIN_REGISTRY: dict[str, type[FeedScorer] | Callable[..., FeedScorer]] = {
    "chronological": ChronologicalScorer,
    "engagement_ranked": EngagementRankedScorer,
    "push_inbox": PushInboxScorer,  # raises on instantiation by design
    "bluesky_discover": BlueskyDiscoverScorer,
}


def register_scorer_plugin(name: str, factory: type[FeedScorer] | Callable[..., FeedScorer]) -> None:
    """Register a platform scorer plugin under ``name`` (or ``plugin:<name>``)."""
    PLUGIN_REGISTRY[name.removeprefix("plugin:")] = factory


def _resolve_plugin(
    name: str | None,
    kind: str,
    registry: Mapping[str, Any] | None = None,
) -> type[FeedScorer] | Callable[..., FeedScorer]:
    """Resolve a scorer plugin name to a registry entry.

    Accepts ``chronological``, ``plugin:chronological``, ``custom:phoenix``
    (tries ``custom:phoenix`` -> ``phoenix`` -> ``custom``).  Falls back to a
    kind-based default when ``name`` is None.
    """
    if name is None:
        name = {
            "chronological": "chronological",
            "discover": "bluesky_discover",
            "push": "push_inbox",
        }.get(kind, "engagement_ranked")
    candidates = [name]
    if name.startswith("plugin:"):
        candidates.insert(0, name.removeprefix("plugin:"))
    if ":" in name:
        candidates.append(name.split(":")[-1])
        candidates.append(name.split(":")[0])
    reg = registry if registry is not None else PLUGIN_REGISTRY
    for cand in candidates:
        if cand in reg:
            return reg[cand]
    raise FeedSpecError(
        f"unknown feed scorer plugin {name!r}; registered: {sorted(reg)}. "
        "Platform plugins must call register_scorer_plugin() first."
    )


# ---------------------------------------------------------------------------
# Item <-> SignalVector adapters + spec accessors (dict or pydantic model)
# ---------------------------------------------------------------------------

_META_KEYS = {
    "signals", "timestamp", "created_at", "ts", "published_at",
    "author", "author_id", "author_followers", "follower_count",
    "out_of_network", "in_network", "observation_mask", "mask",
    "item", "item_id", "id", "duration", "item_duration",
    "is_trending", "trending", "graph_proximity",
}


def _is_mapping(x: Any) -> bool:
    return isinstance(x, Mapping)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Duck-typed accessor: Mapping key or attribute (pydantic/dict/spec)."""
    if obj is None:
        return default
    if _is_mapping(obj):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _item_mapping(item: Any) -> Mapping[str, Any]:
    if _is_mapping(item):
        return item
    dump = getattr(item, "model_dump", None)
    if callable(dump):
        try:
            return dump()
        except Exception:
            pass
    if hasattr(item, "__dict__"):
        return vars(item)
    raise TypeError(f"unsupported feed item type: {type(item)!r}")


def _item_ts(item: Any) -> float:
    d = _item_mapping(item)
    for key in ("timestamp", "created_at", "ts", "published_at"):
        v = d.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return 0.0


def _item_to_signal_vector(item: Any) -> SignalVector:
    """Extract a SignalVector from a candidate item.

    Contract: ``item['signals']`` (mapping) holds raw family values; missing
    -> all non-reserved top-level keys are treated as signals.  Item-level
    ``observation_mask`` (or ``mask``) overrides per-family observability.
    """
    d = _item_mapping(item)
    raw_signals = d.get("signals")
    if _is_mapping(raw_signals):
        sig = dict(raw_signals)
    else:
        sig = {k: v for k, v in d.items() if k not in _META_KEYS}

    meta: dict[str, Any] = {}
    for key in ("item_id", "id", "author", "author_id", "author_followers",
                "follower_count", "out_of_network", "in_network", "is_trending",
                "trending", "graph_proximity", "item_duration", "duration"):
        if d.get(key) is not None:
            meta[key] = d[key]
    ts = _item_ts(item)
    if ts:
        meta["timestamp"] = ts

    mask_raw = d.get("observation_mask") or d.get("mask")
    mask: dict[str, bool] = {}
    if _is_mapping(mask_raw):
        mask = {str(k): bool(v) for k, v in mask_raw.items()}

    return SignalVector(sig, mask=mask, meta=meta)


def _feed_section(spec: Any) -> Mapping[str, Any]:
    feed = _get(spec, "feed")
    if feed is None and (_is_mapping(spec) and "signal_schema" in spec or _get(spec, "kind")):
        feed = spec  # spec IS the feed section
    if feed is None:
        raise FeedSpecError("spec has no 'feed' section")
    return feed


def _build_weights(feed: Any, scorer_params: Mapping[str, Any], feed_params: Mapping[str, Any]) -> dict[str, float]:
    """Merge signal_schema weights with scorer/feed param overrides."""
    weights: dict[str, float] = {}
    schema = _get(feed, "signal_schema") or []
    for sig in schema:
        name = _get(sig, "name")
        w = _get(sig, "weight")
        if name is None or w is None:
            continue  # weight: null => ordering-only signal, not scored
        try:
            weights[str(name)] = float(w)
        except (TypeError, ValueError):
            continue
    for override in (
        scorer_params.get("weights"),
        scorer_params.get("weights_w_pk"),
        feed_params.get("weights"),
    ):
        if _is_mapping(override):
            for k, v in override.items():
                if isinstance(v, bool):
                    continue
                try:
                    weights[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
    return weights


def _instantiate(factory: Any, params: Mapping[str, Any], agent_ctx: Any, rng: random.Random) -> FeedScorer:
    if isinstance(factory, type):
        return factory(params=params, agent_ctx=agent_ctx, rng=rng)
    try:
        return factory(params=params, agent_ctx=agent_ctx, rng=rng)
    except TypeError:
        return factory(params)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def materialize_feed(
    spec: Any,
    candidates: Sequence[Any],
    agent_ctx: Any = None,
    *,
    top_k: int | None = None,
    rng: random.Random | None = None,
    now: float | None = None,
    registry: Mapping[str, Any] | None = None,
) -> list[Any]:
    """Materialize a ranked feed for one agent.

    ``spec`` may be a ``PlatformSpec``, a raw spec dict, or a ``FeedSpec``.
    ``candidates`` are item mappings (see :func:`_item_to_signal_vector`).
    Returns the top-``top_k`` items sorted by score desc (timestamp desc
    tiebreak); ``top_k`` defaults to ``feed.params.top_k``/``page_size`` or
    all candidates.  ``rng`` is injectable for deterministic jitter.
    """
    feed = _feed_section(spec)
    kind = str(_get(feed, "kind", "ranked"))
    feed_params = dict(_get(feed, "params") or {})
    scorer_spec = _get(feed, "scorer") or {}
    plugin_name = _get(scorer_spec, "plugin")
    scorer_params = dict(_get(scorer_spec, "params") or {})

    # Push feeds: no scorer allowed — ordering is a delivery-layer concern.
    if kind == "push":
        if plugin_name:
            raise FeedSpecError(
                f"push feed declares scorer plugin {plugin_name!r}; push specs must "
                "omit feed.scorer and use feed.delivery_model.inbox_rules instead"
            )
        # Placeholder: chronological inbox order until inbox_rules are executed.
        ordered = sorted(candidates, key=_item_ts, reverse=True)
        k = top_k if top_k is not None else int(feed_params.get("top_k") or feed_params.get("page_size") or len(ordered))
        return ordered[:k]

    reg = dict(PLUGIN_REGISTRY)
    if registry:
        reg.update(registry)
    factory = _resolve_plugin(plugin_name, kind, reg)
    scorer = _instantiate(factory, scorer_params, agent_ctx, rng or random.Random())
    scorer.reset()

    weights = _build_weights(feed, scorer_params, feed_params)
    params: dict[str, Any] = {
        **feed_params,
        **scorer_params,
        "weights": weights,
        "kind": kind,
        "now": now,
    }

    scored = []
    for i, item in enumerate(candidates):
        signals = _item_to_signal_vector(item)
        s = scorer.score(signals, agent_ctx, params)
        scored.append((s, _item_ts(item), i, item))
    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))

    k = top_k
    if k is None:
        k = feed_params.get("top_k") or feed_params.get("page_size") or len(scored)
    return [t[3] for t in scored[: int(k)]]


# ---------------------------------------------------------------------------
# Module-level convenience helpers (batch ranking + mask/diversity utils)
# ---------------------------------------------------------------------------


def chronological(items: Sequence[Any], key: str = "ts") -> list[Any]:
    """Return ``items`` sorted by ``key`` (default ``ts``) descending."""
    def _key(it: Any) -> float:
        if _is_mapping(it):
            v = it.get(key)
        else:
            v = getattr(it, key, None)
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    return sorted(items, key=_key, reverse=True)


chronological_order = chronological


def engagement_ranked(
    items: Sequence[Any],
    weights: Mapping[str, float] | None = None,
    **kwargs: Any,
) -> list[Any]:
    """Batch helper: score ``items`` with :class:`EngagementRankedScorer`."""
    scorer = EngagementRankedScorer(params=kwargs.pop("params", None), rng=kwargs.pop("rng", None))
    return scorer.score_and_rank(items, weights=weights, **kwargs)


score_engagement_ranked = engagement_ranked


def apply_observation_mask(signals: Mapping[str, Any], observed: Any) -> dict[str, Any]:
    """Zero out signal families not in ``observed``.

    ``observed`` may be a set/list of family names or a {name: bool} mapping.
    """
    if _is_mapping(observed):
        obs = {str(k): bool(v) for k, v in observed.items()}
        is_obs = lambda k: obs.get(k, k in signals and signals[k] is not None)
    else:
        obs_set = {str(k) for k in observed}
        is_obs = lambda k: k in obs_set
    return {k: (v if is_obs(k) else 0.0) for k, v in signals.items()}


mask_unobserved_signals = apply_observation_mask


def author_diversity_cap(items: Sequence[Any], max_per_author: int = 2, key: str = "score") -> list[Any]:
    """Greedily cap items per author after sorting by ``key`` desc.

    Preserves relative order within each author's kept items.
    """
    def _score(it: Any) -> float:
        v = it.get(key) if _is_mapping(it) else getattr(it, key, None)
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def _author(it: Any) -> Any:
        if _is_mapping(it):
            return it.get("author") or it.get("author_id")
        return getattr(it, "author", getattr(it, "author_id", None))

    counts: dict[Any, int] = {}
    out = []
    for it in sorted(items, key=_score, reverse=True):
        a = _author(it)
        if a is not None and counts.get(a, 0) >= max_per_author:
            continue
        if a is not None:
            counts[a] = counts.get(a, 0) + 1
        out.append(it)
    return out


dedupe_authors = author_diversity_cap


__all__ = [
    "SIGNAL_FAMILIES",
    "FeedSpecError",
    "SignalVector",
    "recency_decay",
    "zscore_rate",
    "dwell_fraction",
    "identity",
    "DEFAULT_CANONICALIZERS",
    "FeedScorer",
    "ChronologicalScorer",
    "EngagementRankedScorer",
    "PushInboxScorer",
    "BlueskyDiscoverScorer",
    "PLUGIN_REGISTRY",
    "register_scorer_plugin",
    "materialize_feed",
    "chronological",
    "chronological_order",
    "engagement_ranked",
    "score_engagement_ranked",
    "apply_observation_mask",
    "mask_unobserved_signals",
    "author_diversity_cap",
    "dedupe_authors",
]
