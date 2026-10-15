"""
MiroFish Enterprise Humanoid ODE & Ekman Needs Engine (Agent 09: Divisi C)
Model System 1 Humanoid:
- ODE Peluruhan Kebutuhan: dN/dt = -lambda * N (energi, sosialisasi, stimulasi)
- 7 Emosi Dasar Paul Ekman: Joy, Sadness, Anger, Fear, Disgust, Surprise, Trust
- Skala Kedekatan Sosial: 0 s.d. 30 (Dunbar-inspired tie strength)
- Jam Sirkadian Aktivitas: Fluktuasi probabilitas aksi berdasarkan jam (0-23)
"""

import math
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class EkmanEmotions(BaseModel):
    joy: float = Field(default=0.5, ge=0.0, le=1.0)
    sadness: float = Field(default=0.1, ge=0.0, le=1.0)
    anger: float = Field(default=0.1, ge=0.0, le=1.0)
    fear: float = Field(default=0.1, ge=0.0, le=1.0)
    disgust: float = Field(default=0.05, ge=0.0, le=1.0)
    surprise: float = Field(default=0.2, ge=0.0, le=1.0)
    trust: float = Field(default=0.6, ge=0.0, le=1.0)

class HumanoidNeedsState(BaseModel):
    energy: float = Field(default=1.0, ge=0.0, le=1.0)
    social_drive: float = Field(default=0.8, ge=0.0, le=1.0)
    stimulation: float = Field(default=0.7, ge=0.0, le=1.0)
    social_closeness: float = Field(default=15.0, ge=0.0, le=30.0)
    emotions: EkmanEmotions = Field(default_factory=EkmanEmotions)
    circadian_factor: float = 1.0

class HumanoidNeedsEngine:
    """Simulates homeostatic needs decay ODE and Ekman emotional dynamics."""

    def __init__(self, lambda_energy: float = 0.05, lambda_social: float = 0.03):
        self.lambda_energy = lambda_energy
        self.lambda_social = lambda_social

    def step_ode_decay(self, state: HumanoidNeedsState, dt_hours: float = 1.0) -> HumanoidNeedsState:
        """
        Solusi analitik ODE dN/dt = -lambda * N:
        N(t + dt) = N(t) * exp(-lambda * dt)
        """
        new_energy = state.energy * math.exp(-self.lambda_energy * dt_hours)
        new_social = state.social_drive * math.exp(-self.lambda_social * dt_hours)
        new_stim = max(0.1, state.stimulation * math.exp(-0.04 * dt_hours))

        return HumanoidNeedsState(
            energy=round(max(0.01, new_energy), 4),
            social_drive=round(max(0.01, new_social), 4),
            stimulation=round(new_stim, 4),
            social_closeness=state.social_closeness,
            emotions=state.emotions,
            circadian_factor=state.circadian_factor
        )

    def compute_circadian_factor(self, hour_of_day: int) -> float:
        """
        Kurva sirkadian 24-jam (puncak pukul 10:00 & 20:00, terendah pukul 03:00-04:00).
        """
        h = hour_of_day % 24
        # Fungsi gelombang kosinus dengan dua puncak
        factor = 0.5 + 0.5 * math.sin((h - 6) / 24.0 * 2.0 * math.pi)
        if 1 <= h <= 5:
            factor *= 0.2  # Mode tidur
        return round(max(0.05, factor), 3)

    def calculate_post_probability(self, state: HumanoidNeedsState, hour: int) -> float:
        """
        Menghitung probabilitas agen melakukan posting / aktivitas produksi.
        Dipengaruhi oleh sisa energi, dorongan stimulasi, dan jam sirkadian.
        """
        circ = self.compute_circadian_factor(hour)
        prob = state.energy * 0.4 + state.social_drive * 0.3 + state.stimulation * 0.3
        return round(prob * circ, 4)
