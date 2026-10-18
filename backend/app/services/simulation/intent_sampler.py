# backend/app/services/simulation/intent_sampler.py
"""
Taksonomi Intent 7-Kategori & Sampling Distribusi Multinomial Empiris Dataset B:
1. Agree/Support
2. Disagree/Counter
3. Sarcasm/Meme
4. Clarification/Question
5. Tangential/Derail
6. Emotional Outburst
7. Nuanced Synthesis
"""
from __future__ import annotations

from enum import Enum
import random
from typing import Dict, List, Optional

from app.services.simulation.persona_store import Persona


class IntentType(str, Enum):
    AGREE_SUPPORT = "Agree/Support"
    DISAGREE_COUNTER = "Disagree/Counter"
    SARCASM_MEME = "Sarcasm/Meme"
    CLARIFICATION_QUESTION = "Clarification/Question"
    TANGENTIAL_DERAIL = "Tangential/Derail"
    EMOTIONAL_OUTBURST = "Emotional Outburst"
    NUANCED_SYNTHESIS = "Nuanced Synthesis"


# Baseline probabilitas empiris dari Dataset B
EMPIRICAL_DATASET_B_PRIORS: Dict[IntentType, float] = {
    IntentType.AGREE_SUPPORT: 0.28,
    IntentType.DISAGREE_COUNTER: 0.24,
    IntentType.SARCASM_MEME: 0.16,
    IntentType.CLARIFICATION_QUESTION: 0.10,
    IntentType.TANGENTIAL_DERAIL: 0.08,
    IntentType.EMOTIONAL_OUTBURST: 0.09,
    IntentType.NUANCED_SYNTHESIS: 0.05,
}


class IntentSampler:
    """Sampler intent percakapan berbasis prior empiris dan modulasi psikometrik."""

    def __init__(self, base_priors: Optional[Dict[IntentType, float]] = None):
        self.base_priors = base_priors or EMPIRICAL_DATASET_B_PRIORS.copy()

    def get_intent_distribution(
        self,
        persona: Optional[Persona] = None,
        content_stance: float = 0.0,
    ) -> Dict[IntentType, float]:
        """Menghitung distribusi probabilitas terbobot berdasarkan karakteristik persona."""
        dist = self.base_priors.copy()

        if persona is not None:
            # 1. Modulasi Agreeableness & Neuroticism
            agree_mod = (persona.agreeableness - 0.5) * 0.20
            neuro_mod = (persona.neuroticism - 0.5) * 0.15
            anger_mod = (persona.baseline_anger - 0.2) * 0.25
            openness_mod = (persona.openness - 0.5) * 0.15

            dist[IntentType.AGREE_SUPPORT] = max(0.02, dist[IntentType.AGREE_SUPPORT] + agree_mod - anger_mod)
            dist[IntentType.DISAGREE_COUNTER] = max(0.02, dist[IntentType.DISAGREE_COUNTER] - agree_mod + anger_mod)
            dist[IntentType.EMOTIONAL_OUTBURST] = max(0.01, dist[IntentType.EMOTIONAL_OUTBURST] + neuro_mod + anger_mod)
            dist[IntentType.NUANCED_SYNTHESIS] = max(0.01, dist[IntentType.NUANCED_SYNTHESIS] + openness_mod)
            dist[IntentType.CLARIFICATION_QUESTION] = max(0.02, dist[IntentType.CLARIFICATION_QUESTION] + 0.5 * openness_mod)

            # 2. Modulasi register bahasa
            if persona.language_register == "sarkastik":
                dist[IntentType.SARCASM_MEME] += 0.15
            elif persona.language_register == "gaul jaksel":
                dist[IntentType.SARCASM_MEME] += 0.05
                dist[IntentType.TANGENTIAL_DERAIL] += 0.03

            # 3. Pengaruh polarisasi sikap (stance alignment)
            # Jika user punya affinity pada topik, hitung delta terhadap stance konten
            persona_affinity = persona.issue_affinity.get("kebijakan_publik", 0.0)
            stance_diff = abs(persona_affinity - content_stance)
            if stance_diff > 0.8:
                dist[IntentType.DISAGREE_COUNTER] += 0.15
                dist[IntentType.EMOTIONAL_OUTBURST] += 0.05
            elif stance_diff < 0.3:
                dist[IntentType.AGREE_SUPPORT] += 0.15

        # Normalisasi ke sum 1.0
        total = sum(dist.values())
        return {k: v / total for k, v in dist.items()}

    def sample_intent(
        self,
        persona: Optional[Persona] = None,
        content_stance: float = 0.0,
        seed: Optional[int] = None,
    ) -> IntentType:
        """Sample satu intent acak menurut distribusi multinomial yang telah dimodulasi."""
        rng = random.Random(seed) if seed is not None else random
        dist = self.get_intent_distribution(persona, content_stance)

        population = list(dist.keys())
        weights = list(dist.values())

        chosen = rng.choices(population, weights=weights, k=1)[0]
        return chosen
