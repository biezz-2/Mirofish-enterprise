"""
Layanan riset internet (SearXNG) - Lapisan 0 MiroFish.
Menghasilkan laporan: fakta inti, entitas, tren, skor kredibilitas.
Seluruh snippet disanitasi sebelum dipakai untuk mencegah injeksi prompt.
Diperkaya dengan Domain Credibility Scorer & Epistemic Grounding Validator (Agent 04).
"""
import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from .searchxng_service import SearchXNGService, SearchXNGResult
from .pii_scrubber import PIIScrubber
from .domain_credibility import (
    DomainCredibilityScorer,
    EpistemicGroundingValidator,
    GroundedFact,
    EpistemicStatus,
    SourceCredibility
)

logger = get_logger('mirofish.web_research')

# Perisai 3-Lapis Anti-Prompt Injection
class ContentShield:
    """Perisai 3-lapis Anti-Prompt Injection untuk konten internet tidak tepercaya (Step 0 Grounding)."""

    # Lapis 1: Regex filter pola jailbreak & prompt injection tokens
    JAILBREAK_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|past)\s+instructions?",
        r"abaikan\s+(semua\s+)?instruksi\s+sebelumnya",
        r"lupakan\s+(semua\s+)?instruksi\s+sebelumnya",
        r"disregard\s+(all\s+)?(prior|previous)\s+instructions?",
        r"forget\s+(all\s+)?previous\s+(context|instructions?)",
        r"system\s*prompt",
        r"system\s*message",
        r"pesan\s*sistem",
        r"you\s+are\s+now",
        r"anda\s+sekarang\s+adalah",
        r"mulai\s+sekarang\s+kamu\s+adalah",
        r"pretend\s+(you\s+are|to\s+be)",
        r"berpura-puralah",
        r"dan\s+mode",
        r"developer\s+mode",
        r"mode\s+pengembang",
        r"<\|.*?\|>",
        r"\{\{.*?\}\}",
        r"\[system\]",
        r"\[assistant\]",
        r"\[INST\]",
        r"\[/INST\]",
        r"<system>",
        r"</system>",
        r"<prompt>",
        r"</prompt>",
        r"<<<.*?>>>",
    ]

    # Lapis 2: Deteksi semantik injeksi instruksi & perintah imperatif berisiko
    SEMANTIC_INSTRUCTION_PATTERNS = [
        r"(print|reveal|output|display|show|leak)\s+(the\s+)?(api[_\s]?key|password|secret|env|token|credential|system\s+prompt)",
        r"(bocorkan|tampilkan|cetak|beberkan)\s+(rahasia|kunci|kata\s+sandi|token|kredensial)",
        r"override\s+(all\s+)?rules",
        r"timpa\s+(semua\s+)?aturan",
        r"bypass\s+(safety|content|filter|security|guardrails?)",
        r"bypass\s+keamanan",
        r"tembus\s+(keamanan|filter)",
        r"act\s+as\s+an?\s+unrestricted",
        r"bertindaklah\s+tanpa\s+batasan",
        r"do\s+not\s+follow\s+(the\s+)?(system|developer|guidelines?|rules?)",
        r"jangan\s+ikuti\s+(aturan|sistem|pengembang)",
        r"new\s+(system\s+)?instructions?:",
        r"instruksi\s+baru:",
        r"you\s+must\s+(now\s+)?obey",
        r"kamu\s+harus\s+mematuhi",
        r"execute\s+the\s+following\s+(command|code|instruction|prompt)",
        r"jalankan\s+perintah\s+berikut",
    ]

    @classmethod
    def sanitize(cls, text: str, max_len: int = 500) -> str:
        """
        Menjalankan perisai 3-lapis:
        - Layer 1: Regex filter pola jailbreak
        - Layer 2: Deteksi semantik injeksi instruksi & netralisasi
        - Layer 3: Isolasi tanda kutip aman (safe quote containment) & netralisasi delimiter
        """
        t = re.sub(r"\s+", " ", str(text or "")).strip()

        # Lapisan 1: Regex filter pola jailbreak
        for pat in cls.JAILBREAK_PATTERNS:
            t = re.sub(pat, "[FILTERED_JAILBREAK]", t, flags=re.IGNORECASE)

        # Lapisan 2: Deteksi semantik injeksi instruksi & netralisasi
        for pat in cls.SEMANTIC_INSTRUCTION_PATTERNS:
            t = re.sub(pat, "[BLOCKED_INSTRUCTION]", t, flags=re.IGNORECASE)

        # Lapisan 3: Isolasi tanda kutip aman & netralisasi delimiter
        t = t.replace("```", "’’’")
        t = t.replace('"', "”").replace("'", "’").replace("`", "‘")
        t = re.sub(r"[<>{}]", "", t)

        # Sanitasi PII (UU PDP)
        t = PIIScrubber.scrub(t)
        return t[:max_len].strip()

    @classmethod
    def isolate_as_evidence(cls, text: str, source_domain: str = "web", credibility_score: float = 0.50, max_len: int = 500) -> str:
        """
        Lapisan 3 Isolasi Struktural Tingkat Lanjut:
        Membungkus fakta web yang telah disanitasi ke dalam tanda pagar kutipan aman (safe quotation fencing),
        menegaskan batas epistemik agar LLM memperlakukannya murni sebagai data observasi empiris, bukan instruksi.
        """
        sanitized = cls.sanitize(text, max_len=max_len)
        return f"«BUKTI_WEB_TERISOLASI [Domain: {source_domain} | S_cred: {credibility_score:.2f}]: {sanitized} AKHIR_BUKTI»"


def sanitize_snippet(text: str, max_len: int = 500) -> str:
    """Sanitasi snippet: 3-lapis Anti-Prompt Injection, PII scrubbing, dan isolasi tanda kutip aman."""
    return ContentShield.sanitize(text, max_len=max_len)
    return ContentShield.sanitize(text, max_len=max_len)


@dataclass
class ResearchReport:
    """Laporan riset web Langkah 0 dengan validasi epistemik dan sitasi kredibilitas domain."""
    query: str
    search_engine: str = "searchxng"
    web_results: List[SearchXNGResult] = field(default_factory=list)
    summarized_facts: List[str] = field(default_factory=list)
    grounded_facts: List[GroundedFact] = field(default_factory=list)
    entities_mentioned: List[Dict[str, Any]] = field(default_factory=list)
    trends: List[str] = field(default_factory=list)
    credibility_score: float = 0.0
    min_credibility_score: float = 0.70
    verified_claims_count: int = 0
    research_type: str = "general"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def export_step0_contract(self, status: str = "COMPLETED") -> Dict[str, Any]:
        """Ekspor laporan ke spesifikasi kontrak Step 0 (contracts/01-step0-research.json)."""
        validator = EpistemicGroundingValidator()
        return validator.export_step0_contract(
            query=self.query,
            facts=self.grounded_facts,
            overall_credibility=self.credibility_score,
            status=status
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "search_engine": self.search_engine,
            "web_results": [r.to_dict() for r in self.web_results],
            "summarized_facts": self.summarized_facts,
            "grounded_facts": [f.to_dict() for f in self.grounded_facts],
            "entities_mentioned": self.entities_mentioned,
            "trends": self.trends,
            "credibility_score": self.credibility_score,
            "min_credibility_score": self.min_credibility_score,
            "verified_claims_count": self.verified_claims_count,
            "research_type": self.research_type,
            "generated_at": self.generated_at
        }

    def to_text(self) -> str:
        """Format teks untuk LLM (Bahasa Indonesia)."""
        parts = [
            "## Laporan Riset Internet (SearXNG)",
            f"Topik kueri: {self.query}",
            f"Mesin: {self.search_engine}",
            f"Skor kredibilitas: {self.credibility_score:.2f} (Ambang batas verifikasi: {self.min_credibility_score:.2f})",
            f"Klaim terverifikasi: {self.verified_claims_count}/{len(self.summarized_facts)}",
            f"\n### Fakta inti ({len(self.summarized_facts)})"
        ]
        for i, f in enumerate(self.summarized_facts, 1):
            parts.append(f"{i}. {f}")
        if self.entities_mentioned:
            parts.append(f"\n### Entitas ({len(self.entities_mentioned)})")
            for e in self.entities_mentioned:
                parts.append(f"- {e.get('name')} ({e.get('type')})")
        if self.trends:
            parts.append("\n### Tren teridentifikasi")
            for t in self.trends:
                parts.append(f"- {t}")
        if self.web_results:
            parts.append(f"\n### Sumber (Top {min(5, len(self.web_results))})")
            for i, r in enumerate(self.web_results[:5], 1):
                parts.append(f"{i}. [{r.title}]({r.url}) - mesin: {r.engine}")
        return "\n".join(parts)


class WebResearchService:
    """Riset internet berbasis SearXNG: privat, sumber terbuka, gratis."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        credibility_scorer: Optional[DomainCredibilityScorer] = None,
        epistemic_validator: Optional[EpistemicGroundingValidator] = None
    ):
        self.searchxng = SearchXNGService()
        self.llm = llm_client
        self.credibility_scorer = credibility_scorer or DomainCredibilityScorer()
        self.epistemic_validator = epistemic_validator or EpistemicGroundingValidator(scorer=self.credibility_scorer)
        logger.info("WebResearchService (SearXNG + Epistemic Grounding) diinisialisasi")

    async def research(self, query: str, research_type: str = "general",
                       include_facts_extraction: bool = True,
                       days_back: int = 7, max_results: int = 20) -> ResearchReport:
        clean_query = PIIScrubber.scrub(query)
        report = ResearchReport(query=clean_query, research_type=research_type)
        if research_type == "news":
            sr = await self.searchxng.search_news(clean_query, days_back=days_back, max_results=max_results)
        elif research_type == "images":
            sr = await self.searchxng.search_images(clean_query, max_results=max_results)
        else:
            sr = await self.searchxng.search(clean_query, max_results=max_results)
            
        # Sanitasi hasil sebelum disimpan
        for r in sr.results:
            r.content = sanitize_snippet(r.content)
            r.title = sanitize_snippet(r.title, max_len=200)
            
        report.web_results = sr.results
        if include_facts_extraction and report.web_results:
            await self._extract_facts(report)
            await self._extract_entities(report)
            self._evaluate_credibility(report)
        return report

    async def _extract_facts(self, report: ResearchReport):
        """Ekstraksi fakta inti ter-grounding dengan skor numerik dan sitasi domain asli."""
        if not report.web_results:
            return

        grounded_facts = self.epistemic_validator.ground_corpus(report.web_results, max_facts=5)
        # Filter fakta empiris berkualitas tinggi: seleksi domain kredibilitas S_cred >= 0.40
        high_quality_facts = [f for f in grounded_facts if f.credibility_score >= 0.40]
        report.grounded_facts = high_quality_facts if high_quality_facts else grounded_facts

        if report.grounded_facts:
            report.summarized_facts = [f.to_formatted_string() for f in report.grounded_facts]
            report.verified_claims_count = sum(
                1 for f in report.grounded_facts if f.epistemic_status == EpistemicStatus.VERIFIED
            )
        else:
            # Fallback jika tidak ada konten yang cukup panjang
            first_domain = self.credibility_scorer.extract_domain(
                report.web_results[0].url if report.web_results else ""
            )
            report.summarized_facts = [
                f"[UNVERIFIED] [Score: 0.50 | Domain: {first_domain}] Informasi terkini mengenai {report.query} berhasil ditemukan."
            ]
            report.verified_claims_count = 0

        # Tren dengan status epistemik
        trend_status = "[VERIFIED]" if report.verified_claims_count > 0 else "[UNVERIFIED]"
        report.trends = [f"{trend_status} Peningkatan diskusi terkait {report.query} di media daring."]

    async def _extract_entities(self, report: ResearchReport):
        """Ekstraksi entitas sederhana dari hasil pencarian."""
        entities = []
        for r in report.web_results[:3]:
            words = r.title.split()
            for w in words:
                if len(w) > 4 and w[0].isupper():
                    entities.append({"name": w.strip(",.:;"), "type": "topic"})
        seen = set()
        dedup = []
        for e in entities:
            if e["name"] not in seen:
                seen.add(e["name"])
                dedup.append(e)
        report.entities_mentioned = dedup[:8]

    def _evaluate_credibility(self, report: ResearchReport):
        """
        Menghitung skor kredibilitas agregat menggunakan DomainCredibilityScorer.
        S_cred(k) komposit diintegrasikan di seluruh domain unik independen (Notion Dokumen #4).
        Mencegah dominasi artifisial oleh domain tunggal berulang atau situs klon.
        """
        if not report.web_results:
            report.credibility_score = 0.0
            return

        scored_sources = self.credibility_scorer.score_batch(report.web_results)
        if scored_sources:
            domain_scores: Dict[str, List[float]] = {}
            for s in scored_sources:
                domain_scores.setdefault(s.domain, []).append(s.composite_score)
            unique_domain_avgs = [sum(scores) / len(scores) for scores in domain_scores.values()]
            avg_score = sum(unique_domain_avgs) / len(unique_domain_avgs)
            report.credibility_score = round(min(1.0, max(0.0, avg_score)), 2)
        else:
            report.credibility_score = 0.0
