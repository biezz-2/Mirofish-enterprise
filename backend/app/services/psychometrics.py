"""
MiroFish Enterprise Whole Trait & Cybernetic Big Five Service (Agent 08: Divisi C)
Implementasi Whole Trait Theory (William Fleeson) dengan density distribution:
s = trait + noise (fluktuasi keadaan kepribadian di sekitar mean).
Dan Cybernetic Big Five Theory (Colin DeYoung) memetakan Big Five ke fungsi regulasi adaptif:
- O (Openness/Intellect): Eksplorasi kognitif dan persepsi
- C (Conscientiousness): Regulasi dan perlindungan target/tujuan
- E (Extraversion): Sensitivitas ganjaran (reward engagement)
- A (Agreeableness): Koordinasi sosial altruistik
- N (Neuroticism): Deteksi ancaman dan kecemasan
"""

import random
import math
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class BigFiveTrait(BaseModel):
    openness: float = Field(default=0.5, ge=0.0, le=1.0)
    conscientiousness: float = Field(default=0.5, ge=0.0, le=1.0)
    extraversion: float = Field(default=0.5, ge=0.0, le=1.0)
    agreeableness: float = Field(default=0.5, ge=0.0, le=1.0)
    neuroticism: float = Field(default=0.5, ge=0.0, le=1.0)

class PersonalityState(BaseModel):
    state_openness: float
    state_conscientiousness: float
    state_extraversion: float
    state_agreeableness: float
    state_neuroticism: float
    exploration_drive: float
    goal_persistence: float
    reward_sensitivity: float
    social_trust: float
    threat_sensitivity: float

class PsychometricsEngine:
    """Simulates Fleeson Whole Trait density distribution & DeYoung Cybernetics."""

    def __init__(self, sigma_noise: float = 0.08):
        self.sigma_noise = sigma_noise

    def sample_state(self, trait: BigFiveTrait) -> PersonalityState:
        """
        Menerapkan Whole Trait Fleeson: s = mean + Gaussian noise,
        dibatasi dalam rentang [0.0, 1.0].
        """
        def sample_var(val: float) -> float:
            noise = random.gauss(0.0, self.sigma_noise)
            return max(0.0, min(1.0, val + noise))

        s_o = sample_var(trait.openness)
        s_c = sample_var(trait.conscientiousness)
        s_e = sample_var(trait.extraversion)
        s_a = sample_var(trait.agreeableness)
        s_n = sample_var(trait.neuroticism)

        # DeYoung Cybernetic Function Mapping
        return PersonalityState(
            state_openness=s_o,
            state_conscientiousness=s_c,
            state_extraversion=s_e,
            state_agreeableness=s_a,
            state_neuroticism=s_n,
            exploration_drive=round(s_o * 1.2, 3),
            goal_persistence=round(s_c * 1.1, 3),
            reward_sensitivity=round(s_e * 1.3, 3),
            social_trust=round(s_a * 1.0, 3),
            threat_sensitivity=round(s_n * 1.4, 3)
        )

    def sample_distribution(self, trait: BigFiveTrait, n_samples: int = 1000) -> Dict[str, float]:
        """Uji stabilitas statistik density distribution Fleeson."""
        o_vals = [self.sample_state(trait).state_openness for _ in range(n_samples)]
        mean_o = sum(o_vals) / n_samples
        diff = abs(mean_o - trait.openness)
        return {
            "mean": mean_o,
            "expected": trait.openness,
            "deviation": diff,
            "is_stable": diff < 0.1
        }
