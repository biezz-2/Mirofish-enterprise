"""Agent behavioral decision layer (math only — decides WHETHER/WHEN).

Modules:
- personality: Big-Five (OCEAN) copula sampling, AR(1) trait dynamics,
  homeostatic needs + EPA emotions + action utility.
- decision: nested logit over action groups, drift–diffusion dwell
  time, prospect-theoretic valuation, and the §10 pipeline orchestrator.
"""

from mirofish.agent.personality import (
    DEFAULT_SIGMA_OCEAN,
    OCEAN_ORDER,
    NeedsEmotions,
    TraitState,
    sample_ocean_copula,
)
from mirofish.agent.decision import (
    ACTION_GROUPS,
    PRODUCTIVE_GROUPS,
    Decision,
    DecisionPipeline,
    DriftDiffusion,
    NestedLogit,
    ProspectValuation,
)

__all__ = [
    "ACTION_GROUPS",
    "DEFAULT_SIGMA_OCEAN",
    "OCEAN_ORDER",
    "PRODUCTIVE_GROUPS",
    "Decision",
    "DecisionPipeline",
    "DriftDiffusion",
    "NeedsEmotions",
    "NestedLogit",
    "ProspectValuation",
    "TraitState",
    "sample_ocean_copula",
]
