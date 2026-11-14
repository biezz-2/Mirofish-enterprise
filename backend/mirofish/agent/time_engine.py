"""OASIS-style time engine for MiroFish (paper §11).

- ``Clock``: single source of simulated time. A magnification factor μ maps
  one real second to μ simulated seconds; internally the clock counts ticks.
  ``sandbox_clock()`` returns the one ``Clock`` instance (or the one injected
  into an :class:`ActivityVector`/``SessionModel`).
- ``ActivityVector``: 24-dimensional hourly activation probability per agent,
  conditioned on platform profile (``PLATFORM_PROFILES``).
- ``SessionModel``: inter-session return probability modulated by the reward
  of the last session (Rescorla–Wagner-shaped update), session extent
  distribution, per-platform attention budget, heavy-tailed inter-action
  intervals.
- ``adaptive_step_size``: fast-forwards low-activity windows.

Deterministic: every stochastic component takes an injected
``random.Random`` (or derives one from a seed).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------


class Clock:
    """Simulated clock with magnification.

    ``tick`` counts simulation ticks (default: 1 tick = 1 sim-minute).
    ``magnification_factor`` μ maps real→sim time for wall-clock pacing:
    ``sim_seconds = real_seconds * μ``. ``sandbox_clock()`` returns the
    process-wide clock so every subsystem shares one time source.
    """

    _instance: "Clock | None" = None

    def __init__(self, magnification_factor: float = 60.0,
                 ticks_per_sim_hour: int = 60,
                 seed: int | None = None) -> None:
        if magnification_factor <= 0:
            raise ValueError("magnification_factor must be > 0")
        self.magnification_factor = float(magnification_factor)
        self.ticks_per_sim_hour = int(ticks_per_sim_hour)
        self._tick = 0
        self._rng = random.Random(seed)
        self._base_real = None  # set on first advance_from_real

    # -- singleton access --------------------------------------------------

    @classmethod
    def sandbox_clock(cls, magnification_factor: float = 60.0,
                      seed: int | None = None) -> "Clock":
        """Return the shared sandbox clock, creating it on first call."""
        if cls._instance is None:
            cls._instance = cls(magnification_factor=magnification_factor,
                                seed=seed)
        return cls._instance

    @classmethod
    def reset_sandbox(cls) -> None:
        cls._instance = None

    # -- properties --------------------------------------------------------

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def sim_seconds(self) -> float:
        # ticks_per_sim_hour ticks = 1 sim-hour = 3600 sim-seconds.
        return self._tick * 3600.0 / self.ticks_per_sim_hour

    @property
    def sim_hour_of_day(self) -> float:
        """Fractional hour-of-day [0,24) in sim time."""
        hours = self.sim_seconds / 3600.0
        return hours % 24.0

    @property
    def rng(self) -> random.Random:
        return self._rng

    # -- mutation ----------------------------------------------------------

    def advance(self, n_ticks: int = 1) -> int:
        self._tick += int(n_ticks)
        return self._tick

    def advance_real_seconds(self, real_seconds: float) -> int:
        """Advance by wall-clock seconds scaled by μ."""
        sim_seconds = real_seconds * self.magnification_factor
        ticks = int(sim_seconds * self.ticks_per_sim_hour / 3600.0)
        return self.advance(max(1, ticks))

    def set_tick(self, tick: int) -> None:
        self._tick = int(tick)

    def seed(self, seed: int) -> None:
        self._rng.seed(seed)

    def __repr__(self) -> str:
        return (f"Clock(tick={self._tick}, mu={self.magnification_factor}, "
                f"hod={self.sim_hour_of_day:.2f})")


# ---------------------------------------------------------------------------
# Platform profiles & ActivityVector
# ---------------------------------------------------------------------------

# 24 hourly activation probabilities (index = hour 0..23).
# Shapes chosen to match the paper §11 platform classes:
#   x/reddit: bimodal (morning + evening commute peaks)
#   tiktok:   sharp evening peak
#   linkedin: weekday 9-17 business hours
#   whatsapp: near-continuous with mild night dip
#   youtube:  evening-heavy
PLATFORM_PROFILES: dict[str, dict[str, Any]] = {
    "x": {
        "kind": "microblog",
        "attention_budget": 8,          # actions per session
        "hourly": [
            0.10, 0.07, 0.05, 0.04, 0.04, 0.05, 0.09, 0.16,
            0.24, 0.26, 0.24, 0.22, 0.20, 0.22, 0.24, 0.26,
            0.28, 0.30, 0.32, 0.36, 0.40, 0.42, 0.38, 0.25,
        ],
    },
    "reddit": {
        "kind": "forum",
        "attention_budget": 6,
        "hourly": [
            0.08, 0.05, 0.04, 0.03, 0.03, 0.05, 0.10, 0.18,
            0.26, 0.28, 0.26, 0.24, 0.24, 0.26, 0.28, 0.30,
            0.32, 0.34, 0.36, 0.38, 0.42, 0.45, 0.40, 0.28,
        ],
    },
    "tiktok": {
        "kind": "short_video",
        "attention_budget": 15,
        "hourly": [
            0.05, 0.03, 0.02, 0.02, 0.02, 0.03, 0.05, 0.08,
            0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24, 0.30,
            0.38, 0.48, 0.60, 0.72, 0.80, 0.85, 0.82, 0.55,
        ],
    },
    "linkedin": {
        "kind": "professional",
        "attention_budget": 5,
        "hourly": [
            0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.05,
            0.15, 0.45, 0.60, 0.62, 0.55, 0.58, 0.60, 0.55,
            0.50, 0.48, 0.42, 0.30, 0.15, 0.06, 0.03, 0.02,
        ],
        "weekday_only": True,
    },
    "whatsapp": {
        "kind": "messaging",
        "attention_budget": 20,
        "hourly": [
            0.55, 0.45, 0.35, 0.28, 0.25, 0.30, 0.45, 0.60,
            0.72, 0.78, 0.76, 0.75, 0.74, 0.76, 0.78, 0.80,
            0.82, 0.85, 0.86, 0.84, 0.80, 0.75, 0.68, 0.60,
        ],
    },
    "youtube": {
        "kind": "video",
        "attention_budget": 10,
        "hourly": [
            0.04, 0.03, 0.02, 0.02, 0.02, 0.03, 0.05, 0.08,
            0.10, 0.12, 0.13, 0.14, 0.15, 0.16, 0.18, 0.22,
            0.28, 0.38, 0.50, 0.62, 0.70, 0.72, 0.65, 0.40,
        ],
    },
}


def _weekday(sim_seconds: float) -> int:
    """0=Monday..6=Sunday for sim time (epoch anchored at a Monday)."""
    return int(sim_seconds // 86400.0) % 7


@dataclass
class ActivityVector:
    """24-dim hourly activation probabilities for one agent on a platform.

    ``sample_activation(agent_id, tick, clock=None)`` performs a Bernoulli
    draw using the hour-of-day (and weekday mask for professional platforms).
    """

    platform: str
    profile: dict[str, Any] = field(default_factory=dict)
    rng: random.Random = field(default_factory=random.Random)
    scale: float = 1.0  # global activity multiplier [0, ~2]

    def __post_init__(self) -> None:
        if not self.profile:
            self.profile = PLATFORM_PROFILES.get(
                self.platform, PLATFORM_PROFILES["x"])
        hourly = self.profile.get("hourly")
        if hourly is None or len(hourly) != 24:
            raise ValueError(f"platform '{self.platform}' needs 24 hourly probs")

    # -- API ---------------------------------------------------------------

    @property
    def attention_budget(self) -> int:
        return int(self.profile.get("attention_budget", 8))

    @property
    def kind(self) -> str:
        return str(self.profile.get("kind", "generic"))

    def hourly_probs(self) -> list[float]:
        return [min(1.0, p * self.scale) for p in self.profile["hourly"]]

    def prob_at(self, hour_of_day: float, weekday: int | None = None) -> float:
        """Activation probability at fractional hour-of-day."""
        h = hour_of_day % 24.0
        i0 = int(h) % 24
        i1 = (i0 + 1) % 24
        frac = h - int(h)
        p = self.profile["hourly"][i0] * (1 - frac) + \
            self.profile["hourly"][i1] * frac
        if self.profile.get("weekday_only") and weekday is not None \
                and weekday >= 5:
            return 0.0
        return min(1.0, p * self.scale)

    def sample_activation(self, agent_id: str, tick: int,
                          clock: Clock | None = None) -> bool:
        """Bernoulli draw: is ``agent_id`` active at ``tick``?"""
        clk = clock or Clock.sandbox_clock()
        hod = (tick / clk.ticks_per_sim_hour) % 24.0
        wd = _weekday(tick * 3600.0 / clk.ticks_per_sim_hour)
        p = self.prob_at(hod, weekday=wd)
        # Per-agent jitter: each agent has a stable multiplicative trait.
        trait = 0.8 + 0.4 * _stable_unit(agent_id)
        return self.rng.random() < min(1.0, p * trait)


def _stable_unit(agent_id: str) -> float:
    """Deterministic pseudo-random in [0,1) derived from agent_id."""
    h = 0
    for ch in agent_id:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    # xorshift-ish finalizer
    h ^= h >> 16
    h = (h * 0x7FEB352D) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


# ---------------------------------------------------------------------------
# SessionModel
# ---------------------------------------------------------------------------


@dataclass
class SessionState:
    """Per-agent session bookkeeping."""

    agent_id: str
    in_session: bool = False
    last_session_end_tick: int | None = None
    last_reward: float = 0.0        # last observed reward
    value: float = 0.0              # Rescorla-Wagner value estimate V
    return_prob: float = 0.5        # current p_r = sigmoid(logit(base) + kappa*V)
    actions_this_session: int = 0
    attention_budget: int = 8


@dataclass
class SessionModel:
    """Session dynamics for agents on one platform class.

    - ``p_return``: probability an agent starts a new session, modulated by
      the reward of its last session via a Rescorla–Wagner-shaped update:
          V <- V + lr * (reward - V);   p_r <- sigmoid(base + kappa * V)
    - ``session_extent``: number of actions per session ~ discretized
      lognormal-ish (heavy-tailed).
    - ``inter_action_interval``: heavy-tailed (Pareto) gaps in ticks.
    """

    platform: str = "generic"
    base_return_prob: float = 0.3
    learning_rate: float = 0.4       # Rescorla-Wagner alpha
    kappa: float = 4.0               # reward→logit gain
    rng: random.Random = field(default_factory=random.Random)
    attention_budget: int | None = None
    states: dict[str, SessionState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.attention_budget is None:
            prof = PLATFORM_PROFILES.get(self.platform)
            self.attention_budget = int(prof["attention_budget"]) \
                if prof else 8

    # -- state -------------------------------------------------------------

    def state(self, agent_id: str) -> SessionState:
        if agent_id not in self.states:
            self.states[agent_id] = SessionState(
                agent_id=agent_id,
                return_prob=self.base_return_prob,
                attention_budget=self.attention_budget or 8,
            )
        return self.states[agent_id]

    # -- session lifecycle -------------------------------------------------

    def should_start_session(self, agent_id: str, tick: int,
                             active: bool) -> bool:
        """Decide whether an active agent opens a session at ``tick``."""
        st = self.state(agent_id)
        if st.in_session:
            return False
        if not active:
            return False
        # Refractory period: minimum gap since last session end.
        if st.last_session_end_tick is not None and \
                tick - st.last_session_end_tick < 5:
            return False
        return self.rng.random() < st.return_prob

    def session_extent(self, agent_id: str) -> int:
        """Sample number of actions in a session (heavy-tailed around budget)."""
        st = self.state(agent_id)
        # Lognormal-ish: exp(N(mu, sigma)) clipped to [1, 3*budget].
        mu = math.log(max(1.0, st.attention_budget * 0.6))
        sigma = 0.7
        n = int(round(math.exp(self.rng.gauss(mu, sigma))))
        return max(1, min(n, st.attention_budget * 3))

    def inter_action_interval(self, agent_id: str) -> int:
        """Heavy-tailed gap (in ticks) between actions within a session.

        Pareto with xmin=1 tick, alpha≈1.6 → mean ≈ 2.7 ticks, long tail.
        """
        u = self.rng.random()
        alpha = 1.6
        return max(1, int(math.ceil(1.0 / (u ** (1.0 / alpha)))))

    def end_session(self, agent_id: str, tick: int, reward: float) -> None:
        """Close a session and apply Rescorla–Wagner reward update."""
        st = self.state(agent_id)
        st.in_session = False
        st.last_session_end_tick = tick
        st.actions_this_session = 0
        reward = max(-1.0, min(1.0, float(reward)))
        st.last_reward = reward
        # Rescorla–Wagner: V <- V + lr * (reward - V); p_r from V.
        st.value += self.learning_rate * (reward - st.value)
        p0 = max(1e-6, min(1 - 1e-6, self.base_return_prob))
        base_logit = math.log(p0 / (1 - p0))
        st.return_prob = 1.0 / (1.0 + math.exp(
            -(base_logit + self.kappa * st.value)))
        st.return_prob = max(0.01, min(0.95, st.return_prob))

    def begin_session(self, agent_id: str) -> int:
        st = self.state(agent_id)
        st.in_session = True
        st.actions_this_session = 0
        return self.session_extent(agent_id)


# ---------------------------------------------------------------------------
# Adaptive step size
# ---------------------------------------------------------------------------


@dataclass
class AdaptiveStepper:
    """Fast-forward low-activity windows.

    Given the set of agents and their :class:`ActivityVector`\\ s, estimate
    the fraction of agents likely active over the next ``window_ticks``.
    If below ``low_activity_threshold``, advance the clock by the whole
    window in one step; otherwise advance in ``base_step`` increments.
    """

    clock: Clock
    activity: dict[str, ActivityVector]
    low_activity_threshold: float = 0.05   # fraction of agents active
    base_step_ticks: int = 5
    max_step_ticks: int = 60

    def expected_active_fraction(self, tick: int, window_ticks: int) -> float:
        if not self.activity:
            return 0.0
        # Sample-free estimate: mean hourly prob over the window.
        total = 0.0
        for vec in self.activity.values():
            # approximate: prob at current hour (cheap, deterministic)
            hod = ((tick + window_ticks // 2) / self.clock.ticks_per_sim_hour) % 24.0
            wd = _weekday((tick + window_ticks // 2) * 3600.0 /
                          self.clock.ticks_per_sim_hour)
            total += vec.prob_at(hod, weekday=wd)
        return total / len(self.activity)

    def step(self, tick: int) -> int:
        """Return the number of ticks to advance from ``tick``."""
        frac = self.expected_active_fraction(tick, self.base_step_ticks)
        if frac < self.low_activity_threshold:
            # Probe a longer window; if still quiet, fast-forward.
            frac_long = self.expected_active_fraction(tick,
                                                      self.max_step_ticks)
            if frac_long < self.low_activity_threshold:
                return self.max_step_ticks
        return self.base_step_ticks


def adaptive_step_size(clock: Clock, activity: dict[str, ActivityVector],
                       tick: int, low_activity_threshold: float = 0.05,
                       base_step: int = 5, max_step: int = 60) -> int:
    """Functional wrapper around :class:`AdaptiveStepper.step`."""
    stepper = AdaptiveStepper(clock=clock, activity=activity,
                              low_activity_threshold=low_activity_threshold,
                              base_step_ticks=base_step,
                              max_step_ticks=max_step)
    return stepper.step(tick)
