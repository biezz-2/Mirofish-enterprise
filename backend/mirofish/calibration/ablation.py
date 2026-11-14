"""Ablation harness for MiroFish calibration (spec §18.2/§20.2).

Stage 1: leave-one-out over agent/simulation components.
Stage 2: 2^k factorial over the top-k sensitive components.

`sim_fn` is dependency-injected: it receives an `AblationConfig` and must
return a `MetricReport`. The harness owns seeding, replication, and
delta/divergence reporting only — it never imports the simulator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence

from .metrics import MetricReport, compare, metric_deltas

# Canonical toggleable components (spec §18.2 ablation list).
COMPONENTS: tuple[str, ...] = (
    "personality",
    "decision_layer",
    "ddm",
    "rescorla_wagner",
    "hawkes",
    "opinion_dynamics",
    "memory",
)

SimFn = Callable[["AblationConfig"], MetricReport]


@dataclass(frozen=True)
class AblationConfig:
    """Configuration handed to `sim_fn`.

    `disabled` holds component names switched OFF (leave-one-out /
    factorial masks). Everything else stays enabled. `population` and
    `seed` are carried here so `sim_fn(config)` is the full call signature.
    """

    disabled: frozenset[str] = frozenset()
    population: int = 1000
    seed: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = set(self.disabled) - set(COMPONENTS)
        if unknown:
            raise ValueError(f"unknown components: {sorted(unknown)}")

    def is_enabled(self, component: str) -> bool:
        return component not in self.disabled

    def with_disabled(self, *components: str) -> "AblationConfig":
        return AblationConfig(
            disabled=frozenset(set(self.disabled) | set(components)),
            population=self.population,
            seed=self.seed,
            metadata=dict(self.metadata),
        )


# ---------------------------------------------------------------------------
# aggregation helpers
# ---------------------------------------------------------------------------

def _metric_mean(reports: Sequence[MetricReport]) -> MetricReport:
    """Element-wise mean of numeric metrics across replicate reports."""
    _require_reports(reports)
    acc: dict[str, list[float]] = {}
    for r in reports:
        for k, v in r.numeric_metrics().items():
            acc.setdefault(k, []).append(v)
    means = {
        k: (sum(vs) / len(vs) if all(not math.isnan(v) for v in vs) else math.nan)
        for k, vs in acc.items()
    }
    return MetricReport(**{k: v for k, v in means.items() if k in MetricReport.__dataclass_fields__})


def _require_reports(reports: Sequence[MetricReport]) -> None:
    if not reports:
        raise ValueError("no replicate reports to aggregate")


def _run_replicates(
    sim_fn: SimFn, disabled: Iterable[str], *, population: int, seed: int, n: int
) -> list[MetricReport]:
    out = []
    for rep in range(n):
        cfg = AblationConfig(
            disabled=frozenset(disabled), population=population, seed=seed + rep
        )
        out.append(sim_fn(cfg))
    return out


# ---------------------------------------------------------------------------
# stage 1 — leave-one-out
# ---------------------------------------------------------------------------

def run_ablation_stage1(
    sim_fn: SimFn,
    components: Sequence[str] | None = None,
    n_replicates: int = 10,
    population: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Leave-one-out ablation.

    Runs `n_replicates` baseline sims (all components enabled) plus
    `n_replicates` sims per component with that component disabled.
    Returns a per-component delta report: for each metric, the mean
    difference (ablated − baseline) and a divergence flag from
    `metrics.compare`.
    """
    comps = list(components) if components is not None else list(COMPONENTS)
    _require_reports_check(comps, n_replicates, population)

    baseline_reports = _run_replicates(
        sim_fn, (), population=population, seed=seed, n=n_replicates
    )
    baseline = _metric_mean(baseline_reports)

    per_component: dict[str, Any] = {}
    for comp in comps:
        reports = _run_replicates(
            sim_fn, (comp,), population=population, seed=seed, n=n_replicates
        )
        ablated = _metric_mean(reports)
        deltas = metric_deltas(ablated, baseline)
        divergences = compare(ablated, baseline)
        per_component[comp] = {
            "ablated_mean": ablated,
            "deltas": deltas,
            "diverged_metrics": sorted(k for k, v in divergences.items() if v["diverged"]),
            "divergences": divergences,
        }

    return {
        "stage": 1,
        "baseline": baseline,
        "components": per_component,
        "n_replicates": n_replicates,
        "population": population,
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# stage 2 — 2^k factorial over top components
# ---------------------------------------------------------------------------

def run_ablation_stage2(
    sim_fn: SimFn,
    top_components: Sequence[str],
    population: int = 10000,
    n_replicates: int = 3,
    seed: int = 0,
    components: Sequence[str] | None = None,
) -> dict[str, Any]:
    """2^k factorial skeleton over `top_components`.

    For each of the 2^k masks, the bit-selected top components are enabled
    and the rest disabled; all non-top components stay enabled. Each cell
    is replicated `n_replicates` times and aggregated to a mean
    MetricReport. Returns ``{mask: {"enabled": [...], "disabled": [...],
    "report": MetricReport}}`` plus a sorted cell list for downstream
    interaction analysis.
    """
    top = list(top_components)
    _require_reports_check(top, n_replicates, population)
    all_comps = set(components) if components is not None else set(COMPONENTS)

    cells: dict[str, Any] = {}
    for mask in range(2 ** len(top)):
        enabled = [top[i] for i in range(len(top)) if (mask >> i) & 1]
        disabled_top = [c for c in top if c not in enabled]
        # non-top components always remain enabled
        disabled = sorted(set(disabled_top) & all_comps)
        reports = _run_replicates(
            sim_fn,
            disabled,
            population=population,
            seed=seed + mask * 1000,
            n=n_replicates,
        )
        cells[str(mask)] = {
            "mask": mask,
            "enabled": enabled,
            "disabled": disabled,
            "report": _metric_mean(reports),
        }

    return {
        "stage": 2,
        "cells": cells,
        "cell_order": [cells[str(m)]["mask"] for m in range(2 ** len(top))],
        "top_components": top,
        "n_replicates": n_replicates,
        "population": population,
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# real-data ceiling hook (interface only)
# ---------------------------------------------------------------------------

def real_data_ceiling(
    observed_snapshot: Any,
    sim_fn: SimFn | None = None,
    *,
    population: int = 10000,
    seed: int = 0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Real-data ceiling hook — interface only, not yet implemented.

    Intended contract:
      1. `observed_snapshot` is a parsed real-world cascade: adoption tree,
         event timestamps, signed interaction graph, engagement counts,
         and (optionally) topic distributions — i.e. everything needed to
         populate a `MetricReport` via `calibration.metrics`.
      2. Initialize the simulator state from the observed snapshot
         (seed agents/topics/graph from observed marginals) via the same
         `sim_fn`/config path used in the ablation harness.
      3. Run the calibrated sim and return
         ``{"observed": MetricReport, "simulated": MetricReport,
            "divergences": metrics.compare(observed, simulated)}``.

    Raises NotImplementedError until the observed-data loader and
    state-initialization path are wired in.
    """
    raise NotImplementedError(
        "real_data_ceiling is an interface stub: wire the observed-snapshot "
        "loader and sim-state initializer, then compare observed vs "
        "simulated MetricReports via calibration.metrics.compare."
    )


# ---------------------------------------------------------------------------
# null-interface preservation — degenerate no-op replacements
# ---------------------------------------------------------------------------

# Valid no-op replacements per component. Each preserves the component's
# interface contract while removing its causal contribution, so ablation
# cells remain runnable instead of crashing on missing modules.
NULL_INTERFACES: dict[str, dict[str, Any]] = {
    "personality": {
        "replacement": "constant_persona",
        "description": "All agents share the population-mean persona; "
                       "per-agent trait variance set to 0.",
        "params": {"trait_variance": 0.0},
    },
    "decision_layer": {
        "replacement": "argmax_policy",
        "description": "Deterministic argmax over utilities "
                       "(temperature -> 0); no stochastic choice.",
        "params": {"temperature": 0.0},
    },
    "ddm": {
        "replacement": "fixed_dwell",
        "description": "Decision dwell time fixed at the population median; "
                       "drift/diffusion processes disabled.",
        "params": {"dwell": "median"},
    },
    "rescorla_wagner": {
        "replacement": "frozen_weights",
        "description": "Learning rates alpha = beta = 0; stimulus weights "
                       "frozen at initialization.",
        "params": {"alpha": 0.0, "beta": 0.0},
    },
    "hawkes": {
        "replacement": "poisson_matched_rate",
        "description": "Self-exciting Hawkes process replaced by a "
                       "homogeneous Poisson process at the matched mean rate; "
                       "no temporal clustering.",
        "params": {"matched_rate": True},
    },
    "opinion_dynamics": {
        "replacement": "frozen_opinions",
        "description": "Opinion update rate 0; agents hold initial opinions "
                       "for the whole run (Deffuant/Bayesian updates off).",
        "params": {"update_rate": 0.0},
    },
    "memory": {
        "replacement": "empty_memory",
        "description": "Memory capacity 0 / always-empty recall; agents act "
                       "without history.",
        "params": {"capacity": 0},
    },
}


def degenerate_interface(component: str, **overrides: Any) -> dict[str, Any]:
    """Return the valid no-op replacement spec for `component`.

    The returned dict is a drop-in contract for the simulator's component
    registry: ``{"component", "mode": "no_op", "replacement",
    "description", "params"}``. `**overrides` merge into ``params``.
    """
    if component not in NULL_INTERFACES:
        raise KeyError(
            f"no null interface for {component!r}; known: {sorted(NULL_INTERFACES)}"
        )
    spec = dict(NULL_INTERFACES[component])
    params = dict(spec.get("params", {}))
    params.update(overrides)
    return {
        "component": component,
        "mode": "no_op",
        "replacement": spec["replacement"],
        "description": spec["description"],
        "params": params,
    }


def _require_reports_check(
    components: Sequence[str], n_replicates: int, population: int
) -> None:
    if not components:
        raise ValueError("components must be non-empty")
    unknown = set(components) - set(COMPONENTS)
    if unknown:
        raise ValueError(f"unknown components: {sorted(unknown)}")
    if n_replicates < 1:
        raise ValueError("n_replicates must be >= 1")
    if population < 1:
        raise ValueError("population must be >= 1")
