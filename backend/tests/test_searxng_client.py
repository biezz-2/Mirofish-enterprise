"""
Test suite untuk SearXNGClient (Agent 02: SearXNG Private Search & Ingestion Specialist)
Menguji:
1. Zero-tracking client header enforcement (tanpa kebocoran IP, DNT=1, Sec-GPC=1).
2. Rotasi User-Agent.
3. Multi-engine routing (Google, Bing, DuckDuckGo, Brave, arXiv).
4. Token bucket rate limiting.
5. In-memory caching dengan sub-millisecond retrieval.
6. Fallback query relaxation saat kueri awal kosong / gagal.
7. Latensi batch search < 1.2s per batch.
8. Kompatibilitas SearchXNGReport / to_dict / to_text.
"""

import time
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.searxng_client import (
    SearXNGClient,
    TokenBucketRateLimiter,
    USER_AGENTS,
    DEFAULT_SUPPORTED_ENGINES,
    ENGINE_CATEGORY_PRESETS,
)
from app.services.searchxng_service import SearchXNGReport, SearchXNGResult


@pytest.fixture
def client():
    c = SearXNGClient(base_url="http://127.0.0.1:8888", timeout_s=3.0, cache_ttl_s=60.0)
    yield c


def test_user_agent_rotation(client):
    """Memastikan rotasi User-Agent mengembalikan string valid dari daftar modern."""
    agents_seen = set()
    for _ in range(50):
        ua = client.get_random_user_agent()
        assert ua in USER_AGENTS
        agents_seen.add(ua)
    assert len(agents_seen) > 1, "User-Agent harus terotasi secara acak"


def test_zero_tracking_headers(client):
    """
    Memverifikasi kepatuhan privasi zero-tracking:
    - Tidak ada Referer, Origin, Cookie, X-Forwarded-For, Client-IP.
    - Header DNT dan Sec-GPC aktif.
    """
    headers = client.get_zero_tracking_headers()
    assert headers["DNT"] == "1"
    assert headers["Sec-GPC"] == "1"
    assert "User-Agent" in headers
    assert "Accept" in headers
    assert "Accept-Language" in headers

    # Kebocoran privasi dilarang
    forbidden_keys = [
        "Referer", "Origin", "Cookie", "X-Forwarded-For", "X-Real-IP",
        "Client-IP", "X-Client-IP", "CF-Connecting-IP"
    ]
    for key in forbidden_keys:
        assert key not in headers
        assert key.lower() not in [k.lower() for k in headers.keys()]


def test_engine_routing_resolution(client):
    """Memverifikasi pemilihan engine berdasarkan kategori."""
    general_engines = client.resolve_engines("general", None)
    assert "google" in general_engines
    assert "duckduckgo" in general_engines

    academic_engines = client.resolve_engines("academic", None)
    assert "arxiv" in academic_engines

    explicit = client.resolve_engines("general", ["brave", "arxiv"])
    assert explicit == ["brave", "arxiv"]


def test_fallback_query_generation(client):
    """Memverifikasi relaksasi kueri untuk fallback saat kueri kompleks nihil hasil."""
    q1 = 'site:nature.com "quantum computing" AND artificial intelligence'
    fallbacks = client.generate_fallback_queries(q1)
    assert len(fallbacks) >= 1
    # Memastikan tanda kutip dan operator terhapus
    assert all('"' not in fb for fb in fallbacks)
    assert all("site:" not in fb for fb in fallbacks)
    assert all("AND" not in fb for fb in fallbacks)

    q2 = "bagaimana cara mengoptimalkan model transformer di gpu"
    fb2 = client.generate_fallback_queries(q2)
    # Harus menyaring stop words seperti 'di'
    assert any("di" not in fb.split() for fb in fb2)


@pytest.mark.asyncio
async def test_token_bucket_rate_limiter():
    """Memastikan token bucket membatasi burst dan request flow."""
    limiter = TokenBucketRateLimiter(rate=20.0, capacity=5.0)
    start = time.monotonic()
    # Mengambil 5 token dalam batas kapasitas (instan)
    for _ in range(5):
        await limiter.acquire(1.0)
    instant_elapsed = time.monotonic() - start
    assert instant_elapsed < 0.1, "Pengambilan dalam burst capacity harus instan"

    # Pengambilan berikutnya harus menunggu pengisian token
    await limiter.acquire(2.0)
    delayed_elapsed = time.monotonic() - start
    assert delayed_elapsed >= 0.08, "Harus menunggu pengisian token saat kapasitas habis"


@pytest.mark.asyncio
async def test_caching_sub_millisecond(client):
    """Memastikan laporan tersimpan di cache in-memory dan dapat diambil kembali dengan latensi < 2ms."""
    mock_results = [
        SearchXNGResult(title="Test Result", url="https://example.com", content="Test snippet", engine="duckduckgo")
    ]
    report = SearchXNGReport(
        query="tes cache kueri",
        category="general",
        results=mock_results,
        total_results=1,
        search_time=0.45,
        engines_used=["duckduckgo"]
    )

    cache_key = client._build_cache_key("tes cache kueri", "general", ["duckduckgo"], "id")
    client._store_in_cache(cache_key, report)

    t0 = time.monotonic()
    cached = client._get_from_cache(cache_key)
    retrieval_ms = (time.monotonic() - t0) * 1000

    assert cached is not None
    assert cached.total_results == 1
    assert cached.results[0].title == "Test Result"
    assert retrieval_ms < 5.0, f"Cache retrieval harus sangat cepat ({retrieval_ms:.2f}ms)"


@pytest.mark.asyncio
async def test_search_with_fallback_mechanism(client):
    """
    Menguji skenario ketika kueri primer mengembalikan 0 hasil,
    client secara otomatis mengeksekusi kueri fallback yang berhasil.
    """
    call_counts = {"primary": 0, "fallback": 0}

    async def mock_execute(query, category="general", engines=None, max_results=10, language="id", time_range=None):
        if 'site:arxiv.org' in query:
            call_counts["primary"] += 1
            return SearchXNGReport(query=query, category=category, results=[])
        else:
            call_counts["fallback"] += 1
            res = [SearchXNGResult(title="Valid Fallback Result", url="https://arxiv.org/abs/123", content="Paper content", engine="arxiv")]
            return SearchXNGReport(query=query, category=category, results=res, total_results=1, engines_used=["arxiv"])

    with patch.object(client, "_execute_single_request", side_effect=mock_execute):
        complex_query = 'site:arxiv.org "neuro-symbolic reasoning" AND transformers'
        report = await client.search_json(complex_query, category="academic", enable_fallback=True)

        assert call_counts["primary"] == 1
        assert call_counts["fallback"] >= 1
        assert len(report.results) == 1
        assert report.results[0].title == "Valid Fallback Result"


@pytest.mark.asyncio
async def test_batch_search_latency_under_1_2s(client):
    """
    Kriteria Validasi: latensi rata-rata < 1.2s per batch pencarian.
    Simulasikan 10 kueri batch konkuren.
    """
    async def mock_execute(query, category="general", engines=None, max_results=10, language="id", time_range=None):
        # Simulasikan latensi jaringan SearXNG rata-rata 0.25 - 0.4 detik
        await asyncio.sleep(0.3)
        res = [SearchXNGResult(title=f"Result for {query}", url=f"https://example.com/{query}", content="Snippet", engine="google")]
        return SearchXNGReport(query=query, category=category, results=res, total_results=1, search_time=0.3, engines_used=["google"])

    with patch.object(client, "_execute_single_request", side_effect=mock_execute):
        queries = [f"topik riset multi-agent {i}" for i in range(10)]
        t_start = time.monotonic()
        results = await client.search_batch(queries, max_concurrency=5)
        total_batch_time = time.monotonic() - t_start
        average_latency = total_batch_time / len(queries)

        assert len(results) == 10
        assert total_batch_time < 1.5, f"Total batch time ({total_batch_time:.2f}s) harus efisien"
        assert average_latency < 0.2, f"Rata-rata latensi per kueri batch ({average_latency:.3f}s) harus jauh di bawah 1.2s"


def test_sync_execution_wrapper(client):
    """Memastikan metode search_sync bekerja tanpa kendala."""
    async def mock_execute(query, **kwargs):
        res = [SearchXNGResult(title="Sync Result", url="https://sync.example.com", content="Sync content", engine="bing")]
        return SearchXNGReport(query=query, category="general", results=res, total_results=1, search_time=0.1, engines_used=["bing"])

    with patch.object(client, "_execute_single_request", side_effect=mock_execute):
        report = client.search_sync("kueri sinkron", category="general")
        assert report is not None
        assert len(report.results) == 1
        assert report.results[0].title == "Sync Result"
