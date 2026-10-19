"""
Layanan integrasi SearXNG - pencarian privat, sumber terbuka, self-hosted.
Tanpa API key komersial. Hasil hanya snippet (cuplikan), bukan halaman penuh.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.searchxng')

@dataclass
class SearchXNGResult:
    """Satu hasil pencarian (snippet)."""
    title: str = ""
    url: str = ""
    content: str = ""          # snippet - data TIDAK TERPERCAYA, wajib disanitasi
    engine: str = "unknown"
    publish_date: Optional[str] = None
    img_src: Optional[str] = None
    category: str = "general"
    relevance_score: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "engine": self.engine,
            "publish_date": self.publish_date,
            "img_src": self.img_src,
            "category": self.category,
            "relevance_score": self.relevance_score
        }

@dataclass
class SearchXNGReport:
    """Laporan pencarian agregat multi-mesin."""
    query: str
    category: str = "general"
    results: List[SearchXNGResult] = field(default_factory=list)
    total_results: int = 0
    search_time: float = 0.0
    engines_used: List[str] = field(default_factory=list)
    endpoint_used: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "category": self.category,
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "search_time": self.search_time,
            "engines_used": self.engines_used,
            "endpoint_used": self.endpoint_used,
            "generated_at": self.generated_at
        }

    def to_text(self) -> str:
        """Format teks untuk LLM (Bahasa Indonesia)."""
        parts = [
            "## Laporan Pencarian SearXNG",
            f"Kueri: {self.query}",
            f"Kategori: {self.category}",
            f"Total hasil: {self.total_results}",
            f"Waktu pencarian: {self.search_time:.2f} detik",
            f"Mesin digunakan: {', '.join(self.engines_used)}",
            f"\n### Hasil (Top {len(self.results)})"
        ]
        for i, r in enumerate(self.results, 1):
            parts.append(f"\n{i}. **{r.title}**")
            parts.append(f"   Sumber mesin: {r.engine}")
            parts.append(f"   Cuplikan: {r.content[:150]}...")
            parts.append(f"   URL: {r.url}")
            if r.publish_date:
                parts.append(f"   Tanggal terbit: {r.publish_date}")
        return "\n".join(parts)


class SearchXNGService:
    """Layanan SearXNG - metasearch agregator 100+ mesin."""

    def __init__(self):
        self.searchxng_url = getattr(Config, "SEARCHXNG_URL", "http://localhost:8088")
        self.enabled = getattr(Config, "SEARCHXNG_ENABLED", True)
        self.timeout = getattr(Config, "SEARCHXNG_TIMEOUT", 30)
        self.max_results = getattr(Config, "SEARCHXNG_MAX_RESULTS", 10)
        logger.info(f"Layanan SearXNG diinisialisasi: URL={self.searchxng_url}, aktif={self.enabled}")

    def get_candidate_endpoints(self) -> List[str]:
        """
        Daftar endpoint SearXNG berurutan:
        1. Local primary: http://localhost:8088
        2. Local IP: http://127.0.0.1:8088
        3. Remote failover: http://192.168.101.19:8089
        4. Configured custom URL (jika ada)
        """
        candidate_urls = []
        local_primary = getattr(Config, "SEARCHXNG_LOCAL_URL", "http://localhost:8088").rstrip("/")
        candidate_urls.append(local_primary)
        local_ip = "http://127.0.0.1:8088"
        if local_ip not in candidate_urls:
            candidate_urls.append(local_ip)

        remote_fallback = getattr(Config, "SEARCHXNG_FALLBACK_URL", "http://192.168.101.19:8089").rstrip("/")
        if remote_fallback not in candidate_urls:
            candidate_urls.append(remote_fallback)

        if self.searchxng_url:
            configured_url = self.searchxng_url.rstrip("/")
            if configured_url not in candidate_urls:
                candidate_urls.append(configured_url)
        return candidate_urls

    async def search(self, query: str, category: str = "general", page: int = 1,
                     max_results: int = None, language: str = "id",
                     time_range: str = None) -> SearchXNGReport:
        if not self.enabled:
            logger.warning("SearXNG dinonaktifkan - kembalikan hasil kosong")
            return SearchXNGReport(query=query, category=category)
        max_results = max_results or self.max_results
        report = SearchXNGReport(query=query, category=category)
        start = datetime.now()
        params = {
            "q": query,
            "category": category,
            "format": "json",
            "pageno": page,
            "language": language,
            "num_results": max_results
        }
        if time_range:
            params["time_range"] = time_range

        # Arsitektur Search: Primary instance pada local machine (http://localhost:8088),
        # dengan failover otomatis ke remote server 192.168.101.19:8089 jika offline.
        candidate_urls = self.get_candidate_endpoints()

        last_error = None
        for endpoint in candidate_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{endpoint}/search",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout, connect=2.0)
                    ) as resp:
                        if resp.status != 200:
                            raise Exception(f"SearXNG ({endpoint}) mengembalikan status {resp.status}")
                        data = await resp.json()
                results = data.get("results", [])
                report.total_results = data.get("number_of_results", len(results))
                report.engines_used = list({r.get("engine", "unknown") for r in results})
                report.endpoint_used = endpoint
                for r in results[:max_results]:
                    report.results.append(SearchXNGResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        content=r.get("content", ""),
                        engine=r.get("engine", "unknown"),
                        publish_date=r.get("publishedDate"),
                        img_src=r.get("img_src"),
                        category=category,
                        relevance_score=max(0.2, 0.8 - len(report.results) * 0.03)
                    ))
                last_error = None
                break
            except asyncio.TimeoutError:
                last_error = f"Pencarian SearXNG kehabisan waktu di {endpoint}"
                logger.warning(f"{last_error}, mencoba endpoint failover...")
            except Exception as e:
                last_error = f"Pencarian SearXNG gagal di {endpoint}: {e}"
                logger.warning(f"{last_error}, mencoba endpoint failover...")

        if last_error and not report.results:
            logger.error(f"Semua endpoint SearXNG gagal. Terakhir: {last_error}")
            report.total_results = 0
            report.results = []
        report.search_time = (datetime.now() - start).total_seconds()
        return report

    async def search_news(self, query: str, days_back: int = 7, max_results: int = 10, language: str = "id") -> SearchXNGReport:
        return await self.search(
            query,
            category="news",
            max_results=max_results,
            language=language,
            time_range="month" if days_back > 7 else "day"
        )

    async def search_images(self, query: str, max_results: int = 20) -> SearchXNGReport:
        return await self.search(query, category="images", max_results=max_results)

    async def search_videos(self, query: str, max_results: int = 10) -> SearchXNGReport:
        return await self.search(query, category="videos", max_results=max_results)

    async def multi_search(self, queries: List[str], category="general", max_results_per_query=5) -> List[SearchXNGReport]:
        tasks = [self.search(q, category=category, max_results=max_results_per_query) for q in queries]
        reports = await asyncio.gather(*tasks, return_exceptions=True)
        out = []
        for i, rep in enumerate(reports):
            out.append(SearchXNGReport(query=queries[i]) if isinstance(rep, Exception) else rep)
        return out
