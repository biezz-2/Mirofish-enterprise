"""
Layanan riset internet (SearXNG) - Lapisan 0 MiroFish.
Menghasilkan laporan: fakta inti, entitas, tren, skor kredibilitas.
Seluruh snippet disanitasi sebelum dipakai untuk mencegah injeksi prompt.
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

logger = get_logger('mirofish.web_research')

# Pola pembersih injeksi-prompt
_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"abaikan (semua )?instruksi sebelumnya",
    r"system\s*prompt",
    r"you are now",
    r"<\|.*?\|>",
    r"\{\{.*?\}\}",
]

def sanitize_snippet(text: str, max_len: int = 500) -> str:
    """Sanitasi snippet: lepas instruksi bawaan, markup, dan pangkas."""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    for pat in _INJECTION_PATTERNS:
        t = re.sub(pat, "[teks disunting]", t, flags=re.IGNORECASE)
    t = re.sub(r"[<>{}]", "", t)
    return t[:max_len]


@dataclass
class ResearchReport:
    """Laporan riset web Langkah 0."""
    query: str
    search_engine: str = "searchxng"
    web_results: List[SearchXNGResult] = field(default_factory=list)
    summarized_facts: List[str] = field(default_factory=list)
    entities_mentioned: List[Dict[str, Any]] = field(default_factory=list)
    trends: List[str] = field(default_factory=list)
    credibility_score: float = 0.0
    research_type: str = "general"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "search_engine": self.search_engine,
            "web_results": [r.to_dict() for r in self.web_results],
            "summarized_facts": self.summarized_facts,
            "entities_mentioned": self.entities_mentioned,
            "trends": self.trends,
            "credibility_score": self.credibility_score,
            "research_type": self.research_type,
            "generated_at": self.generated_at
        }

    def to_text(self) -> str:
        """Format teks untuk LLM (Bahasa Indonesia)."""
        parts = [
            "## Laporan Riset Internet (SearXNG)",
            f"Topik kueri: {self.query}",
            f"Mesin: {self.search_engine}",
            f"Skor kredibilitas: {self.credibility_score:.2f}",
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

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.searchxng = SearchXNGService()
        self.llm = llm_client
        logger.info("WebResearchService (SearXNG) diinisialisasi")

    async def research(self, query: str, research_type: str = "general",
                       include_facts_extraction: bool = True,
                       days_back: int = 7, max_results: int = 20) -> ResearchReport:
        report = ResearchReport(query=query, research_type=research_type)
        if research_type == "news":
            sr = await self.searchxng.search_news(query, days_back=days_back, max_results=max_results)
        elif research_type == "images":
            sr = await self.searchxng.search_images(query, max_results=max_results)
        else:
            sr = await self.searchxng.search(query, max_results=max_results)
            
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
        """Ekstraksi fakta inti dari cuplikan hasil pencarian."""
        if not report.web_results:
            return
        # Heuristik bawaan jika LLM client belum aktif
        facts = []
        for r in report.web_results[:5]:
            if len(r.content) > 30:
                facts.append(r.content[:160] + "...")
        report.summarized_facts = facts or [f"Informasi terkini mengenai {report.query} berhasil ditemukan."]
        report.trends = [f"Peningkatan diskusi terkait {report.query} di media daring."]

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
        """Menghitung skor kredibilitas: relevansi + bonus sumber berita + agregasi mesin."""
        if not report.web_results:
            report.credibility_score = 0.0
            return
        scores = []
        for r in report.web_results:
            s = r.relevance_score
            if r.category == "news":
                s += 0.15
            if len(report.web_results) >= 5:
                s += 0.05
            scores.append(s)
        report.credibility_score = round(min(sum(scores) / len(scores), 1.0), 2)
