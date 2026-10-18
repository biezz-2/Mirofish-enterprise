"""Bounded, resumable embeddings for graph-building chunks.

The service is optional: when EMBEDDING_API_KEY is absent, callers can skip it.
It speaks the OpenAI-compatible /v1/embeddings contract used by 9Router.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from urllib import error, request
from ..utils.sqlite_engine import get_sqlite_connection

logger = logging.getLogger("mirofish.embedding")


@dataclass(frozen=True)
class EmbeddingConfig:
    base_url: str
    api_key: str
    model: str
    batch_size: int = 32
    concurrency: int = 4
    timeout_seconds: float = 60.0
    max_retries: int = 3
    cache_path: str = ".cache/mirofish-embeddings.sqlite3"


class EmbeddingService:
    """Embed text batches with bounded concurrency and durable hash caching."""

    def __init__(self, config: EmbeddingConfig):
        if not config.api_key:
            raise ValueError("Embedding API key is required")
        if not 1 <= config.batch_size <= 128:
            raise ValueError("embedding batch_size must be between 1 and 128")
        if not 1 <= config.concurrency <= 8:
            raise ValueError("embedding concurrency must be between 1 and 8")
        self.config = config
        self._db_lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        parent = os.path.dirname(os.path.abspath(self.config.cache_path))
        os.makedirs(parent, exist_ok=True)
        with get_sqlite_connection(self.config.cache_path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS embeddings ("
                "cache_key TEXT PRIMARY KEY, model TEXT NOT NULL, dimension INTEGER NOT NULL, vector TEXT NOT NULL, created_at REAL NOT NULL)"
            )
            db.commit()

    def _key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return hashlib.sha256(f"{self.config.model}:{digest}".encode("ascii")).hexdigest()

    def _get_cached(self, key: str) -> Optional[List[float]]:
        with get_sqlite_connection(self.config.cache_path) as db:
            row = db.execute("SELECT vector FROM embeddings WHERE cache_key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _put_cached(self, key: str, vector: List[float]) -> None:
        with self._db_lock, get_sqlite_connection(self.config.cache_path) as db:
            db.execute(
                "INSERT OR REPLACE INTO embeddings(cache_key, model, dimension, vector, created_at) VALUES (?, ?, ?, ?, ?)",
                (key, self.config.model, len(vector), json.dumps(vector, separators=(",", ":")), time.time()),
            )
            db.commit()

    def _request_batch(self, texts: Sequence[str]) -> List[List[float]]:
        payload = json.dumps({"model": self.config.model, "input": list(texts)}).encode("utf-8")
        url = self.config.base_url.rstrip("/") + "/v1/embeddings"
        last_error: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            req = request.Request(url, data=payload, method="POST", headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            })
            try:
                with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                    body = json.load(response)
                rows = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
                vectors = [row["embedding"] for row in rows]
                if len(vectors) != len(texts):
                    raise ValueError(f"embedding response count {len(vectors)} != request count {len(texts)}")
                return vectors
            except (error.HTTPError, error.URLError, TimeoutError, OSError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                time.sleep(min(8.0, 0.5 * (2 ** attempt)))
        raise RuntimeError(f"embedding batch failed after retries: {last_error}") from last_error

    def embed(self, texts: Sequence[str], progress: Optional[Callable[[int, int, int], None]] = None) -> Tuple[List[List[float]], int]:
        """Return vectors in input order and count remote requests.

        `progress(completed, total, cached)` is called after each batch.
        Failed batches raise instead of returning partial vectors.
        """
        values = list(texts)
        if not values:
            return [], 0
        vectors: List[Optional[List[float]]] = [None] * len(values)
        pending: List[Tuple[List[int], List[str]]] = []
        cached_count = 0
        for start in range(0, len(values), self.config.batch_size):
            indexes = list(range(start, min(start + self.config.batch_size, len(values))))
            missing: List[str] = []
            missing_indexes: List[int] = []
            for index in indexes:
                vector = self._get_cached(self._key(values[index]))
                if vector is None:
                    missing.append(values[index])
                    missing_indexes.append(index)
                else:
                    vectors[index] = vector
                    cached_count += 1
            if missing:
                pending.append((missing_indexes, missing))
            if progress:
                progress(sum(vector is not None for vector in vectors), len(values), cached_count)

        requests_count = 0
        with ThreadPoolExecutor(max_workers=self.config.concurrency) as pool:
            futures = {pool.submit(self._request_batch, texts_for_batch): (start, texts_for_batch) for start, texts_for_batch in pending}
            for future in as_completed(futures):
                indexes, texts_for_batch = futures[future]
                batch_vectors = future.result()
                if len(batch_vectors) != len(indexes):
                    raise RuntimeError("embedding response count does not match batch indexes")
                for index, vector in zip(indexes, batch_vectors):
                    vectors[index] = vector
                    self._put_cached(self._key(values[index]), vector)
                requests_count += 1
                if progress:
                    progress(sum(vector is not None for vector in vectors), len(values), cached_count)
        if any(vector is None for vector in vectors):
            raise RuntimeError("embedding pipeline produced incomplete output")
        return [vector for vector in vectors if vector is not None], requests_count


def configured_embedding_service(config: object) -> Optional[EmbeddingService]:
    key = os.environ.get("EMBEDDING_API_KEY") or os.environ.get("NINEROUTER_KEY")
    if not key:
        return None
    embedding_config = EmbeddingConfig(
        base_url=os.environ.get("EMBEDDING_BASE_URL", "https://9router.biezz.my.id"),
        api_key=key,
        model=os.environ.get("EMBEDDING_MODEL", "nvidia/nvidia/nv-embedqa-e5-v5"),
        batch_size=int(os.environ.get("EMBEDDING_BATCH_SIZE", "32")),
        concurrency=int(os.environ.get("EMBEDDING_CONCURRENCY", "4")),
        timeout_seconds=float(os.environ.get("EMBEDDING_TIMEOUT_SECONDS", "60")),
        max_retries=int(os.environ.get("EMBEDDING_MAX_RETRIES", "3")),
        cache_path=os.environ.get("EMBEDDING_CACHE_PATH", os.path.join(getattr(config, "UPLOAD_FOLDER", "."), "embedding-cache.sqlite3")),
    )
    return EmbeddingService(embedding_config)
