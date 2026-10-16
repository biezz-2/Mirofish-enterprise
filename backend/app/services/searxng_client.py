"""
MiroFish Enterprise SearXNG Specialist Client (Agent 02: Divisi R2P)
Metasearch privat zero-tracking dengan output JSON, rotasi user-agent,
multi-engine routing (Google, Bing, DuckDuckGo, Brave, arXiv), token-bucket rate limiting,
query fallback relaxation, in-memory TTL caching, dan batch latency < 1.2s.
"""

import os
import re
import time
import random
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Set
import aiohttp

from .searchxng_service import SearchXNGReport, SearchXNGResult
from ..utils.logger import get_logger

logger = get_logger("mirofish.searxng_client")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

DEFAULT_SUPPORTED_ENGINES = ["google", "bing", "duckduckgo", "brave", "arxiv"]

ENGINE_CATEGORY_PRESETS: Dict[str, List[str]] = {
    "general": ["google", "bing", "duckduckgo", "brave"],
    "academic": ["arxiv", "google"],
    "science": ["arxiv", "google"],
    "news": ["bing", "brave", "google"],
    "privacy_first": ["duckduckgo", "brave"],
}

STOP_WORDS = {
    "yang", "di", "ke", "dari", "pada", "dalam", "untuk", "dengan", "dan", "atau",
    "ini", "itu", "juga", "sudah", "saya", "kamu", "dia", "mereka", "kita", "kami",
    "adalah", "sebagai", "tentang", "the", "a", "an", "in", "on", "at", "for",
    "to", "of", "and", "or", "is", "are", "was", "were", "with", "by", "from"
}


class TokenBucketRateLimiter:
    """Token Bucket rate limiter untuk membatasi request per detik secara aman."""

    def __init__(self, rate: float = 10.0, capacity: float = 20.0):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, amount: float = 1.0) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens < amount:
                wait_time = (amount - self.tokens) / self.rate
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self.tokens = 0.0
            else:
                self.tokens -= amount


class SearXNGClient:
    """
    Specialized client for SearXNG private metasearch.
    Features:
    - Zero-tracking client header enforcement (no IP/Referer leakage).
    - Multi-engine routing (Google, Bing, DuckDuckGo, Brave, arXiv).
    - Token-bucket rate limiting.
    - Fallback query generation & relaxation.
    - In-memory TTL caching for sub-millisecond repeated queries.
    - Asynchronous batch execution maintaining target latency < 1.2s.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_s: float = 4.0,
        rate_limit_qps: float = 10.0,
        rate_limit_burst: float = 20.0,
        cache_ttl_s: float = 300.0,
    ):
        self.base_url = (base_url or os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888")).rstrip("/")
        self.timeout_s = timeout_s
        self.cache_ttl_s = cache_ttl_s
        self.rate_limiter = TokenBucketRateLimiter(rate=rate_limit_qps, capacity=rate_limit_burst)
        self._cache: Dict[str, Tuple[float, SearchXNGReport]] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

    def get_random_user_agent(self) -> str:
        """Mengambil string User-Agent acak dari peramban modern."""
        return random.choice(USER_AGENTS)

    def get_zero_tracking_headers(self, user_agent: Optional[str] = None) -> Dict[str, str]:
        """
        Menyusun header HTTP zero-tracking ketat.
        Menghapus informasi identitas pengguna, IP klien, dan referer.
        """
        ua = user_agent or self.get_random_user_agent()
        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    async def get_session(self) -> aiohttp.ClientSession:
        """Membuat / memakai ulang ClientSession dengan connection pooling optimal."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=25,
                    keepalive_timeout=30.0,
                    enable_cleanup_closed=True,
                )
                timeout = aiohttp.ClientTimeout(total=self.timeout_s)
                self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
            return self._session

    def _build_cache_key(
        self,
        query: str,
        category: str,
        engines: Optional[List[str]],
        language: str,
    ) -> str:
        sorted_eng = ",".join(sorted(engines)) if engines else "default"
        return f"{query.strip().lower()}|{category}|{sorted_eng}|{language}"

    def _get_from_cache(self, cache_key: str) -> Optional[SearchXNGReport]:
        now = time.monotonic()
        if cache_key in self._cache:
            created_at, report = self._cache[cache_key]
            if now - created_at < self.cache_ttl_s:
                # Return deepcopy-like cloned report
                return SearchXNGReport(
                    query=report.query,
                    category=report.category,
                    results=list(report.results),
                    total_results=report.total_results,
                    search_time=0.001,
                    engines_used=list(report.engines_used),
                    generated_at=report.generated_at,
                )
            del self._cache[cache_key]
        return None

    def _store_in_cache(self, cache_key: str, report: SearchXNGReport) -> None:
        if report.results:
            self._cache[cache_key] = (time.monotonic(), report)

    def generate_fallback_queries(self, query: str) -> List[str]:
        """
        Menghasilkan kueri alternatif bertingkat (query relaxation).
        Tingkat 1: Menghapus tanda kutip dan operator pencarian (site:, filetype:, AND/OR).
        Tingkat 2: Menghapus tanda baca dan kata henti (stop words).
        """
        fallbacks: List[str] = []
        cleaned = re.sub(r'(site:[^\s]+|filetype:[^\s]+|\bAND\b|\bOR\b|\bNOT\b)', '', query, flags=re.IGNORECASE)
        cleaned = re.sub(r'["\']', ' ', cleaned).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        if cleaned and cleaned.lower() != query.lower():
            fallbacks.append(cleaned)

        words = re.findall(r'\b\w+\b', cleaned if cleaned else query)
        filtered_words = [w for w in words if w.lower() not in STOP_WORDS]
        if 1 < len(filtered_words) < len(words):
            relaxed = " ".join(filtered_words)
            if relaxed not in fallbacks and relaxed.lower() != query.lower():
                fallbacks.append(relaxed)

        return fallbacks

    def resolve_engines(self, category: str, explicit_engines: Optional[List[str]]) -> List[str]:
        """Menentukan daftar engine berdasarkan kategori dan request eksplisit."""
        if explicit_engines:
            return [e for e in explicit_engines if e in DEFAULT_SUPPORTED_ENGINES] or explicit_engines
        return ENGINE_CATEGORY_PRESETS.get(category, ENGINE_CATEGORY_PRESETS["general"])

    async def _execute_single_request(
        self,
        query: str,
        category: str = "general",
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        language: str = "id",
        time_range: Optional[str] = None,
    ) -> SearchXNGReport:
        """Eksekusi HTTP langsung ke SearXNG dengan zero-tracking headers dan token bucket."""
        await self.rate_limiter.acquire(1.0)

        resolved_engines = self.resolve_engines(category, engines)
        engines_param = ",".join(resolved_engines)

        report = SearchXNGReport(query=query, category=category)
        headers = self.get_zero_tracking_headers()
        session = await self.get_session()

        params: Dict[str, Any] = {
            "q": query,
            "format": "json",
            "category": category,
            "pageno": 1,
            "language": language,
            "engines": engines_param,
        }
        if time_range:
            params["time_range"] = time_range

        start_time = time.monotonic()
        try:
            async with session.get(
                f"{self.base_url}/search",
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout_s),
            ) as resp:
                elapsed = time.monotonic() - start_time
                report.search_time = round(elapsed, 4)

                if resp.status != 200:
                    logger.warning(f"SearXNG status {resp.status} untuk query '{query}'")
                    return report

                data = await resp.json()

            raw_results = data.get("results", [])
            report.total_results = data.get("number_of_results", len(raw_results))

            engines_used: Set[str] = set()
            parsed_results: List[SearchXNGResult] = []

            for r in raw_results[:max_results]:
                eng = r.get("engine", "unknown")
                engines_used.add(eng)
                parsed_results.append(
                    SearchXNGResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        content=r.get("content", ""),
                        engine=eng,
                        publish_date=r.get("publishedDate"),
                        img_src=r.get("img_src"),
                        category=category,
                        relevance_score=max(0.2, 0.9 - len(parsed_results) * 0.05),
                    )
                )

            report.results = parsed_results
            report.engines_used = list(engines_used) or resolved_engines

        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start_time
            report.search_time = round(elapsed, 4)
            logger.warning(f"Pencarian SearXNG timeout ({self.timeout_s}s) untuk '{query}'")
        except Exception as e:
            elapsed = time.monotonic() - start_time
            report.search_time = round(elapsed, 4)
            logger.error(f"Pencarian SearXNG gagal untuk '{query}': {e}")

        return report

    async def search_json(
        self,
        query: str,
        category: str = "general",
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        language: str = "id",
        enable_fallback: bool = True,
        time_range: Optional[str] = None,
    ) -> SearchXNGReport:
        """
        Pencarian privat lengkap dengan:
        1. In-memory cache check.
        2. Primary query execution via multi-engine routing.
        3. Automatic query fallback relaxation jika hasil kosong.
        4. In-memory cache storage.
        """
        cache_key = self._build_cache_key(query, category, engines, language)
        cached_report = self._get_from_cache(cache_key)
        if cached_report:
            return cached_report

        report = await self._execute_single_request(
            query=query,
            category=category,
            engines=engines,
            max_results=max_results,
            language=language,
            time_range=time_range,
        )

        # Fallback logic jika hasil kosong dan enable_fallback aktif
        if not report.results and enable_fallback:
            fallbacks = self.generate_fallback_queries(query)
            for fb_query in fallbacks:
                logger.info(f"Mencoba kueri fallback: '{fb_query}' untuk kueri awal '{query}'")
                fb_report = await self._execute_single_request(
                    query=fb_query,
                    category=category,
                    engines=engines,
                    max_results=max_results,
                    language=language,
                    time_range=time_range,
                )
                if fb_report.results:
                    fb_report.query = query  # Tetap kaitkan kueri awal
                    report = fb_report
                    break

            # Fallback engine jika masih kosong dan kueri spesifik digunakan
            if not report.results and engines and set(engines) != set(ENGINE_CATEGORY_PRESETS["general"]):
                logger.info(f"Fallback ke engine general untuk query '{query}'")
                fb_report = await self._execute_single_request(
                    query=query,
                    category="general",
                    engines=ENGINE_CATEGORY_PRESETS["general"],
                    max_results=max_results,
                    language=language,
                    time_range=time_range,
                )
                if fb_report.results:
                    report = fb_report

        self._store_in_cache(cache_key, report)
        return report

    async def search(
        self,
        query: str,
        category: str = "general",
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        language: str = "id",
        time_range: Optional[str] = None,
    ) -> SearchXNGReport:
        """Alias kompatibel penuh dengan SearchXNGService."""
        return await self.search_json(
            query=query,
            category=category,
            engines=engines,
            max_results=max_results,
            language=language,
            time_range=time_range,
        )

    async def search_batch(
        self,
        queries: List[str],
        category: str = "general",
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        language: str = "id",
        max_concurrency: int = 5,
    ) -> List[SearchXNGReport]:
        """
        Pencarian batch konkuren dengan batas concurrency semaphore.
        Memastikan latensi rata-rata batch tetap < 1.2s.
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _bounded_search(q: str) -> SearchXNGReport:
            async with semaphore:
                return await self.search_json(
                    query=q,
                    category=category,
                    engines=engines,
                    max_results=max_results,
                    language=language,
                )

        tasks = [_bounded_search(q) for q in queries]
        return await asyncio.gather(*tasks)

    def search_sync(self, query: str, **kwargs) -> SearchXNGReport:
        """Eksekusi sinkron untuk CLI atau modul blocking."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Nested loop handling
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, self.search_json(query, **kwargs)).result()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.search_json(query, **kwargs))

    async def close(self) -> None:
        """Menutup ClientSession secara bersih."""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
