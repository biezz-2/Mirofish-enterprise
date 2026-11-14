"""Decision layer: whether/when agents act (paper §10 pipeline).

Pipeline per exposure tick:
    dwell time (DriftDiffusion) → content exposure → nested logit choice
    → flag `requires_llm` for productive actions (text rendering is the
    LLM's job later; this module only decides *that* an action happens).

Pure stdlib + optional numpy. All samplers take a seeded
`random.Random` for determinism.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from mirofish.agent.personality import (
    NeedsEmotions,
    TraitState,
    sample_ocean_copula,
)

__all__ = [
    "ACTION_GROUPS",
    "PRODUCTIVE_GROUPS",
    "NestedLogit",
    "DriftDiffusion",
    "ProspectValuation",
    "DecisionPipeline",
    "Decision",
]

ACTION_GROUPS = ("consume", "react", "amplify", "create", "relational")
# Groups whose chosen action produces new user-visible content → the
# downstream LLM renderer must be invoked.
PRODUCTIVE_GROUPS = frozenset({"amplify", "create"})


def _softmax(xs: Sequence[float]) -> list[float]:
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps)
    return [e / s for e in exps]


def _gumbel(rng: random.Random) -> float:
    u = min(max(rng.random(), 1e-12), 1.0 - 1e-12)
    return -math.log(-math.log(u))


def _norm(rng: random.Random) -> float:
    """Standard normal via Box–Muller."""
    u1 = min(max(rng.random(), 1e-12), 1.0)
    u2 = rng.random()
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


# ---------------------------------------------------------------------------
# Nested logit
# ---------------------------------------------------------------------------


@dataclass
class NestedLogit:
    """Two-level discrete-choice model over platform actions.

    Level 1 — choice among 5 action groups g ∈ ACTION_GROUPS:
        U_g = θ_g · z_agent + π_{p,g} + ε_g,   ε_g ~ Gumbel(0,1)
    Level 2 — conditional logit over the platform's action set A_{p,g}:
        V_a = β_{p,g} · x_a + κ_g · U_g(agent),  ε_a ~ Gumbel(0,1)

    `group_coefs[g]` is a coefficient vector over agent context features
    z_agent; `platform_group_intercepts[p]` is a dict g → π_{p,g};
    `action_coefs[(p, g)]` is a list of coefficient vectors, one per
    action in `platform_spec.actions` whose `verb`/`group` == g, aligned
    with the platform's declaration order; `action_coefs` keys may also
    be `(p, g, action_id)` to target a single action.

    Mixed-logit option: any coefficient may be given as
    {"mean": m, "sd": s} (or a plain sequence of such dicts); coefficients
    are then re-drawn per choice — flagged via `mixed=True`.
    """

    group_coefs: Mapping[str, Sequence[float]] = field(default_factory=dict)
    platform_group_intercepts: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    action_coefs: Mapping[Any, Sequence[Sequence[float]]] = field(default_factory=dict)
    mixed: bool = False
    rng: random.Random = field(default_factory=random.Random)

    # -- mixed-logit parameter handling -----------------------------------
    def _draw_param(self, spec: Any) -> float:
        if isinstance(spec, Mapping) and "mean" in spec:
            return float(spec["mean"]) + float(spec.get("sd", 0.0)) * _norm(self.rng)
        if isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
            # sequence of {mean,sd} draws → sum of independent normals
            return sum(self._draw_param(s) for s in spec)
        return float(spec)

    def _coef_vec(self, vec: Sequence[Any]) -> list[float]:
        if self.mixed:
            return [self._draw_param(c) for c in vec]
        return [float(c) for c in vec]

    def _group_utilities(
        self, agent_ctx: Mapping[str, float], platform_id: str
    ) -> dict[str, float]:
        z = [float(v) for v in agent_ctx.values()]
        pi = self.platform_group_intercepts.get(platform_id, {})
        utils = {}
        for g in ACTION_GROUPS:
            coef = self.group_coefs.get(g)
            base = float(pi.get(g, 0.0))
            if coef is not None:
                cv = self._coef_vec(coef)
                base += sum(c * zi for c, zi in zip(cv, z))
            utils[g] = base + _gumbel(self.rng)
        return utils

    @staticmethod
    def _actions_by_group(platform_spec: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
        out: dict[str, list[Mapping[str, Any]]] = {g: [] for g in ACTION_GROUPS}
        for act in platform_spec.get("actions", []):
            g = act.get("group") or act.get("verb") or "consume"
            if g in out:
                out[g].append(act)
        return out

    def _action_utility(
        self,
        group: str,
        action: Mapping[str, Any],
        group_actions: Sequence[Mapping[str, Any]],
        agent_ctx: Mapping[str, float],
        platform_id: str,
        group_utility: float,
    ) -> float:
        key = (platform_id, group, action.get("action_id"))
        direct = key in self.action_coefs
        coef_spec = self.action_coefs.get(key)
        if coef_spec is None:
            coef_spec = self.action_coefs.get((platform_id, group))
        base = float(action.get("bias", 0.0)) - 0.05 * float(action.get("cost", 0))
        if coef_spec is not None:
            # (p, g, action_id) keys hold a single coefficient vector;
            # (p, g) keys hold a list of vectors aligned with the group's
            # action declaration order.
            if (
                not direct
                and isinstance(coef_spec, Sequence)
                and coef_spec
                and isinstance(coef_spec[0], Sequence)
            ):
                idx = next(
                    (i for i, a in enumerate(group_actions)
                     if a.get("action_id") == action.get("action_id")),
                    0,
                )
                vec = coef_spec[min(idx, len(coef_spec) - 1)]
            else:
                vec = coef_spec
            cv = self._coef_vec(vec)
            x = [float(v) for v in agent_ctx.values()]
            # allow action-level feature override
            feat = action.get("features")
            if isinstance(feat, Mapping):
                x = [float(v) for v in feat.values()]
            base += sum(c * xi for c, xi in zip(cv, x))
        return base + 0.5 * group_utility + _gumbel(self.rng)

    def choose(
        self, agent_ctx: Mapping[str, float], platform_spec: Mapping[str, Any]
    ) -> tuple[str, str]:
        """Return (group, action_id) for one exposure decision."""
        platform_id = str(platform_spec.get("platform_id", "default"))
        group_utils = self._group_utilities(agent_ctx, platform_id)
        # level-1 pick
        groups = list(ACTION_GROUPS)
        probs = _softmax([group_utils[g] for g in groups])
        r = self.rng.random()
        acc = 0.0
        group = groups[-1]
        for g, p in zip(groups, probs):
            acc += p
            if r <= acc:
                group = g
                break

        acts = self._actions_by_group(platform_spec).get(group, [])
        if not acts:
            # group unavailable on this platform → fall back to consume
            group = "consume"
            acts = self._actions_by_group(platform_spec)["consume"]
        if not acts:
            return group, "noop"

        utils = [
            self._action_utility(
                group, a, acts, agent_ctx, platform_id, group_utils[group]
            )
            for a in acts
        ]
        aprobs = _softmax(utils)
        r = self.rng.random()
        acc = 0.0
        chosen = acts[-1]
        for a, p in zip(acts, aprobs):
            acc += p
            if r <= acc:
                chosen = a
                break
        return group, str(chosen.get("action_id", "unknown"))


# ---------------------------------------------------------------------------
# Drift–diffusion dwell time
# ---------------------------------------------------------------------------


@dataclass
class DriftDiffusion:
    """DDM for exposure dwell / decision latency.

    Evidence accumulator x_t follows
        dx = v·dt + s·√dt·N(0,1),   decision when |x| ≥ a,
    drift v = content_fit − τ_p (attention threshold), decision = sign(x).

    `simulate=True` runs an Euler–Maruyama simulation (accurate, seeded);
    `simulate=False` uses the closed-form approximation for the mean
    decision time  E[T] ≈ (a/v)·tanh(a·v/s²)  and P(+)=1/(1+e^{−2av/s²}).
    """

    boundary: float = 1.0          # a
    noise: float = 0.5             # s
    drift_scale: float = 1.0       # multiplies (fit − threshold)
    dt: float = 0.01               # Euler step (sim units)
    max_steps: int = 20_000
    time_scale: float = 1.0        # sim units → seconds
    simulate: bool = True
    rng: random.Random = field(default_factory=random.Random)

    def dwell_and_decide(
        self, content_fit: float, platform_threshold: float = 0.0
    ) -> tuple[float, int]:
        """Return (dwell_time_seconds, decision ∈ {−1,+1})."""
        v = self.drift_scale * (content_fit - platform_threshold)
        a, s = self.boundary, self.noise
        if abs(v) < 1e-9:
            # pure diffusion: mean exit time a²/s², symmetric choice
            t = a * a / max(s * s, 1e-9)
            decision = 1 if self.rng.random() < 0.5 else -1
            return t * self.time_scale, decision

        if not self.simulate:
            ez = math.tanh(a * v / (s * s))
            mean_t = (a / v) * ez if abs(v) > 1e-12 else a * a / (s * s)
            p_pos = 1.0 / (1.0 + math.exp(-2.0 * a * v / (s * s)))
            decision = 1 if self.rng.random() < p_pos else -1
            return max(mean_t, 0.0) * self.time_scale, decision

        x = 0.0
        t = 0.0
        sqdt = math.sqrt(self.dt)
        for _ in range(self.max_steps):
            x += v * self.dt + s * sqdt * _norm(self.rng)
            t += self.dt
            if abs(x) >= a:
                return t * self.time_scale, (1 if x > 0 else -1)
        # did not hit boundary: cap dwell, decide by sign of evidence
        return t * self.time_scale, (1 if x >= 0 else -1)


# ---------------------------------------------------------------------------
# Prospect-theoretic valuation
# ---------------------------------------------------------------------------


@dataclass
class ProspectValuation:
    """Piecewise power value function with reference point.

    v(x) =  x^α                 if x ≥ 0   (gain, α < 1 → diminishing)
          = −λ·(−x)^β           if x < 0   (loss, λ > 1 → loss aversion)

    `evaluate(expected, reference)` values the outcome relative to the
    reference point r (e.g. expected engagement): returns v(expected − r).
    """

    alpha: float = 0.88
    beta: float = 0.88
    loss_aversion: float = 2.25

    def v(self, x: float) -> float:
        if x >= 0.0:
            return x ** self.alpha
        return -self.loss_aversion * ((-x) ** self.beta)

    def evaluate(self, expected: float, reference: float) -> float:
        return self.v(expected - reference)


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------


@dataclass
class Decision:
    """One behavioral decision record (math layer only — no text)."""

    dwell_time: float
    dwell_decision: int
    group: str
    action_id: str
    requires_llm: bool
    utility: float | None = None
    valuation: float | None = None


@dataclass
class DecisionPipeline:
    """Orchestrates one §10 pipeline step per agent exposure.

    dwell → exposure valuation → nested logit → productive-action flag.

    agent_state bundles the per-agent math state:
        {"traits": TraitState, "needs": NeedsEmotions, "ctx": {...features}}
    `content` is a mapping with at least `fit` (content–agent fit ∈ [0,1])
    and optionally `expected`/`reference` for prospect valuation.
    """

    nested: NestedLogit = field(default_factory=NestedLogit)
    ddm: DriftDiffusion = field(default_factory=DriftDiffusion)
    prospect: ProspectValuation = field(default_factory=ProspectValuation)
    attention_threshold: float = 0.5
    engage_threshold: float = 0.0
    rng: random.Random = field(default_factory=random.Random)

    def step(
        self,
        agent_state: Mapping[str, Any],
        platform_spec: Mapping[str, Any],
        content: Mapping[str, float] | None = None,
        dt: float = 1.0,
    ) -> Decision:
        content = content or {}
        fit = float(content.get("fit", 0.5))
        platform_id = str(platform_spec.get("platform_id", "default"))
        p_threshold = float(
            platform_spec.get("attention_threshold", self.attention_threshold)
        )

        # 1) dwell / attention gate
        dwell_time, dwell_decision = self.ddm.dwell_and_decide(fit, p_threshold)
        if dwell_decision < 0 or dwell_time <= 0.0:
            return Decision(
                dwell_time=dwell_time,
                dwell_decision=dwell_decision,
                group="none",
                action_id="scroll_past",
                requires_llm=False,
            )

        # 2) trait/need drift + exposure valuation
        traits: TraitState | None = agent_state.get("traits")
        needs: NeedsEmotions | None = agent_state.get("needs")
        if traits is not None:
            traits.step(dt)
        if needs is not None:
            needs.tick(dt)

        valuation = None
        if "expected" in content:
            ref = float(content.get("reference", content.get("expected", 0.0)))
            valuation = self.prospect.evaluate(float(content["expected"]), ref)

        # 3) nested logit choice over actions
        agent_ctx = dict(agent_state.get("ctx", {}))
        # inject trait vector as features t0..t4 for coefficient models
        theta = traits.current_traits() if traits is not None else [0.5] * 5
        for i, t in enumerate(theta):
            agent_ctx.setdefault(f"trait{i}", t)
        if needs is not None:
            agent_ctx.setdefault("eval_emotion", needs.emotions_now()[0])
            agent_ctx.setdefault("activation", needs.emotions_now()[2])

        group, action_id = self.nested.choose(agent_ctx, platform_spec)

        # 4) apply action consequences to homeostatic state (math only)
        utility = None
        if needs is not None:
            needs.apply_action(action_id, dt=dt)
            utility = needs.utility(theta, action_id=action_id)

        requires_llm = group in PRODUCTIVE_GROUPS
        return Decision(
            dwell_time=dwell_time,
            dwell_decision=dwell_decision,
            group=group,
            action_id=action_id,
            requires_llm=requires_llm,
            utility=utility,
            valuation=valuation,
        )

    # convenience constructor used by tests / calibration
    @classmethod
    def from_population(
        cls,
        n: int,
        seed: int = 0,
        **kwargs: Any,
    ) -> tuple["DecisionPipeline", list[dict[str, Any]]]:
        """Build a pipeline plus n seeded agent states (traits+needs)."""
        import random as _r

        rng = _r.Random(seed)
        cop = sample_ocean_copula(n, rng=rng)
        agents = []
        for row in cop:
            theta = [float(x) for x in row]
            agents.append(
                {
                    "traits": TraitState(
                        theta0=theta,
                        phi=0.85,
                        tau=0.15,
                        rng=_r.Random(rng.random()),
                    ),
                    "needs": NeedsEmotions(),
                    "ctx": {f"trait{i}": t for i, t in enumerate(theta)},
                }
            )
        return cls(rng=_r.Random(seed), **kwargs), agents
