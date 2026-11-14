"""LLM cost model for MiroFish population simulations.

Token profile measured on OASIS (~20:1 input:output ratio):
    INPUT_TOKENS_PER_STEP  = 3356   (prompt: persona, env state, retrieved posts)
    OUTPUT_TOKENS_PER_STEP = 167    (action JSON)

Cost is expressed per "action" (one productive agent step = one LLM call),
blended to an effective USD figure per model tier:

    cheap    ~ $0.0005/action effective  (batch + cache-optimized small models)
    frontier ~ 17x cheap                 (frontier reasoning models, no discounts)

Stdlib only.
"""

from __future__ import annotations

# --- measured token profile (OASIS) -----------------------------------------
INPUT_TOKENS_PER_STEP = 3356
OUTPUT_TOKENS_PER_STEP = 167
TOKENS_PER_STEP = INPUT_TOKENS_PER_STEP + OUTPUT_TOKENS_PER_STEP  # 3523

# --- effective USD per action, by model tier --------------------------------
COST_PER_ACTION_USD = {
    "cheap": 0.0005,    # midpoint of observed $0.0004-0.0006/action
    "frontier": 0.0085, # ~17x cheap
}
FRONTIER_MULTIPLIER = 17.0

DAYS_PER_MONTH = 30

# --- emergent-behavior floor -------------------------------------------------
EMERGENT_FLOOR_POPULATION = 10_000

# --- optimization levers (targets / measured savings) ------------------------
PROMPT_CACHE_HIT_TARGET = 0.70        # fraction of prompt prefix served from cache
BATCH_DISCOUNT = 0.50                 # provider batch-API price reduction
EMBEDDING_CACHE_SAVINGS = (0.31, 0.80)  # observed range of embedding cost saved

# --- preset scenarios ---------------------------------------------------------
SCENARIOS = {
    "1K": 1_000,
    "10K": 10_000,
    "52K": 52_000,
    "100K": 100_000,
    "1M": 1_000_000,
}

VALID_TIERS = tuple(COST_PER_ACTION_USD)


def estimate_cost(
    population: int,
    steps_per_day: int = 24,
    activation_rate: float = 0.10,
    productive_rate: float = 0.10,
    model_tier: str = "cheap",
) -> dict:
    """Estimate monthly LLM spend for a simulated population.

    Args:
        population:      number of simulated agents.
        steps_per_day:   max decision steps per agent per day.
        activation_rate: fraction of steps where an agent is "awake"/active.
        productive_rate: fraction of active steps that issue an LLM action.
        model_tier:      'cheap' or 'frontier' (see COST_PER_ACTION_USD).

    Returns:
        dict with keys:
            population, model_tier, calls_per_day, tokens_per_day,
            monthly_llm_cost_usd, cost_per_action_usd,
            emergent_floor_warning (str | None),
            optimization_levers (dict of lever constants).
    """
    if model_tier not in COST_PER_ACTION_USD:
        raise ValueError(
            f"unknown model_tier {model_tier!r}; expected one of {VALID_TIERS}"
        )
    if population < 0:
        raise ValueError("population must be >= 0")

    calls_per_day = population * steps_per_day * activation_rate * productive_rate
    tokens_per_day = calls_per_day * TOKENS_PER_STEP
    monthly_cost = calls_per_day * DAYS_PER_MONTH * COST_PER_ACTION_USD[model_tier]

    warning = None
    if population < EMERGENT_FLOOR_POPULATION:
        warning = (
            f"EmergentFloor: population {population} < "
            f"{EMERGENT_FLOOR_POPULATION}; collective/emergent phenomena "
            "may not manifest at this scale"
        )

    return {
        "population": population,
        "model_tier": model_tier,
        "calls_per_day": round(calls_per_day, 2),
        "tokens_per_day": round(tokens_per_day, 2),
        "monthly_llm_cost_usd": round(monthly_cost, 4),
        "cost_per_action_usd": COST_PER_ACTION_USD[model_tier],
        "emergent_floor_warning": warning,
        "optimization_levers": {
            "prompt_cache_hit_target": PROMPT_CACHE_HIT_TARGET,
            "batch_discount": BATCH_DISCOUNT,
            "embedding_cache_savings_range": EMBEDDING_CACHE_SAVINGS,
        },
    }


def scenario(name_or_size) -> dict:
    """Resolve a preset scenario name ('10K') or raw population to a cost dict."""
    if isinstance(name_or_size, str):
        key = name_or_size.strip().upper()
        if key not in SCENARIOS:
            raise KeyError(
                f"unknown scenario {name_or_size!r}; "
                f"expected one of {sorted(SCENARIOS)} or an integer population"
            )
        population = SCENARIOS[key]
    else:
        population = int(name_or_size)
    return estimate_cost(population)


def scenario_table(model_tier: str = "cheap") -> list[dict]:
    """Cost estimates for all preset scenarios at a given tier."""
    return [
        {"scenario": name, **estimate_cost(pop, model_tier=model_tier)}
        for name, pop in SCENARIOS.items()
    ]
