"""Behavioral primitives for the agent math layer (paper §9).

Pure-stdlib implementation. `numpy` is used opportunistically when
installed (arrays returned as `np.ndarray`); otherwise lists of floats
are returned. All randomness flows through a caller-supplied
`random.Random` (or `np.random.Generator`-compatible `.random()`/`.normal()`)
so simulation runs are fully deterministic given a seed.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Iterable, Sequence

try:  # optional acceleration / ndarray returns
    import numpy as _np

    HAS_NUMPY = True
except Exception:  # pragma: no cover - numpy not installed
    _np = None
    HAS_NUMPY = False

__all__ = [
    "HAS_NUMPY",
    "OCEAN_ORDER",
    "DEFAULT_SIGMA_OCEAN",
    "sample_ocean_copula",
    "TraitState",
    "NeedsEmotions",
]

OCEAN_ORDER = ("O", "C", "E", "A", "N")

# Big-Five correlation matrix, order O,C,E,A,N. Plausible inter-trait
# correlations (N = low Emotional Stability): N correlates negatively
# with E/O/A, mildly negatively with C. Diagonal = 1.
DEFAULT_SIGMA_OCEAN: tuple[tuple[float, ...], ...] = (
    (1.00, 0.15, 0.10, 0.05, -0.30),  # O
    (0.15, 1.00, 0.15, -0.10, -0.15),  # C
    (0.10, 0.15, 1.00, 0.20, -0.30),  # E
    (0.05, -0.10, 0.20, 1.00, -0.10),  # A
    (-0.30, -0.15, -0.30, -0.10, 1.00),  # N
)

_ND = statistics.NormalDist()


def _phi(z: float) -> float:
    """Standard normal CDF."""
    return _ND.cdf(z)


def _phi_inv(p: float) -> float:
    """Standard normal quantile."""
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return _ND.inv_cdf(p)


def _logit(p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def _cholesky(sigma: Sequence[Sequence[float]]) -> list[list[float]]:
    """Lower-triangular Cholesky factor L with L Lᵀ = Σ (pure Python)."""
    n = len(sigma)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sigma[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                if s <= 0.0:
                    raise ValueError("sigma is not positive definite")
                L[i][j] = math.sqrt(s)
            else:
                L[i][j] = s / L[j][j]
    return L


def _mvnormal(rng: random.Random, L: list[list[float]]) -> list[float]:
    """Sample z ~ N(0, Σ) given Cholesky factor L of Σ."""
    n = len(L)
    eps = [_norm_ppf(rng.random()) for _ in range(n)]
    return [sum(L[i][j] * eps[j] for j in range(i + 1)) for i in range(n)]


def _norm_ppf(u: float) -> float:
    return _phi_inv(u)


def _logistic(rng: random.Random, scale: float) -> float:
    """Sample Logistic(0, scale) via inverse CDF."""
    u = min(max(rng.random(), 1e-12), 1.0 - 1e-12)
    return scale * math.log(u / (1.0 - u))


def sample_ocean_copula(
    n: int,
    sigma_ocean: Sequence[Sequence[float]] = DEFAULT_SIGMA_OCEAN,
    rng: random.Random | None = None,
) -> "object":
    """Draw n Big-Five trait vectors via a Gaussian copula.

    Z ~ N(0, Σ), u = Φ(Z) marginally uniform on [0,1]. Returns an
    (n, 5) array (`np.ndarray` when numpy is installed, else a list of
    lists). Trait order follows `OCEAN_ORDER` = O, C, E, A, N.
    """
    if rng is None:
        rng = random.Random()
    L = _cholesky(sigma_ocean)
    rows = []
    for _ in range(n):
        z = _mvnormal(rng, L)
        rows.append([_phi(zi) for zi in z])
    if HAS_NUMPY:
        return _np.asarray(rows, dtype=float)
    return rows


@dataclass
class TraitState:
    """Per-agent latent trait state with AR(1) dynamics in logit space.

    s_{t+1} = φ·s_t + (1−φ)·μ + ε,  μ = logit(θ₀),  ε ~ Logistic(0, τ).

    φ ∈ [0.6, 0.95] controls trait persistence; τ is per-trait noise.
    """

    theta0: Sequence[float]
    phi: float | Sequence[float] = 0.85
    tau: float | Sequence[float] = 0.15
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        th = list(self.theta0)
        if len(th) != 5:
            raise ValueError("theta0 must have 5 entries (O,C,E,A,N)")
        self._mu = [_logit(t) for t in th]
        self._s = list(self._mu)  # start at the population mean in logit space
        if isinstance(self.phi, (int, float)):
            self._phi = [float(self.phi)] * 5
        else:
            self._phi = [float(p) for p in self.phi]
        for p in self._phi:
            if not 0.6 <= p <= 0.95:
                raise ValueError("phi must be in [0.6, 0.95]")
        if isinstance(self.tau, (int, float)):
            self._tau = [float(self.tau)] * 5
        else:
            self._tau = [float(t) for t in self.tau]

    def step(self, dt: float = 1.0) -> None:
        """Advance one time step; dt scales the innovation variance."""
        scale = math.sqrt(max(dt, 0.0))
        for k in range(5):
            eps = _logistic(self.rng, self._tau[k] * scale)
            self._s[k] = self._phi[k] * self._s[k] + (1.0 - self._phi[k]) * self._mu[k] + eps

    def current_traits(self) -> list[float]:
        """Observable traits θ_t = sigmoid(s_t) ∈ [0,1]^5."""
        return [_sigmoid(s) for s in self._s]


@dataclass
class NeedsEmotions:
    """Homeostatic needs + EPA affect + action utility (paper §9.2).

    Needs N_k decay toward zero between actions and are replenished by
    action-dependent gains:  N_k ← N_k·e^{−a_k Δt} + g_k(a).

    Emotions follow an EPA (Evaluation / Potency / Activation) model with
    inertia ψ:  ψ_t = ψ·ψ_{t−1} + (1−ψ)·v_t.

    Utility of action a for agent i:
        U_i(a) = Σ_k w_k · u_k(N_k, E) − ρ · C(θ, a)
    where u_k is a Cobb–Douglas shortfall term
        u_k = θ_k(a)^{w_k} · (N_k / N̄_k)^{γ_k}   (clipped to [0,1])
    and C(θ, a) is a trait-conditioned cost (effort, reputational risk).
    """

    needs: Sequence[float] = (0.5, 0.5, 0.5, 0.5)
    decay: float | Sequence[float] = 0.05
    gains: dict[str, Sequence[float]] = field(default_factory=dict)
    emotions: tuple[float, float, float] = (0.0, 0.0, 0.0)  # E, P, A ∈ [-1,1]
    emotion_inertia: float = 0.7
    utility_weights: Sequence[float] = (1.0, 1.0, 1.0, 1.0)
    cobb_exponents: Sequence[float] = (0.5, 0.5, 0.5, 0.5)
    need_scale: Sequence[float] = (1.0, 1.0, 1.0, 1.0)
    rho: float = 0.3
    cost_coef: Sequence[float] = (0.2, 0.2, 0.2, 0.2)

    def __post_init__(self) -> None:
        self._N = [float(x) for x in self.needs]
        if isinstance(self.decay, (int, float)):
            self._a = [float(self.decay)] * len(self._N)
        else:
            self._a = [float(x) for x in self.decay]
        self._w = [float(x) for x in self.utility_weights]
        self._g_exp = [float(x) for x in self.cobb_exponents]
        self._n_scale = [float(x) for x in self.need_scale]
        self._c = [float(x) for x in self.cost_coef]
        self._psi = (float(self.emotions[0]), float(self.emotions[1]), float(self.emotions[2]))

    # -- needs -----------------------------------------------------------
    def tick(self, dt: float = 1.0) -> None:
        """Passive decay of needs over dt seconds/rounds."""
        for k in range(len(self._N)):
            self._N[k] *= math.exp(-self._a[k] * dt)

    def apply_action(self, action_id: str, dt: float = 1.0) -> None:
        """Decay then add the action's need gains g_k(a)."""
        self.tick(dt)
        g = self.gains.get(action_id)
        if g is None:
            return
        for k, gv in enumerate(g):
            if k < len(self._N):
                self._N[k] = min(1.0, self._N[k] + float(gv))

    def current_needs(self) -> list[float]:
        return list(self._N)

    # -- emotions ----------------------------------------------------------
    def update_emotions(self, valence: float, potency: float, activation: float) -> None:
        """EPA update with inertia ψ (inputs in [-1, 1])."""
        psi = self.emotion_inertia
        self._psi = tuple(
            psi * old + (1.0 - psi) * new
            for old, new in zip(self._psi, (valence, potency, activation))
        )

    def emotions_now(self) -> tuple[float, float, float]:
        return self._psi

    # -- utility -------------------------------------------------------------
    def _shortfall_term(self, k: int, theta_k: float, emotion_eval: float) -> float:
        """Cobb–Douglas-ish shortfall utility for need k.

        Combines the action's trait-affinity θ_k(a) with the current
        need level N_k and the evaluation emotion E.
        """
        need_ratio = min(max(self._N[k] / max(self._n_scale[k], 1e-9), 0.0), 1.5)
        emo = 0.5 + 0.5 * max(-1.0, min(1.0, emotion_eval))  # E ∈ [0,1]
        base = (max(theta_k, 1e-9) ** self._g_exp[k]) * (need_ratio ** 0.5) * emo
        return min(base, 1.0)

    def cost(self, theta: Sequence[float], action_id: str = "") -> float:
        """Trait-conditioned cost C(θ, a): effort rises when the action
        demands traits the agent lacks (1 − θ̄ weighted by cost_coef)."""
        if not theta:
            return 0.0
        mismatch = sum(self._c[k % len(self._c)] * (1.0 - min(max(theta[k], 0.0), 1.0))
                       for k in range(min(len(theta), len(self._c))))
        return mismatch / max(len(self._c), 1)

    def utility(
        self,
        theta: Sequence[float],
        action_fit: Sequence[float] | None = None,
        action_id: str = "",
    ) -> float:
        """U_i(a) = Σ_k w_k·u_k − ρ·C(θ, a).

        `theta` = agent traits (5,); `action_fit` = per-need trait affinity
        of the action (defaults to theta itself).
        """
        fit = list(action_fit) if action_fit is not None else list(theta)
        eval_emotion = self._psi[0]
        total = 0.0
        for k in range(min(len(self._w), len(fit))):
            total += self._w[k] * self._shortfall_term(k, fit[k], eval_emotion)
        return total - self.rho * self.cost(theta, action_id)
