# backend/app/services/simulation/noise_layer.py
"""
Noise Layer: Deterministic Post-LLM Noise Injection
Menambahkan ketidaksempurnaan realistis pada teks komentar:
- Singkatan internet Indonesia (yg, byk, gak, bgt, tp, klo, dgn, udh, skrg, gmn)
- Typo rate terkontrol (1-3% transposisi/swap tombol tetangga QWERTY)
- Punctuation quirks (koma/titik ganda ,, .., huruf kapital awal hilang)
- Dialek/slang regional mix (Jaksel, Jawa, Sunda, Banjar)
- Variasi panjang kata / determinisme berbasis seed.
"""
from __future__ import annotations

import hashlib
import random
import re
from typing import Dict, List, Optional

from app.services.simulation.persona_store import Persona

QWERTY_NEIGHBORS: Dict[str, str] = {
    "a": "sqwz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wsdr",
    "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn",
    "k": "jiol", "l": "kop", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu", "z": "asx",
}

INDONESIAN_ABBREVIATIONS: Dict[str, str] = {
    "yang": "yg",
    "banyak": "byk",
    "tidak": "gak",
    "nggak": "gak",
    "banget": "bgt",
    "tetapi": "tp",
    "tapi": "tp",
    "kalau": "klo",
    "kalo": "klo",
    "dengan": "dgn",
    "sudah": "udh",
    "udah": "udh",
    "sekarang": "skrg",
    "bagaimana": "gmn",
    "gimana": "gmn",
    "bukan": "bkn",
    "bisa": "bs",
    "karena": "krn",
    "saja": "aja",
}

REGIONAL_PARTICLES: Dict[str, List[str]] = {
    "Jabodetabek": ["sih", "nih", "tuh", "deh"],
    "gaul jaksel": ["which is", "literally", "jujurly", "honestly"],
    "Jawa Barat": ["teh", "mah", "atuh", "euy"],
    "Jawa Timur": ["rek", "lho", "tenan", "to"],
    "Jawa Tengah": ["lho", "to", "njih", "je"],
    "Kalimantan Timur": ["pang", "nah", "jua", "am"],
}


class NoiseInjector:
    """Injektor noise realistis pasca-generasi LLM."""

    def __init__(self, default_typo_rate: float = 0.02):
        self.default_typo_rate = max(0.01, min(default_typo_rate, 0.05))

    def _get_seed(self, text: str, explicit_seed: Optional[int] = None) -> int:
        if explicit_seed is not None:
            return explicit_seed
        # Seed deterministik dari hash teks
        return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)

    def apply_abbreviations(self, text: str, rng: random.Random, prob: float = 0.70) -> str:
        """Mengganti kata baku dengan singkatan medsos Indonesia."""
        words = text.split()
        new_words = []
        for w in words:
            # Bersihkan tanda baca tepi untuk pencocokan kata
            cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()
            if cleaned in INDONESIAN_ABBREVIATIONS and rng.random() < prob:
                replacement = INDONESIAN_ABBREVIATIONS[cleaned]
                # Pertahankan tanda baca
                prefix = re.match(r"^[^\w]+", w)
                suffix = re.search(r"[^\w]+$", w)
                p_str = prefix.group(0) if prefix else ""
                s_str = suffix.group(0) if suffix else ""
                new_words.append(f"{p_str}{replacement}{s_str}")
            else:
                new_words.append(w)
        return " ".join(new_words)

    def apply_typos(self, text: str, rng: random.Random, rate: float = 0.02) -> str:
        """Menginjeksi kesalahan ketik QWERTY swap atau transposisi."""
        chars = list(text)
        n = len(chars)
        if n < 4:
            return text

        num_typos = max(1, int(round(n * rate))) if rate > 0 else 0
        indices = rng.sample(range(n), min(num_typos, n))

        for idx in indices:
            c = chars[idx]
            c_lower = c.lower()
            if c_lower in QWERTY_NEIGHBORS:
                neighbor = rng.choice(QWERTY_NEIGHBORS[c_lower])
                chars[idx] = neighbor.upper() if c.isupper() else neighbor
            elif idx < n - 1 and chars[idx].isalnum() and chars[idx + 1].isalnum():
                # Transposisi karakter bersebelahan
                chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]

        return "".join(chars)

    def apply_punctuation_quirks(self, text: str, rng: random.Random) -> str:
        """Menambahkan kebiasaan tanda baca medsos (, , ganda, hilangnya huruf kapital)."""
        res = text

        # 1. Hilangkan huruf kapital di awal (common social media lowercasing)
        if len(res) > 0 and rng.random() < 0.65:
            res = res[0].lower() + res[1:]

        # 2. Quirks tanda baca: koma ganda ',,' atau tanda tanya ganda '??'
        if "," in res and rng.random() < 0.35:
            res = res.replace(",", ",,", 1)
        if "?" in res and rng.random() < 0.40:
            res = res.replace("?", "??", 1)
        if "!" in res and rng.random() < 0.40:
            res = res.replace("!", "!!", 1)

        return res

    def apply_regional_particles(
        self,
        text: str,
        persona: Optional[Persona],
        rng: random.Random,
    ) -> str:
        """Menyisipkan partikel atau slang khas daerah/register."""
        if not persona:
            return text

        particles: List[str] = []
        if persona.language_register == "gaul jaksel":
            particles = REGIONAL_PARTICLES["gaul jaksel"]
        elif persona.domicile in REGIONAL_PARTICLES:
            particles = REGIONAL_PARTICLES[persona.domicile]

        if particles and rng.random() < 0.45:
            particle = rng.choice(particles)
            # Selipkan di akhir kalimat atau sebelum tanda baca
            words = text.split()
            if words:
                words.append(particle)
                return " ".join(words)

        return text

    def inject_noise(
        self,
        text: str,
        persona: Optional[Persona] = None,
        typo_rate: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> str:
        """Eksekusi pipeline deterministik noise injection."""
        if not text or not text.strip():
            return text

        effective_seed = self._get_seed(text, seed)
        rng = random.Random(effective_seed)
        eff_typo_rate = typo_rate if typo_rate is not None else self.default_typo_rate

        # Pipeline transformasi
        t1 = self.apply_abbreviations(text, rng, prob=0.75)
        t2 = self.apply_regional_particles(t1, persona, rng)
        t3 = self.apply_punctuation_quirks(t2, rng)
        t4 = self.apply_typos(t3, rng, rate=eff_typo_rate)

        return t4


def apply_noise(
    text: str,
    persona: Optional[Persona] = None,
    typo_rate: float = 0.02,
    seed: Optional[int] = None,
) -> str:
    """Fungsi pembungkus praktis untuk apply noise."""
    injector = NoiseInjector(default_typo_rate=typo_rate)
    return injector.inject_noise(text=text, persona=persona, typo_rate=typo_rate, seed=seed)
