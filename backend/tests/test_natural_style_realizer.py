import pytest
from app.services.simulation.style_realizer import (
    StyleRealizer,
    style_realizer,
    FEW_SHOT_CORPUS,
    ConversationSample,
    PLATFORM_STYLE_RULES,
)
from app.services.simulation_config_generator import INDONESIA_WIB_TIMEZONE_CONFIG


class DummyUserInfo:
    def __init__(self, description="Mahasiswa Jaksel suka kopi dan start-up", personality="Sarcastic tech bro", traits=None):
        self.description = description
        self.personality = personality
        self.traits = traits or ["sarcastic", "gaul", "witty"]


def test_few_shot_corpus_coverage():
    """Memastikan corpus memuat 4 register utama sesuai spesifikasi Notion."""
    registers_in_corpus = {s.register for s in FEW_SHOT_CORPUS}
    for reg in ["formal", "kasual santai", "gaul jaksel", "sarkastik"]:
        assert reg in registers_in_corpus
        count = sum(1 for s in FEW_SHOT_CORPUS if s.register == reg)
        assert count >= 4


def test_karhutla_netizen_slang_dataset():
    """Memverifikasi kehadiran dataset Notion Karhutla dan frasa slang lisan otentik netizen."""
    corpus_text = " ".join([s.response.lower() + " " + s.context.lower() for s in FEW_SHOT_CORPUS])

    # Frasa wajib spesifik dari user
    assert "ya allah" in corpus_text
    assert "amit-amit" in corpus_text
    assert "sesak lgi liat kmu dek" in corpus_text
    assert "beneran parah bgt" in corpus_text

    # Topik karhutla_kabut_asap di seluruh 4 register
    karhutla_samples = [s for s in FEW_SHOT_CORPUS if s.topic == "karhutla_kabut_asap"]
    assert len(karhutla_samples) >= 8
    karhutla_registers = {s.register for s in karhutla_samples}
    assert {"formal", "kasual santai", "gaul jaksel", "sarkastik"}.issubset(karhutla_registers)


def test_platform_style_rules_differentiation():
    """Memverifikasi diferensiasi platform: TikTok santai/lisan, LinkedIn profesional, Reddit argumentatif."""
    # TikTok
    tiktok_guidance = PLATFORM_STYLE_RULES["tiktok"]["guidance"]
    assert "TikTok" in tiktok_guidance
    assert "ya Allah" in tiktok_guidance or "amit-amit" in tiktok_guidance
    assert "1-2 kalimat" in tiktok_guidance

    # LinkedIn
    linkedin_guidance = PLATFORM_STYLE_RULES["linkedin"]["guidance"]
    assert "LinkedIn" in linkedin_guidance
    assert "ESG" in linkedin_guidance
    assert "profesional" in linkedin_guidance.lower()

    # Reddit
    reddit_guidance = PLATFORM_STYLE_RULES["reddit"]["guidance"]
    assert "Reddit" in reddit_guidance
    assert "argumentatif" in reddit_guidance.lower()
    assert "AQI" in reddit_guidance or "ISPU" in reddit_guidance


def test_determine_register():
    """Memastikan deteksi register berdasarkan profil kepribadian akurat."""
    realizer = StyleRealizer()

    # Jaksel profile
    jaksel_user = DummyUserInfo(description="Anak Jaksel chill", personality="gaul jaksel mixing english")
    assert realizer.determine_register(jaksel_user) == "gaul jaksel"

    # Sarcastic profile
    sarcastic_user = DummyUserInfo(description="Pengamat sinis", personality="Cynical and sarcastic", traits=["sarkastik"])
    assert realizer.determine_register(sarcastic_user) == "sarkastik"

    # Formal profile
    formal_user = DummyUserInfo(description="Pejabat kementerian", personality="Birokrat formal berwibawa", traits=["formal"])
    assert realizer.determine_register(formal_user) == "formal"


def test_build_natural_system_prompt():
    """Memastikan prompt akhir memuat panduan gaya bahasa netizen Indonesia dan platform context."""
    base_prompt = "You are a social media user."
    user = DummyUserInfo()
    prompt = style_realizer.build_natural_system_prompt(
        base_prompt=base_prompt,
        user_info=user,
        platform="tiktok"
    )
    assert base_prompt in prompt
    assert "ATURAN GAYA KOMUNIKASI & REGISTER BAHASA NETIZEN INDONESIA (TIKTOK)" in prompt
    assert "Contoh Komentar Riil Netizen Indonesia" in prompt
    assert "TikTok" in prompt


def test_indonesia_wib_timezone_config():
    """Memastikan konfigurasi zona waktu Indonesia (WIB UTC+7) diterapkan."""
    assert INDONESIA_WIB_TIMEZONE_CONFIG["peak_hours"] == [19, 20, 21, 22]
    assert INDONESIA_WIB_TIMEZONE_CONFIG["lunch_hours"] == [12, 13]
    assert INDONESIA_WIB_TIMEZONE_CONFIG["dead_hours"] == [0, 1, 2, 3, 4, 5]
    assert INDONESIA_WIB_TIMEZONE_CONFIG["activity_multipliers"]["peak"] == 1.6
