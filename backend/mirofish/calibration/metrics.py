"""Calibration metric battery (spec §18.2 / §20.2).

Stdlib + numpy only. All functions are pure, deterministic, and typed.
Seeded randomness is the caller's responsibility — nothing here uses RNG.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, fields
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

ArrayLike = Iterable[float] | np.ndarray


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _as_1d_float(values: ArrayLike, name: str = "values") -> np.ndarray:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-D, got shape {arr.shape}")
    return arr


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# §18.2 cascade metrics
# ---------------------------------------------------------------------------

def _tree_nodes(children: Mapping[Any, Sequence[Any]]) -> set[Any]:
    nodes: set[Any] = set()
    for parent, kids in children.items():
        nodes.add(parent)
        nodes.update(kids)
    return nodes


def _tree_adjacency(children: Mapping[Any, Sequence[Any]]) -> dict[Any, set[Any]]:
    adj: dict[Any, set[Any]] = {n: set() for n in _tree_nodes(children)}
    for parent, kids in children.items():
        for kid in kids:
            adj[parent].add(kid)
            adj[kid].add(parent)
    return adj


def _bfs_distances(adj: Mapping[Any, set[Any]], source: Any) -> dict[Any, int]:
    dist = {source: 0}
    frontier = [source]
    while frontier:
        nxt = []
        for node in frontier:
            for nb in adj[node]:
                if nb not in dist:
                    dist[nb] = dist[node] + 1
                    nxt.append(nb)
        frontier = nxt
    return dist


def cascade_size(children: Mapping[Any, Sequence[Any]]) -> int:
    """Number of adoption events in the cascade (non-root nodes)."""
    return sum(len(kids) for kids in children.values())


def cascade_depth(children: Mapping[Any, Sequence[Any]]) -> int:
    """Longest root-to-leaf path length (edges) in the cascade tree."""
    if not children:
        return 0
    adj = _tree_adjacency(children)
    # roots = nodes that are never a child
    child_set = {c for kids in children.values() for c in kids}
    roots = [n for n in adj if n not in child_set]
    roots = roots or list(adj)
    return max(
        max(_bfs_distances(adj, r).values()) for r in roots
    )


def cascade_breadth(children: Mapping[Any, Sequence[Any]]) -> int:
    """Maximum number of direct children of any single node."""
    return max((len(kids) for kids in children.values()), default=0)


def structural_virality(children: Mapping[Any, Sequence[Any]]) -> float:
    """Weng et al. structural virality: mean shortest-path distance over all
    unordered node pairs in the cascade graph. Returns 0.0 for <2 nodes."""
    nodes = sorted(_tree_nodes(children), key=repr)
    n = len(nodes)
    if n < 2:
        return 0.0
    adj = _tree_adjacency(children)
    total = 0
    count = 0
    for i, a in enumerate(nodes):
        dists = _bfs_distances(adj, a)
        for b in nodes[i + 1 :]:
            if b in dists:
                total += dists[b]
                count += 1
    return total / count if count else 0.0


def time_to_peak_t50(cascade_times: ArrayLike, final_size: int | None = None) -> float:
    """Fraction of total cascade duration elapsed when cumulative adoptions
    first reach 50% of the final cascade size. Returns value in [0, 1]."""
    t = _as_1d_float(cascade_times, "cascade_times")
    _require(len(t) >= 1, "cascade_times must be non-empty")
    t = np.sort(t)
    size = final_size if final_size is not None else len(t)
    _require(size > 0, "final_size must be positive")
    idx = int(math.ceil(0.5 * size)) - 1
    idx = min(max(idx, 0), len(t) - 1)
    span = t[-1] - t[0]
    if span <= 0:
        return 0.0
    return float((t[idx] - t[0]) / span)


# ---------------------------------------------------------------------------
# §20.2 temporal metrics
# ---------------------------------------------------------------------------

def inter_event_times(timestamps: ArrayLike) -> np.ndarray:
    """Sorted diffs between consecutive event timestamps."""
    t = np.sort(_as_1d_float(timestamps, "timestamps"))
    if len(t) < 2:
        return np.empty(0)
    return np.diff(t)


def burstiness(ies: ArrayLike) -> float:
    """Goh–Barabási burstiness parameter B = (σ − m) / (σ + m) computed on
    inter-event times. B ∈ [−1, 1]; positive = bursty."""
    x = _as_1d_float(ies, "inter_event_times")
    _require(len(x) >= 2, "burstiness requires >= 2 inter-event times")
    m = float(np.mean(x))
    s = float(np.std(x))  # population std, per Goh–Barabási
    denom = s + m
    if denom == 0:
        return 0.0
    return (s - m) / denom


def ks_distance(sample: ArrayLike, reference: ArrayLike) -> float:
    """Two-sample Kolmogorov–Smirnov statistic D = sup_x |F_s(x) − F_r(x)|,
    computed manually (no scipy)."""
    s = np.sort(_as_1d_float(sample, "sample"))
    r = np.sort(_as_1d_float(reference, "reference"))
    _require(len(s) > 0 and len(r) > 0, "sample and reference must be non-empty")
    grid = np.unique(np.concatenate([s, r]))
    cdf_s = np.searchsorted(s, grid, side="right") / len(s)
    cdf_r = np.searchsorted(r, grid, side="right") / len(r)
    return float(np.max(np.abs(cdf_s - cdf_r)))


# ---------------------------------------------------------------------------
# §20.2 inequality metrics
# ---------------------------------------------------------------------------

def gini(values: ArrayLike) -> float:
    """Gini coefficient for non-negative values. 0 = perfect equality,
    →1 = maximal inequality. Returns 0.0 for all-zero input."""
    x = np.sort(_as_1d_float(values, "values"))
    n = len(x)
    _require(n > 0, "values must be non-empty")
    total = float(np.sum(x))
    if total <= 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2.0 * np.sum(idx * x)) / (n * total) - (n + 1.0) / n)


def palma_ratio(values: ArrayLike, top_frac: float = 0.10, bottom_frac: float = 0.40) -> float:
    """Palma ratio: share of total held by top `top_frac` vs bottom `bottom_frac`.
    Default top 10% / bottom 40%. Returns inf if bottom share is 0."""
    x = np.sort(_as_1d_float(values, "values"))[::-1]  # descending
    n = len(x)
    _require(n > 0, "values must be non-empty")
    total = float(np.sum(x))
    _require(total > 0, "values must have positive sum")
    n_top = max(1, int(math.ceil(top_frac * n)))
    n_bot = max(1, int(math.floor(bottom_frac * n)))
    top_share = float(np.sum(x[:n_top])) / total
    bot_share = float(np.sum(x[-n_bot:])) / total
    if bot_share == 0:
        return math.inf
    return top_share / bot_share


def degree_distribution_fit(
    degrees: ArrayLike, x_min: float = 1.0
) -> dict[str, float]:
    """Power-law fit to a degree sequence.

    Exponent via continuous MLE: α = 1 + n / Σ ln(x_i / x_min).
    Goodness-of-fit via KS distance between empirical and fitted CDF.
    Returns {alpha, ks, x_min, n}.
    """
    x = _as_1d_float(degrees, "degrees")
    x = x[x >= x_min]
    n = len(x)
    _require(n >= 2, "need >= 2 observations above x_min")
    alpha = 1.0 + n / float(np.sum(np.log(x / x_min)))

    xs = np.sort(x)
    # fitted power-law CDF: F(x) = 1 - (x_min / x)^(alpha - 1)
    fitted = 1.0 - (x_min / xs) ** (alpha - 1.0)
    empirical = np.arange(1, n + 1) / n
    ks = float(np.max(np.abs(empirical - fitted)))
    return {"alpha": float(alpha), "ks": ks, "x_min": float(x_min), "n": float(n)}


# ---------------------------------------------------------------------------
# §20.2 content metrics
# ---------------------------------------------------------------------------

def _js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / b[mask])))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def topic_divergence(
    p: ArrayLike | Callable[[], ArrayLike],
    q: ArrayLike | Callable[[], ArrayLike],
) -> float:
    """Jensen–Shannon divergence between two topic distributions.

    BERTopic hook: pass callables that return topic-probability vectors —
    e.g. ``lambda: bertopic_model.transform(texts_a)[0]`` — or precomputed
    distribution vectors directly. The hook interface is intentionally
    duck-typed so any topic model (BERTopic, LDA, NMF) can plug in.
    """
    pv = p() if callable(p) else _as_1d_float(p, "p")
    qv = q() if callable(q) else _as_1d_float(q, "q")
    _require(len(pv) == len(qv) and len(pv) > 0, "topic distributions must match and be non-empty")
    return _js_divergence(np.asarray(pv, dtype=float), np.asarray(qv, dtype=float))


def rwc_controversy(
    signed_graph: Mapping[tuple[int, int], float]
    | Iterable[tuple[int, int, float]]
    | np.ndarray,
) -> dict[str, float]:
    """Robertson–Webster–Cornell controversy score on a signed interaction
    graph.

    Accepts either an adjacency matrix (signed weights, 0 = no edge), an
    iterable of ``(i, j, weight)`` triples, or a ``{(i, j): weight}`` mapping.
    Positive weight = supportive/agree interaction, negative = antagonistic.

    controversy = W_neg / (W_pos + W_neg)  — the fraction of antagonistic
    interaction weight, matching RWC's "proportion of disagree interactions".
    """
    weights: list[float] = []
    if isinstance(signed_graph, np.ndarray):
        mat = np.asarray(signed_graph, dtype=float)
        _require(mat.ndim == 2 and mat.shape[0] == mat.shape[1], "adjacency must be square")
        weights = mat[np.triu_indices(mat.shape[0], k=1)].tolist()
        weights = [w for w in weights if w != 0]
    elif isinstance(signed_graph, Mapping):
        weights = [float(w) for w in signed_graph.values() if float(w) != 0]
    else:
        for triple in signed_graph:
            i, j, w = triple
            if i != j:
                weights.append(float(w))

    weights = [w for w in weights if w != 0]
    _require(len(weights) > 0, "signed graph must contain at least one edge")
    w_pos = sum(w for w in weights if w > 0)
    w_neg = -sum(w for w in weights if w < 0)
    total = w_pos + w_neg
    return {
        "controversy": float(w_neg / total) if total > 0 else 0.0,
        "positive_weight": float(w_pos),
        "negative_weight": float(w_neg),
        "n_edges": float(len(weights)),
    }


def engagement_ratios(events: Iterable[str] | Mapping[str, float]) -> dict[str, float]:
    """Like:comment:share engagement ratios.

    Accepts an iterable of event-type strings or a counts mapping.
    Returns normalized ratios (sum = 1) plus raw counts.
    """
    if isinstance(events, Mapping):
        counts = {k: float(v) for k, v in events.items()}
    else:
        counts = {"like": 0.0, "comment": 0.0, "share": 0.0}
        for e in events:
            key = str(e).lower()
            if key in counts:
                counts[key] += 1.0
    total = sum(counts.get(k, 0.0) for k in ("like", "comment", "share"))
    _require(total > 0, "engagement events must be non-empty")
    return {
        "like_ratio": counts.get("like", 0.0) / total,
        "comment_ratio": counts.get("comment", 0.0) / total,
        "share_ratio": counts.get("share", 0.0) / total,
        "like_count": counts.get("like", 0.0),
        "comment_count": counts.get("comment", 0.0),
        "share_count": counts.get("share", 0.0),
    }


# ---------------------------------------------------------------------------
# MetricReport
# ---------------------------------------------------------------------------

@dataclass
class MetricReport:
    """Aggregated output of the §18.2/§20.2 metric battery."""

    # cascade (§18.2)
    cascade_size: float = math.nan
    cascade_depth: float = math.nan
    cascade_breadth: float = math.nan
    structural_virality: float = math.nan
    time_to_peak_t50: float = math.nan
    # temporal (§20.2)
    mean_inter_event_time: float = math.nan
    burstiness: float = math.nan
    ks_distance: float = math.nan  # vs. reference distribution, if supplied
    # inequality (§20.2)
    gini: float = math.nan
    palma_ratio: float = math.nan
    powerlaw_alpha: float = math.nan
    powerlaw_ks: float = math.nan
    # content (§20.2)
    topic_divergence: float = math.nan
    rwc_controversy: float = math.nan
    like_ratio: float = math.nan
    comment_ratio: float = math.nan
    share_ratio: float = math.nan
    # extensibility
    extras: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def numeric_metrics(self) -> dict[str, float]:
        """All scalar float fields (excludes extras/metadata)."""
        out: dict[str, float] = {}
        for f in fields(self):
            if f.name in ("extras", "metadata"):
                continue
            v = getattr(self, f.name)
            if isinstance(v, (int, float)):
                out[f.name] = float(v)
        return out


def compare(
    report_a: MetricReport,
    report_b: MetricReport,
    *,
    rtol: float = 0.05,
    atol: float = 1e-9,
) -> dict[str, dict[str, Any]]:
    """Compare two MetricReports metric-by-metric.

    Returns ``{metric: {a, b, abs_diff, rel_diff, diverged}}`` for every
    shared numeric field. ``diverged`` is True when the relative difference
    exceeds ``rtol`` or the absolute difference exceeds ``atol``. A metric
    diverges if exactly one side is NaN.
    """
    a_metrics = report_a.numeric_metrics()
    b_metrics = report_b.numeric_metrics()
    out: dict[str, dict[str, Any]] = {}
    for name in sorted(set(a_metrics) & set(b_metrics)):
        va, vb = a_metrics[name], b_metrics[name]
        if math.isnan(va) or math.isnan(vb):
            out[name] = {
                "a": va, "b": vb, "abs_diff": math.nan, "rel_diff": math.nan,
                "diverged": math.isnan(va) != math.isnan(vb),
            }
            continue
        abs_diff = abs(va - vb)
        denom = max(abs(vb), 1e-12)
        rel_diff = abs_diff / denom
        diverged = rel_diff > rtol or abs_diff > atol
        out[name] = {
            "a": va, "b": vb,
            "abs_diff": abs_diff, "rel_diff": rel_diff,
            "diverged": diverged,
        }
    return out


def metric_deltas(report_a: MetricReport, report_b: MetricReport) -> dict[str, float]:
    """Plain per-metric difference ``a − b`` (NaN-safe)."""
    a_m, b_m = report_a.numeric_metrics(), report_b.numeric_metrics()
    return {
        name: (a_m.get(name, math.nan) - b_m.get(name, math.nan))
        for name in sorted(set(a_m) | set(b_m))
    }
