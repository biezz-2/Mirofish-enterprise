"""Bounded, resumable embeddings for graph-building chunks.

Priority #1: Google TPU (bge-m3, 1024 dims) via 9Router.
Priority #2: Automatic failover to secondary configured endpoint if TPU is offline/5xx/timeout.
It speaks the OpenAI-compatible /v1/embeddings contract.
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
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib import error, request
from ..utils.sqlite_engine import get_sqlite_connection

logger = logging.getLogger("mirofish.embedding")


@dataclass(frozen=True)
class EmbeddingConfig:
    # Priority #1 (Primary - Google TPU)
    base_url: str
    api_key: str
    model: str
    dimensions: Optional[int] = 1024
    batch_size: int = 32
    concurrency: int = 4
    timeout_seconds: float = 30.0
    max_retries: int = 2
    cache_path: str = ".cache/mirofish-embeddings.sqlite3"

    # Priority #2 (Fallback when Priority #1 is offline / error)
    fallback_base_url: Optional[str] = None
    fallback_api_key: Optional[str] = None
    fallback_model: Optional[str] = None
    fallback_dimensions: Optional[int] = 1024
    fallback_timeout_seconds: float = 30.0
    cooldown_seconds: float = 60.0


class EmbeddingService:
    """Embed text batches with bounded concurrency, durable hash caching, and TPU failover."""

    def __init__(self, config: EmbeddingConfig):
        if not config.api_key:
            raise ValueError("Embedding API key is required")
        if not 1 <= config.batch_size <= 128:
            raise ValueError("embedding batch_size must be between 1 and 128")
        if not 1 <= config.concurrency <= 8:
            raise ValueError("embedding concurrency must be between 1 and 8")
        self.config = config
        self._db_lock = threading.Lock()
        self._health_lock = threading.Lock()
        self._primary_unhealthy_until: float = 0.0
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

    def is_primary_healthy(self) -> bool:
        with self._health_lock:
            return time.time() >= self._primary_unhealthy_until

    def mark_primary_unhealthy(self, duration: Optional[float] = None) -> None:
        cooldown = duration if duration is not None else self.config.cooldown_seconds
        with self._health_lock:
            self._primary_unhealthy_until = time.time() + cooldown
        logger.warning(
            "Primary embedding endpoint (%s, model=%s) marked offline for %.1fs. Routing to fallback.",
            self.config.base_url,
            self.config.model,
            cooldown,
        )

    def mark_primary_healthy(self) -> None:
        with self._health_lock:
            if self._primary_unhealthy_until > 0.0:
                logger.info("Primary embedding endpoint (%s) restored to healthy status.", self.config.base_url)
                self._primary_unhealthy_until = 0.0

    def has_fallback(self) -> bool:
        return bool(self.config.fallback_base_url and self.config.fallback_api_key and self.config.fallback_model)

    def _key(self, text: str, model_name: Optional[str] = None) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        m = model_name or self.config.model
        return hashlib.sha256(f"{m}:{digest}".encode("ascii")).hexdigest()

    def _get_cached(self, key: str) -> Optional[List[float]]:
        with get_sqlite_connection(self.config.cache_path) as db:
            row = db.execute("SELECT vector FROM embeddings WHERE cache_key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _put_cached(self, key: str, model_name: str, vector: List[float]) -> None:
        with self._db_lock, get_sqlite_connection(self.config.cache_path) as db:
            db.execute(
                "INSERT OR REPLACE INTO embeddings(cache_key, model, dimension, vector, created_at) VALUES (?, ?, ?, ?, ?)",
                (key, model_name, len(vector), json.dumps(vector, separators=(",", ":")), time.time()),
            )
            db.commit()

    def _execute_http_batch(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: Optional[int],
        timeout_seconds: float,
        texts: Sequence[str],
    ) -> List[List[float]]:
        payload_dict: Dict[str, Any] = {
            "model": model,
            "input": list(texts),
        }
        if dimensions:
            payload_dict["dimensions"] = dimensions
        payload = json.dumps(payload_dict).encode("utf-8")
        url = base_url.rstrip("/") + "/v1/embeddings"

        req = request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "MiroFish-Enterprise/3.6 (TPU-Embedding-Client)",
            },
        )
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = json.load(response)

        rows = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
        vectors = [row["embedding"] for row in rows]
        if len(vectors) != len(texts):
            raise ValueError(f"embedding response count {len(vectors)} != request count {len(texts)}")
        return vectors

    def _request_batch(self, texts: Sequence[str]) -> Tuple[List[List[float]], str]:
        """Request embedding for a batch of texts with TPU Priority #1 and automatic failover."""
        primary_healthy = self.is_primary_healthy()
        last_primary_error: Optional[Exception] = None

        if primary_healthy:
            for attempt in range(self.config.max_retries + 1):
                try:
                    vectors = self._execute_http_batch(
                        base_url=self.config.base_url,
                        api_key=self.config.api_key,
                        model=self.config.model,
                        dimensions=self.config.dimensions,
                        timeout_seconds=self.config.timeout_seconds,
                        texts=texts,
                    )
                    self.mark_primary_healthy()
                    return vectors, self.config.model
                except (error.HTTPError, error.URLError, TimeoutError, OSError, KeyError, ValueError) as exc:
                    last_primary_error = exc
                    if attempt < self.config.max_retries:
                        time.sleep(min(4.0, 0.4 * (2 ** attempt)))

            # Primary exhausted retries, mark unhealthy
            self.mark_primary_unhealthy()

        # If primary is unhealthy or failed, try fallback
        if self.has_fallback():
            logger.warning(
                "Attempting fallback embedding via %s (model=%s) due to primary failure/offline: %s",
                self.config.fallback_base_url,
                self.config.fallback_model,
                last_primary_error or "primary in cooldown",
            )
            try:
                vectors = self._execute_http_batch(
                    base_url=self.config.fallback_base_url,  # type: ignore[arg-type]
                    api_key=self.config.fallback_api_key,    # type: ignore[arg-type]
                    model=self.config.fallback_model,        # type: ignore[arg-type]
                    dimensions=self.config.fallback_dimensions,
                    timeout_seconds=self.config.fallback_timeout_seconds,
                    texts=texts,
                )
                return vectors, self.config.fallback_model  # type: ignore[return-value]
            except Exception as fb_exc:
                logger.error("Fallback embedding endpoint also failed: %s", fb_exc)
                raise RuntimeError(
                    f"Both primary ({last_primary_error}) and fallback ({fb_exc}) embedding endpoints failed"
                ) from fb_exc

        raise RuntimeError(f"Primary embedding batch failed and no fallback available: {last_primary_error}") from last_primary_error

    def embed(
        self,
        texts: Sequence[str],
        progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> Tuple[List[List[float]], int]:
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

        # Check cache under primary model key first
        for start in range(0, len(values), self.config.batch_size):
            indexes = list(range(start, min(start + self.config.batch_size, len(values))))
            missing: List[str] = []
            missing_indexes: List[int] = []
            for index in indexes:
                vector = self._get_cached(self._key(values[index], self.config.model))
                if vector is None and self.has_fallback() and self.config.fallback_model != self.config.model:
                    # Also check fallback model cache if primary not cached
                    vector = self._get_cached(self._key(values[index], self.config.fallback_model))

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
        if pending:
            with ThreadPoolExecutor(max_workers=self.config.concurrency) as pool:
                futures = {
                    pool.submit(self._request_batch, texts_for_batch): (batch_indexes, texts_for_batch)
                    for batch_indexes, texts_for_batch in pending
                }
                for future in as_completed(futures):
                    indexes, texts_for_batch = futures[future]
                    batch_vectors, used_model = future.result()
                    if len(batch_vectors) != len(indexes):
                        raise RuntimeError("embedding response count does not match batch indexes")
                    for index, vector in zip(indexes, batch_vectors):
                        vectors[index] = vector
                        self._put_cached(self._key(values[index], used_model), used_model, vector)
                    requests_count += 1
                    if progress:
                        progress(sum(vector is not None for vector in vectors), len(values), cached_count)

        if any(vector is None for vector in vectors):
            raise RuntimeError("embedding pipeline produced incomplete output")
        return [vector for vector in vectors if vector is not None], requests_count


def configured_embedding_service(config: object = None) -> Optional[EmbeddingService]:
    """Factory creating EmbeddingService with TPU Google bge-m3 as Priority #1 and automatic failover."""
    # Priority #1 Primary Credentials (Google TPU bge-m3)
    primary_key = (
        os.environ.get("EMBEDDING_PRIMARY_API_KEY")
        or os.environ.get("EMBEDDING_API_KEY")
        or "sk-dc3493f22a937c2c-h5uphp-1f3ca706"
    )
    primary_base_url = (
        os.environ.get("EMBEDDING_PRIMARY_BASE_URL")
        or os.environ.get("EMBEDDING_BASE_URL")
        or "https://9router.biezz.my.id"
    )
    primary_model = (
        os.environ.get("EMBEDDING_PRIMARY_MODEL")
        or os.environ.get("EMBEDDING_MODEL")
        or "bge-m3/bge-m3"
    )
    primary_dimensions = int(
        os.environ.get("EMBEDDING_PRIMARY_DIMENSIONS")
        or os.environ.get("EMBEDDING_DIMENSIONS")
        or "1024"
    )

    if not primary_key:
        return None

    # Priority #2 Fallback Credentials (Local/Secondary Router)
    fallback_base_url = (
        os.environ.get("EMBEDDING_FALLBACK_BASE_URL")
        or os.environ.get("LLM_BASE_URL", "http://192.168.101.19:20128/v1").replace("/v1", "")
    )
    fallback_key = (
        os.environ.get("EMBEDDING_FALLBACK_API_KEY")
        or os.environ.get("LLM_API_KEY")
        or os.environ.get("NINEROUTER_KEY")
        or "sk-dc3493f22a937c2c-k2u58l-151dece0"
    )
    fallback_model = os.environ.get("EMBEDDING_FALLBACK_MODEL", "bge-m3/bge-m3")
    fallback_dim_str = os.environ.get("EMBEDDING_FALLBACK_DIMENSIONS", "1024")
    fallback_dimensions = int(fallback_dim_str) if fallback_dim_str else None

    cache_dir = getattr(config, "UPLOAD_FOLDER", ".") if config else "."
    cache_path = os.environ.get(
        "EMBEDDING_CACHE_PATH",
        os.path.join(cache_dir, "embedding-cache.sqlite3"),
    )

    embedding_config = EmbeddingConfig(
        base_url=primary_base_url,
        api_key=primary_key,
        model=primary_model,
        dimensions=primary_dimensions,
        batch_size=int(os.environ.get("EMBEDDING_BATCH_SIZE", "32")),
        concurrency=int(os.environ.get("EMBEDDING_CONCURRENCY", "4")),
        timeout_seconds=float(os.environ.get("EMBEDDING_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.environ.get("EMBEDDING_MAX_RETRIES", "2")),
        cache_path=cache_path,
        fallback_base_url=fallback_base_url,
        fallback_api_key=fallback_key,
        fallback_model=fallback_model,
        fallback_dimensions=fallback_dimensions,
        fallback_timeout_seconds=float(os.environ.get("EMBEDDING_FALLBACK_TIMEOUT_SECONDS", "30")),
        cooldown_seconds=float(os.environ.get("EMBEDDING_COOLDOWN_SECONDS", "60")),
    )
    return EmbeddingService(embedding_config)
