"""
Unit & Sanity Test: Natural Indonesian Comment Algorithm & OASIS Calibration
Memverifikasi integrasi StyleRealizer, Few-Shot Corpus, Register Netizen,
Anti-Bot Guardrails, dan Konfigurasi Jadwal Netizen Indonesia (WIB UTC+7).
"""
import os
import sys

# Isolasi env agar tidak memanggil network/proxy eksternal saat unit test
os.environ["OPENAI_API_KEY"] = "mock-key-for-test"
os.environ.pop("OPENAI_API_BASE_URL", None)
os.environ.pop("LLM_BASE_URL", None)
os.environ.pop("LLM_BOOST_BASE_URL", None)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
scripts_dir = os.path.join(backend_dir, "scripts")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from app.services.simulation.style_realizer import style_realizer, StyleRealizer, FEW_SHOT_CORPUS
from app.services.simulation_config_generator import (
    INDONESIA_WIB_TIMEZONE_CONFIG,
    SimulationConfigGenerator,
)
from oasis.social_platform.config.user import UserInfo
from oasis.social_agent.agent import SocialAgent
from oasis.social_agent.agent_graph import AgentGraph
import run_parallel_simulation


def test_few_shot_corpus_and_slangs():
    """Verifikasi bahwa bank few-shot memuat slang otentik netizen Indonesia."""
    all_responses = " ".join([s.response.lower() for s in FEW_SHOT_CORPUS])

    assert "bener bgt sih" in all_responses, "Slang 'bener bgt sih' harus ada dalam korpus"
    assert "literally" in all_responses, "Slang 'literally' harus ada dalam korpus"
    assert "jujurly" in all_responses, "Slang 'jujurly' harus ada dalam korpus"
    assert "gokil" in all_responses, "Slang 'gokil' harus ada dalam korpus"
    assert "wkwk" in all_responses, "Slang 'wkwk' harus ada dalam korpus"
    assert "ya allah" in all_responses, "Slang 'ya Allah' harus ada dalam korpus"
    assert "amit-amit" in all_responses, "Slang 'amit-amit' harus ada dalam korpus"
    assert "sesak lgi liat kmu dek" in all_responses, "Frasa 'sesak lgi liat kmu dek' harus ada dalam korpus"
    assert "beneran parah bgt" in all_responses, "Frasa 'beneran parah bgt' harus ada dalam korpus"
    print("[PASS] test_few_shot_corpus_and_slangs: Semua slang otentik terverifikasi.")


def test_determine_register_heuristics():
    """Verifikasi heuristik penentuan register berdasarkan profil."""
    assert style_realizer.determine_register("Profesor dan Dosen Peneliti AI") == "formal"
    assert style_realizer.determine_register("Anak Jaksel gaul kerja di startup SCBD") == "gaul jaksel"
    assert style_realizer.determine_register("Netizen kritis sarkas suka nyindir pejabat") == "sarkastik"
    assert style_realizer.determine_register("Warga biasa suka jajan cilok") == "kasual santai"
    print("[PASS] test_determine_register_heuristics: Deteksi register bahasa akurat.")


def test_style_guidance_anti_bot_and_meta():
    """Verifikasi panduan gaya bahasa memuat guardrail anti-bot dan anti-meta."""
    guidance = style_realizer.format_style_guidance("kasual santai", platform="twitter")

    assert "DILARANG KERAS menggunakan frasa meta AI" in guidance
    assert "Sebagai AI..." in guidance
    assert "bener bgt sih" in guidance or "wkwk" in guidance
    assert "TWITTER" in guidance
    print("[PASS] test_style_guidance_anti_bot_and_meta: Guardrail anti-bot & anti-meta terverifikasi.")


def test_user_info_monkey_patch():
    """Verifikasi bahwa monkey-patch UserInfo menyuntikkan gaya natural ke system message."""
    user = UserInfo(
        name="Rian_Jaksel",
        description="Product Manager startup fintech di Sudirman",
        profile={"other_info": {"user_profile": "Gen-Z hustle culture SCBD"}},
        recsys_type="twitter",
    )

    run_parallel_simulation.patch_oasis_user_info_for_indonesian_style()

    tw_msg = user.to_twitter_system_message()
    assert "ATURAN GAYA KOMUNIKASI & REGISTER BAHASA NETIZEN INDONESIA" in tw_msg
    assert "GAUL JAKSEL" in tw_msg or "KASUAL SANTAI" in tw_msg
    assert "Contoh Komentar Riil Netizen Indonesia" in tw_msg

    user.recsys_type = "reddit"
    red_msg = user.to_reddit_system_message()
    assert "ATURAN GAYA KOMUNIKASI & REGISTER BAHASA NETIZEN INDONESIA (REDDIT)" in red_msg
    print("[PASS] test_user_info_monkey_patch: Monkey-patch UserInfo sukses menyuntikkan prompt natural.")


def test_social_agent_memory_enrichment():
    """Verifikasi bahwa SocialAgent memory terisi system message yang diperkaya."""
    user = UserInfo(
        name="Pak_Bambang",
        description="Akademisi dan Dosen Kebijakan Publik",
        profile={"other_info": {"user_profile": "Peneliti tata kelola pemerintahan"}},
        recsys_type="twitter",
    )
    graph = AgentGraph()
    agent = SocialAgent(agent_id=0, user_info=user, agent_graph=graph, model=None)

    graph.add_agent(agent)
    run_parallel_simulation.enrich_social_agents_with_style(graph, platform="twitter")

    records, _ = agent.memory.get_context()
    assert len(records) > 0
    sys_record = records[0]
    assert sys_record["role"] == "system"
    assert "ATURAN GAYA KOMUNIKASI & REGISTER BAHASA NETIZEN INDONESIA" in sys_record["content"]
    assert "FORMAL" in sys_record["content"]
    print("[PASS] test_social_agent_memory_enrichment: Dual-layer enrichment ke SocialAgent memory valid.")


def test_indonesia_wib_timezone_config():
    """Verifikasi jadwal netizen Indonesia WIB (UTC+7)."""
    assert INDONESIA_WIB_TIMEZONE_CONFIG["dead_hours"] == [0, 1, 2, 3, 4, 5]
    assert INDONESIA_WIB_TIMEZONE_CONFIG["morning_hours"] == [6, 7, 8]
    assert INDONESIA_WIB_TIMEZONE_CONFIG["lunch_hours"] == [12, 13]
    assert INDONESIA_WIB_TIMEZONE_CONFIG["peak_hours"] == [19, 20, 21, 22]

    cfg_gen = SimulationConfigGenerator(model_name="gpt-4o-mini")
    default_cfg = cfg_gen._get_default_time_config(num_entities=30)
    assert default_cfg["peak_hours"] == [19, 20, 21, 22]
    assert default_cfg["morning_hours"] == [6, 7, 8]
    assert default_cfg["lunch_hours"] == [12, 13]
    assert "WIB (UTC+7)" in default_cfg["reasoning"]
    print("[PASS] test_indonesia_wib_timezone_config: Konfigurasi jadwal WIB (UTC+7) valid.")


def test_karhutla_and_platform_adaptation():
    """Verifikasi dataset Karhutla dan adaptasi lintas platform (TikTok, LinkedIn, Reddit)."""
    # TikTok
    tiktok_prompt = style_realizer.build_natural_system_prompt(
        base_prompt="You are a social agent",
        register="kasual santai",
        platform="tiktok",
        topic="karhutla_kabut_asap",
    )
    assert "TIKTOK" in tiktok_prompt
    assert "ya Allah" in tiktok_prompt or "amit-amit" in tiktok_prompt
    assert "1-2 kalimat" in tiktok_prompt

    # LinkedIn
    linkedin_prompt = style_realizer.build_natural_system_prompt(
        base_prompt="You are a social agent",
        register="formal",
        platform="linkedin",
        topic="karhutla_kabut_asap",
    )
    assert "LINKEDIN" in linkedin_prompt
    assert "ESG" in linkedin_prompt
    assert "profesional" in linkedin_prompt.lower()

    # Reddit
    reddit_prompt = style_realizer.build_natural_system_prompt(
        base_prompt="You are a social agent",
        register="sarkastik",
        platform="reddit",
        topic="karhutla_kabut_asap",
    )
    assert "REDDIT" in reddit_prompt
    assert "argumentatif" in reddit_prompt.lower()
    print("[PASS] test_karhutla_and_platform_adaptation: Karhutla & adaptasi platform terverifikasi.")


if __name__ == "__main__":
    test_few_shot_corpus_and_slangs()
    test_determine_register_heuristics()
    test_style_guidance_anti_bot_and_meta()
    test_karhutla_and_platform_adaptation()
    test_user_info_monkey_patch()
    test_social_agent_memory_enrichment()
    test_indonesia_wib_timezone_config()
    print("\nALL SANITY TESTS PASSED SUCCESSFULLY!")
