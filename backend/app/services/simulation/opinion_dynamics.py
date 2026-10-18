# backend/app/services/simulation/opinion_dynamics.py
"""
Opinion Dynamics & Cascade Point Process:
- Bounded Confidence Model (Deffuant & Hegselmann-Krause)
- Emotional Contagion (Valence & Arousal)
- Hawkes Self-Exciting Point Process untuk kedatangan interaksi dan viralitas.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple


class BoundedConfidenceModel:
    """Model dinamika opini Bounded Confidence (Deffuant & Hegselmann-Krause)."""

    def __init__(self, epsilon: float = 0.25, convergence_rate: float = 0.3):
        self.epsilon = epsilon
        self.convergence_rate = convergence_rate

    def deffuant_pairwise_step(
        self,
        opinion_i: float,
        opinion_j: float,
        epsilon: Optional[float] = None,
        mu: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Satu langkah interaksi pairwise Deffuant antar dua agen."""
        eps = epsilon if epsilon is not None else self.epsilon
        rate = mu if mu is not None else self.convergence_rate

        diff = abs(opinion_i - opinion_j)
        if diff <= eps:
            new_i = opinion_i + rate * (opinion_j - opinion_i)
            new_j = opinion_j + rate * (opinion_i - opinion_j)
            return (round(new_i, 4), round(new_j, 4))
        # Tidak ada konvergensi jika di luar batas toleransi
        return (opinion_i, opinion_j)

    def hegselmann_krause_step(
        self,
        opinions: List[float],
        epsilon: Optional[float] = None,
    ) -> List[float]:
        """Satu langkah sinkronisasi kelompok Hegselmann-Krause."""
        eps = epsilon if epsilon is not None else self.epsilon
        new_opinions = []

        for i, op_i in enumerate(opinions):
            # Temukan tetangga dalam rentang toleransi
            neighbors = [op_j for op_j in opinions if abs(op_i - op_j) <= eps]
            if neighbors:
                avg_op = sum(neighbors) / len(neighbors)
                new_opinions.append(round(avg_op, 4))
            else:
                new_opinions.append(op_i)

        return new_opinions


class EmotionalContagion:
    """Model transmisi emosi antar agen dalam jaringan sosial."""

    def __init__(self, contagion_rate: float = 0.2):
        self.contagion_rate = contagion_rate

    def update_emotion(
        self,
        receiver_valence: float,
        receiver_arousal: float,
        sender_valence: float,
        sender_arousal: float,
        susceptibility: float = 0.5,
    ) -> Tuple[float, float]:
        """Update valence [-1.0, 1.0] dan arousal [0.0, 1.0] penerima."""
        weight = self.contagion_rate * susceptibility

        new_val = receiver_valence + weight * (sender_valence - receiver_valence)
        new_aro = receiver_arousal + weight * (sender_arousal - receiver_arousal)

        # Clamping
        new_val = max(-1.0, min(1.0, round(new_val, 4)))
        new_aro = max(0.0, min(1.0, round(new_aro, 4)))
        return (new_val, new_aro)


class HawkesProcess:
    """Hawkes Self-Exciting Point Process untuk memodelkan ledakan interaksi komentar viral.
    lambda(t) = mu + sum_{t_i < t} alpha * exp(-beta * (t - t_i))
    """

    def __init__(self, mu: float = 0.5, alpha: float = 0.8, beta: float = 1.2):
        self.mu = max(0.01, mu)
        self.alpha = max(0.0, alpha)
        self.beta = max(0.01, beta)

    @property
    def branching_ratio(self) -> float:
        """Rasio percabangan (alpha / beta). Subkritis bila < 1.0."""
        return self.alpha / self.beta

    def intensity(self, t: float, history: List[float]) -> float:
        """Menghitung intensitas kedatangan instan lambda(t)."""
        val = self.mu
        for t_i in history:
            if t_i < t:
                val += self.alpha * math.exp(-self.beta * (t - t_i))
        return val

    def simulate_arrivals(
        self,
        duration: float,
        seed: Optional[int] = None,
        max_events: int = 1000,
    ) -> List[float]:
        """Simulasi waktu kedatangan event menggunakan algoritma Ogata's Modified Thinning."""
        rng = random.Random(seed) if seed is not None else random
        events: List[float] = []
        t = 0.0

        while t < duration and len(events) < max_events:
            # Batas atas intensitas
            lambda_bar = self.intensity(t, events)
            # Waktu antar kedatangan eksponensial
            u1 = rng.random()
            if u1 <= 0.0:
                break
            delta = -math.log(u1) / lambda_bar
            t += delta

            if t >= duration:
                break

            # Tahap thinning
            lambda_t = self.intensity(t, events)
            u2 = rng.random()
            if u2 <= (lambda_t / lambda_bar):
                events.append(round(t, 4))

        return events
