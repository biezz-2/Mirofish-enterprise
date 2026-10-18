# backend/app/services/simulation/persona_store.py
"""
Persona Store untuk Multi-Dimensi Atribut:
- Big Five (OCEAN: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Domisili / regional (Jabodetabek, Jawa Barat, Jawa Timur, Kalimantan Timur, Sumatera Utara, Bali, dll.)
- Rentang usia ("18-24", "25-34", "35-49", "50+")
- Register bahasa ("formal", "kasual santai", "gaul jaksel", "sarkastik")
- Frekuensi emoji ("low", "medium", "high")
- Log-normal parameters untuk panjang komentar (mu, sigma)
- Baseline anger (0.0 - 1.0)
- Keterikatan pada isu/event (issue_affinity).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Dict, List, Optional

REGIONAL_DOMICILES = [
    "Jabodetabek",
    "Jawa Barat",
    "Jawa Timur",
    "Jawa Tengah",
    "Kalimantan Timur",
    "Sumatera Utara",
    "Sulawesi Selatan",
    "Bali",
]

AGE_RANGES = ["18-24", "25-34", "35-49", "50+"]
LANGUAGE_REGISTERS = ["formal", "kasual santai", "gaul jaksel", "sarkastik"]
EMOJI_FREQUENCIES = ["low", "medium", "high"]


@dataclass
class Persona:
    """Representasi agen berspesifikasi psikometrik & demografis lengkap."""
    persona_id: str
    name: str = "Agen Anonim"
    # Big Five (OCEAN) [0.0 - 1.0]
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Demografis & Komunikasi
    domicile: str = "Jabodetabek"
    age_range: str = "25-34"
    language_register: str = "kasual santai"
    emoji_frequency: str = "medium"

    # Log-normal parameters untuk panjang komentar (kata)
    comment_length_mu: float = 3.2
    comment_length_sigma: float = 0.5

    # Sikap emosional & isu
    baseline_anger: float = 0.2
    issue_affinity: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "ocean": {
                "openness": self.openness,
                "conscientiousness": self.conscientiousness,
                "extraversion": self.extraversion,
                "agreeableness": self.agreeableness,
                "neuroticism": self.neuroticism,
            },
            "domicile": self.domicile,
            "age_range": self.age_range,
            "language_register": self.language_register,
            "emoji_frequency": self.emoji_frequency,
            "comment_length_params": {
                "mu": self.comment_length_mu,
                "sigma": self.comment_length_sigma,
            },
            "baseline_anger": self.baseline_anger,
            "issue_affinity": self.issue_affinity,
        }


class PersonaStore:
    """Manajer koleksi dan generator profil persona."""

    def __init__(self):
        self._personas: Dict[str, Persona] = {}

    def register(self, persona: Persona) -> None:
        self._personas[persona.persona_id] = persona

    def get(self, persona_id: str) -> Optional[Persona]:
        return self._personas.get(persona_id)

    def generate_random_persona(
        self,
        persona_id: str,
        name: Optional[str] = None,
        seed: Optional[int] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Persona:
        """Menghasilkan persona realistis dengan seed deterministik jika diberikan."""
        rng = random.Random(seed) if seed is not None else random

        # Log-normal mu dipengaruhi ekstraversi & keterbukaan
        e_val = round(rng.uniform(0.1, 0.9), 2)
        o_val = round(rng.uniform(0.1, 0.9), 2)
        mu = round(2.5 + 1.2 * o_val + 0.5 * e_val, 2)
        sigma = round(rng.uniform(0.3, 0.7), 2)

        domicile = rng.choice(REGIONAL_DOMICILES)
        age_range = rng.choice(AGE_RANGES)

        # Register bahasa bias usia
        if age_range in ["18-24", "25-34"] and domicile == "Jabodetabek":
            register_choices = ["gaul jaksel", "kasual santai", "sarkastik"]
        elif age_range == "50+":
            register_choices = ["formal", "kasual santai"]
        else:
            register_choices = LANGUAGE_REGISTERS
        language_register = rng.choice(register_choices)

        persona = Persona(
            persona_id=persona_id,
            name=name or f"Warga_{persona_id}",
            openness=o_val,
            conscientiousness=round(rng.uniform(0.1, 0.9), 2),
            extraversion=e_val,
            agreeableness=round(rng.uniform(0.1, 0.9), 2),
            neuroticism=round(rng.uniform(0.1, 0.9), 2),
            domicile=domicile,
            age_range=age_range,
            language_register=language_register,
            emoji_frequency=rng.choice(EMOJI_FREQUENCIES),
            comment_length_mu=mu,
            comment_length_sigma=sigma,
            baseline_anger=round(rng.uniform(0.05, 0.50), 2),
            issue_affinity={"kebijakan_publik": round(rng.uniform(-1.0, 1.0), 2)},
        )

        if overrides:
            for k, v in overrides.items():
                if hasattr(persona, k):
                    setattr(persona, k, v)

        self._personas[persona_id] = persona
        return persona

    def export_all(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._personas.values()]

    def count(self) -> int:
        return len(self._personas)
