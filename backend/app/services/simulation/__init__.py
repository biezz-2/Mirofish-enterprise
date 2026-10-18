# backend/app/services/simulation/__init__.py
"""
Paket Simulator Algoritma Platform dan Komentar AI Menyerupai Manusia (MiroFish Engine v3.6).
Berdasarkan Makalah 2:
1. feed_pipeline: Arsitektur Home-Mixer 6-Tahap
2. platform_profile_store: Profil platform versioned YAML
3. persona_store: Profil agen multi-dimensi Big Five (OCEAN) & komunikasi
4. intent_sampler: Taksonomi 7-intent & multinomial sampling
5. style_realizer: Thread transcript prompt dengan few-shot retrieval
6. noise_layer: Deterministic post-LLM noise injection (singkatan & QWERTY typo)
7. opinion_dynamics: Bounded confidence & Hawkes self-exciting process
8. calibration_harness: Validator 90-9-1, heavy tail, diurnal cycle
9. evaluation_suite: C2ST, TTR, Self-BLEU, dan n-gram leakage checker
10. ethics_guard: Sandbox lock, mandatory metadata, dan watermark export.
"""

from app.services.simulation.feed_pipeline import (
    CandidateItem,
    FeedPipeline,
    FilterStage,
    HydratorStage,
    PipelineContext,
    ScorerStage,
    SelectorStage,
    SideEffectStage,
    SourceStage,
)
from app.services.simulation.platform_profile_store import PlatformProfileStore
from app.services.simulation.persona_store import Persona, PersonaStore
from app.services.simulation.intent_sampler import IntentSampler, IntentType
from app.services.simulation.style_realizer import StyleRealizer, ConversationSample
from app.services.simulation.noise_layer import NoiseInjector, apply_noise
from app.services.simulation.opinion_dynamics import (
    BoundedConfidenceModel,
    EmotionalContagion,
    HawkesProcess,
)
from app.services.simulation.calibration_harness import (
    CalibrationReport,
    StylizedFactsValidator,
)
from app.services.simulation.evaluation_suite import (
    EvaluationSuite,
    check_ngram_leakage,
    compute_proxy_perplexity,
    compute_self_bleu,
    compute_ttr,
    evaluate_c2st_proxy,
)
from app.services.simulation.ethics_guard import (
    EthicsGuard,
    SandboxViolationError,
    WATERMARK_TEXT,
)

__all__ = [
    "CandidateItem",
    "FeedPipeline",
    "PipelineContext",
    "SourceStage",
    "HydratorStage",
    "FilterStage",
    "ScorerStage",
    "SelectorStage",
    "SideEffectStage",
    "PlatformProfileStore",
    "Persona",
    "PersonaStore",
    "IntentSampler",
    "IntentType",
    "StyleRealizer",
    "ConversationSample",
    "NoiseInjector",
    "apply_noise",
    "BoundedConfidenceModel",
    "EmotionalContagion",
    "HawkesProcess",
    "CalibrationReport",
    "StylizedFactsValidator",
    "EvaluationSuite",
    "check_ngram_leakage",
    "compute_ttr",
    "compute_self_bleu",
    "compute_proxy_perplexity",
    "evaluate_c2st_proxy",
    "EthicsGuard",
    "SandboxViolationError",
    "WATERMARK_TEXT",
]
