# backend/tests/test_simulation_engine_v36.py
"""
Unit Tests Komprehensif untuk MiroFish Simulation Engine v3.6:
1. Pipeline 6-Tahap (Source, Hydrator, Filter, Scorer, Selector, SideEffect)
2. Platform Profile Store (Versioned YAML & Fallback)
3. Persona Store (OCEAN, Demografi, Register Bahasa)
4. Intent Sampler (7-Kategori & Modulasi Multinomial)
5. Style Realizer (Few-Shot Retrieval & Prompt Construction)
6. Noise Layer (Singkatan Indonesia & Typo QWERTY Deterministic)
7. Opinion Dynamics & Hawkes Process (Bounded Confidence & Self-Exciting Cascade)
8. Calibration Harness (90-9-1 Rule, Heavy-Tail, Diurnal Cycle)
9. Evaluation Suite & N-Gram Leakage Checker
10. Ethics Guard (Sandbox Lock, Mandatory is_synthetic, Watermark, Audit Log)
"""
from __future__ import annotations

import pytest

from app.services.simulation import (
    CandidateItem,
    FeedPipeline,
    PipelineContext,
    PlatformProfileStore,
    Persona,
    PersonaStore,
    IntentSampler,
    IntentType,
    StyleRealizer,
    NoiseInjector,
    apply_noise,
    BoundedConfidenceModel,
    EmotionalContagion,
    HawkesProcess,
    StylizedFactsValidator,
    EvaluationSuite,
    check_ngram_leakage,
    compute_ttr,
    EthicsGuard,
    SandboxViolationError,
    WATERMARK_TEXT,
)


# ============================================================================
# 1. TEST FEED PIPELINE (6 STAGES HOME-MIXER)
# ============================================================================
def test_feed_pipeline_six_stages():
    pipeline = FeedPipeline()
    ctx = PipelineContext(
        platform="x",
        user_id="user_test",
        user_network={"author_friend"},
        blocked_authors={"author_spammer"},
        slate_size=4,
    )

    candidates = [
        # In-network item
        CandidateItem(id="item_1", author_id="author_friend", text="Kabar baik hari ini", domain="news", features={"likes_count": 100}),
        # Out-network item
        CandidateItem(id="item_2", author_id="author_stranger_1", text="Opini publik terkini", domain="opini", features={"likes_count": 50}),
        # Toxic item (harus difilter)
        CandidateItem(id="item_3", author_id="author_toxic", text="Konten berbahaya", toxic_score=0.95),
        # Blocked author item (harus difilter)
        CandidateItem(id="item_4", author_id="author_spammer", text="Spam iklan"),
        # Duplikat item (harus difilter)
        CandidateItem(id="item_1", author_id="author_friend", text="Kabar baik hari ini duplikat"),
        # Out-network item lain
        CandidateItem(id="item_5", author_id="author_stranger_2", text="Perkembangan AI", domain="tech", features={"likes_count": 80}),
        # In-network item lain
        CandidateItem(id="item_6", author_id="author_friend", text="Diskusi santai malam", domain="lifestyle", features={"likes_count": 40}),
    ]

    selected = pipeline.run(candidates, ctx)

    # Verifikasi Stage 3: Item toxic, blocked, dan duplikat tidak boleh ada
    selected_ids = [c.id for c in selected]
    assert "item_3" not in selected_ids
    assert "item_4" not in selected_ids
    assert selected_ids.count("item_1") <= 1

    # Verifikasi Stage 4: Scorer mengisi predicted_scores dan final_score
    for item in selected:
        assert "p_like" in item.predicted_scores
        assert "p_retweet" in item.predicted_scores
        assert "p_reply" in item.predicted_scores
        assert item.final_score > 0.0

    # Verifikasi Stage 5: Slate size dihormati
    assert len(selected) <= ctx.slate_size

    # Verifikasi Stage 6: SideEffect mencatat impresi
    assert len(ctx.impressions) == len(selected)
    for s_id in selected_ids:
        assert s_id in ctx.seen_ids


# ============================================================================
# 2. TEST PLATFORM PROFILE STORE
# ============================================================================
def test_platform_profile_store():
    store = PlatformProfileStore()

    # Load profil X (termasuk alias twitter)
    prof_x = store.get_profile("x", version="2026-10")
    prof_tw = store.get_profile("twitter", version="2026-10")
    assert prof_x["platform"] == "x"
    assert prof_tw["platform"] == "x"
    assert prof_x["regimes"]["regular"]["max_chars"] == 280
    assert prof_x["regimes"]["premium"]["max_chars"] == 25000

    # Load profil Reddit
    prof_reddit = store.get_profile("reddit", version="2026-10")
    assert prof_reddit["karma_threshold"] == 50
    assert "subreddit_hierarchy" in prof_reddit

    # Load profil TikTok
    prof_tiktok = store.get_profile("tiktok", version="2026-10")
    assert prof_tiktok["watch_time_duration_weight"] == 0.50

    # Load profil Meta
    prof_meta = store.get_profile("meta", version="2026-10")
    assert "instagram" in prof_meta["sub_platforms"]

    # Test unknown platform fallback
    prof_unknown = store.get_profile("platform_fiktif_123")
    assert prof_unknown["platform"] == "platform_fiktif_123"
    assert "weights" in prof_unknown


# ============================================================================
# 3. TEST PERSONA STORE
# ============================================================================
def test_persona_store():
    store = PersonaStore()
    persona = store.generate_random_persona(
        persona_id="p_001",
        name="Budi Santoso",
        seed=42,
    )

    assert persona.persona_id == "p_001"
    assert 0.0 <= persona.openness <= 1.0
    assert 0.0 <= persona.conscientiousness <= 1.0
    assert persona.domicile in [
        "Jabodetabek", "Jawa Barat", "Jawa Timur", "Jawa Tengah",
        "Kalimantan Timur", "Sumatera Utara", "Sulawesi Selatan", "Bali"
    ]
    assert persona.language_register in ["formal", "kasual santai", "gaul jaksel", "sarkastik"]

    # Determinisme seed
    persona_2 = store.generate_random_persona(persona_id="p_002", seed=42)
    assert persona.openness == persona_2.openness
    assert persona.domicile == persona_2.domicile

    # Export dictionary
    d = persona.to_dict()
    assert d["ocean"]["openness"] == persona.openness
    assert "comment_length_params" in d


# ============================================================================
# 4. TEST INTENT SAMPLER
# ============================================================================
def test_intent_sampler():
    sampler = IntentSampler()

    # Pastikan 7 kategori intent terdaftar
    assert len(IntentType) == 7
    expected_intents = {
        "Agree/Support", "Disagree/Counter", "Sarcasm/Meme",
        "Clarification/Question", "Tangential/Derail",
        "Emotional Outburst", "Nuanced Synthesis"
    }
    assert {i.value for i in IntentType} == expected_intents

    # Sample intent dengan persona sarkastik
    persona_sarcastic = Persona(persona_id="p_sarc", language_register="sarkastik", agreeableness=0.1)
    dist = sampler.get_intent_distribution(persona_sarcastic)
    assert dist[IntentType.SARCASM_MEME] > 0.16  # boosted

    # Determinisme sample
    sampled_1 = sampler.sample_intent(persona_sarcastic, seed=123)
    sampled_2 = sampler.sample_intent(persona_sarcastic, seed=123)
    assert sampled_1 == sampled_2
    assert isinstance(sampled_1, IntentType)


# ============================================================================
# 5. TEST STYLE REALIZER
# ============================================================================
def test_style_realizer():
    realizer = StyleRealizer()
    few_shots = realizer.retrieve_few_shots(register="gaul jaksel", topic="kebijakan_publik", k=3)

    assert 3 <= len(few_shots) <= 5
    assert any(s.register == "gaul jaksel" for s in few_shots)

    persona = Persona(persona_id="p_jaksel", language_register="gaul jaksel")
    prompt_pkg = realizer.build_thread_prompt(
        persona=persona,
        parent_post="Uji coba tarif KRL berbasis NIK dimulai pekan depan.",
        thread_history=[{"author": "UserA", "text": "Setuju biar tepat sasaran."}],
        intent=IntentType.DISAGREE_COUNTER,
    )

    assert "system_instruction" in prompt_pkg
    assert "user_prompt" in prompt_pkg
    assert prompt_pkg["few_shots_used"] >= 3
    assert "gaul jaksel" in prompt_pkg["user_prompt"]


# ============================================================================
# 6. TEST NOISE LAYER (SINGKATAN & TYPO DETERMINISTIC)
# ============================================================================
def test_noise_layer():
    injector = NoiseInjector(default_typo_rate=0.03)
    raw_text = "Yang tidak setuju dengan kebijakan ini banyak sekali, sudah seharusnya dievaluasi sekarang."

    # Injeksi singkatan medsos
    rng = __import__("random").Random(10)
    abbreviated = injector.apply_abbreviations(raw_text, rng=rng, prob=1.0)
    # Kata 'yang' -> 'yg', 'tidak' -> 'gak', 'banyak' -> 'byk', 'sudah' -> 'udh', 'sekarang' -> 'skrg'
    assert any(abbr in abbreviated for abbr in ["yg", "gak", "byk", "udh", "skrg"])

    # Injeksi typo QWERTY
    text_clean = "pemerintah daerah menetapkan anggaran baru"
    text_with_typo = injector.apply_typos(text_clean, rng=__import__("random").Random(42), rate=0.05)
    assert text_with_typo != text_clean
    assert len(text_with_typo) == len(text_clean) or abs(len(text_with_typo) - len(text_clean)) <= 1

    # Determinisme full pipeline apply_noise
    res_1 = apply_noise(raw_text, seed=999)
    res_2 = apply_noise(raw_text, seed=999)
    assert res_1 == res_2


# ============================================================================
# 7. TEST OPINION DYNAMICS & HAWKES PROCESS
# ============================================================================
def test_bounded_confidence_and_hawkes():
    # Bounded Confidence: Deffuant
    model = BoundedConfidenceModel(epsilon=0.3, convergence_rate=0.5)

    # Opini dekat (selisih 0.2 <= 0.3) -> konvergensi
    new_i, new_j = model.deffuant_pairwise_step(0.4, 0.6)
    assert new_i > 0.4
    assert new_j < 0.6
    assert abs(new_i - new_j) < 0.2

    # Opini jauh (selisih 0.8 > 0.3) -> tidak berubah
    stay_i, stay_j = model.deffuant_pairwise_step(0.1, 0.9)
    assert stay_i == 0.1
    assert stay_j == 0.9

    # Hegselmann-Krause
    opinions = [0.1, 0.15, 0.2, 0.8, 0.85]
    updated = model.hegselmann_krause_step(opinions, epsilon=0.2)
    assert len(updated) == 5
    # Kelompok bawah konvergen ke ~0.15
    assert abs(updated[0] - 0.15) < 0.05

    # Emotional contagion
    contagion = EmotionalContagion(contagion_rate=0.4)
    v, a = contagion.update_emotion(receiver_valence=-0.2, receiver_arousal=0.3, sender_valence=0.8, sender_arousal=0.7)
    assert v > -0.2  # valence meningkat ke arah sender
    assert a > 0.3  # arousal meningkat

    # Hawkes Process
    hawkes = HawkesProcess(mu=0.5, alpha=0.6, beta=1.0)
    assert hawkes.branching_ratio == 0.6  # subkritis
    events = hawkes.simulate_arrivals(duration=10.0, seed=42)
    assert isinstance(events, list)
    assert len(events) > 0
    # Waktu harus monoton naik
    assert all(events[i] <= events[i + 1] for i in range(len(events) - 1))


# ============================================================================
# 8. TEST CALIBRATION HARNESS
# ============================================================================
def test_calibration_harness():
    validator = StylizedFactsValidator()

    # 1. Aturan 90-9-1: 90 lurkers, 9 curators, 1 creator
    actions_mock = {}
    for i in range(90):
        actions_mock[f"lurker_{i}"] = {}
    for i in range(9):
        actions_mock[f"curator_{i}"] = {"like": 3}
    actions_mock["creator_0"] = {"post": 1, "comment": 2}

    res_90 = validator.validate_90_9_1_rule(actions_mock)
    assert res_90["passed"] is True
    assert res_90["ratios"]["lurker"] == 0.90
    assert res_90["ratios"]["curator"] == 0.09
    assert res_90["ratios"]["creator"] == 0.01

    # 2. Heavy-tailed cascade (sampel Pareto)
    cascade_sizes = [1] * 50 + [2] * 20 + [5] * 10 + [15] * 5 + [50] * 2 + [200] * 1
    res_tail = validator.validate_heavy_tail(cascade_sizes)
    assert res_tail["passed"] is True
    assert 1.1 <= res_tail["alpha"] <= 3.8

    # 3. Diurnal cycle
    # Puncak siang (12-13) dan malam (19-22), sepi dini hari (1-5)
    hours = [12] * 15 + [13] * 15 + [20] * 25 + [21] * 25 + [2] * 2 + [3] * 2
    res_diurnal = validator.validate_diurnal_cycle(hours)
    assert res_diurnal["passed"] is True


# ============================================================================
# 9. TEST EVALUATION SUITE & N-GRAM LEAKAGE CHECKER
# ============================================================================
def test_evaluation_suite_and_leakage():
    suite = EvaluationSuite()

    # TTR
    texts = ["pemerintah daerah meresmikan fasilitas baru", "fasilitas baru tersebut sangat bermanfaat"]
    ttr = compute_ttr(texts)
    assert 0.0 < ttr <= 1.0

    # Leakage Checker
    ref_seed = [
        "kebijakan integrasi data kependudukan nasional untuk alokasi subsidi tepat sasaran terpadu"
    ]

    # Kasus A: Teks orisinal tanpa leak
    gen_clean = [
        "kami menyambut baik kebijakan baru ini agar ekonomi tumbuh sehat dan inklusif"
    ]
    res_clean = check_ngram_leakage(gen_clean, ref_seed, n=8)
    assert res_clean["leakage_detected"] is False
    assert res_clean["overlap_count"] == 0

    # Kasus B: Teks bocor persis 8 kata berturut-turut dari referensi
    gen_leaked = [
        "kebijakan integrasi data kependudukan nasional untuk alokasi subsidi tepat sasaran terpadu di masa depan"
    ]
    res_leaked = check_ngram_leakage(gen_leaked, ref_seed, n=8)
    assert res_leaked["leakage_detected"] is True
    assert res_leaked["overlap_count"] >= 1


# ============================================================================
# 10. TEST ETHICS GUARD (SANDBOX LOCK, WATERMARK, MANDATORY METADATA)
# ============================================================================
def test_ethics_guard():
    guard = EthicsGuard(strict_sandbox=True)

    # 1. Sandbox Lock: Tolak koneksi API platform nyata
    with pytest.raises(SandboxViolationError) as exc_info:
        guard.verify_sandbox_safety("https://api.twitter.com/2/tweets")
    assert "[SANDBOX LOCK]" in str(exc_info.value)

    with pytest.raises(SandboxViolationError):
        guard.verify_sandbox_safety("https://oauth.reddit.com/api/v1/me")

    with pytest.raises(SandboxViolationError):
        guard.verify_sandbox_safety("https://graph.facebook.com/v19.0/me")

    # Target aman sintetis tidak boleh error
    guard.verify_sandbox_safety("http://localhost:8088/synthetic_mock")

    # 2. Mandatory Metadata
    post_item = {"id": "p123", "text": "Contoh komentar simulasi"}
    tagged = guard.attach_mandatory_metadata(post_item, simulation_id="sim_abc")
    assert tagged["is_synthetic"] is True
    assert tagged["simulation_id"] == "sim_abc"
    assert tagged["simulation_watermark"] == WATERMARK_TEXT

    # 3. Export Watermark
    exported_str = guard.apply_export_watermark("kolom1,kolom2\nval1,val2")
    assert WATERMARK_TEXT in exported_str

    exported_dict = guard.apply_export_watermark({"items": [1, 2, 3]})
    assert exported_dict["__NOTICE__"] == WATERMARK_TEXT
    assert exported_dict["is_synthetic_dataset"] is True

    # 4. Audit Log
    rec = guard.record_audit(simulation_id="sim_abc", event_count=150, agent_count=50)
    assert rec.simulation_id == "sim_abc"
    assert rec.watermark == WATERMARK_TEXT
    logs = guard.get_audit_records()
    assert len(logs) == 1
    assert logs[0]["event_count"] == 150
