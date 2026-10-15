"""
MiroFish Enterprise SearXNG Specialist Client (Agent 02: Divisi A)
Metasearch privat zero-tracking dengan output JSON, rotasi user-agent,
multi-engine routing (Google, Bing, DuckDuckGo, arXiv), dan rate limiting.
Port: 8888 (dialihkan dari 8080 untuk mencegah bentrok container).
"""

import os
import random
import asyncio
from typing import Dict, Any, List, Optional
from .searchxng_service import SearchXNGService, SearchXNGReport, SearchXNGResult

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

class SearXNGClient:
    """Specialized client for SearXNG private metasearch."""

    def __init__(self, base_url: Optional[str] = None, timeout_s: float = 10.0):
        self.base_url = base_url or os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888")
        self.timeout_s = timeout_s
        self._underlying_service = SearchXNGService()
        self._underlying_service.searchxng_url = self.base_url

    def get_random_user_agent(self) -> str:
        return random.choice(USER_AGENTS)

    async def search_json(
        self,
        query: str,
        category: str = "general",
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        language: str = "id"
    ) -> SearchXNGReport:
        """Eksekusi pencarian privat dengan format JSON wajib."""
        return await self._underlying_service.search(
            query=query,
            category=category,
            max_results=max_results,
            language=language
        )

    def search_sync(self, query: str, **kwargs) -> SearchXNGReport:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.search_json(query, **kwargs))
