"""Provenance and watermarking utilities for MiroFish runs.

Provides:
- ``RunManifest``: immutable record of a simulation run (seed, spec hashes,
  model snapshot, tick range) for reproducibility auditing.
- ``ResponseCache`` / ``CachedLLM``: content-addressed LLM response cache
  guaranteeing deterministic replay (paper section 19.5).
- ``Watermark``: invisible (zero-width) provenance marker plus a visible
  EU AI Act Art.50-style synthetic-content label.
- ``ManifestStore``: persistence of manifests under ``runs/<run_id>/``.

Stdlib only (hashlib, json, uuid, pathlib, sqlite3, dataclasses).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization: sorted keys, tight separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def spec_hash(spec_yaml_str: str) -> str:
    """sha256 hex digest of a PlatformSpec YAML string."""
    return hashlib.sha256(spec_yaml_str.encode("utf-8")).hexdigest()


def content_hash(payload: Any) -> str:
    """sha256 hex digest of a payload's canonical JSON form."""
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass
class RunManifest:
    """Provenance record for a single simulation run."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    seed: int = 0
    model_snapshot_hash: str = ""
    spec_versions: dict[str, str] = field(default_factory=dict)
    parameter_values: dict[str, Any] = field(default_factory=dict)
    start_tick: int = 0
    end_tick: int = 0
    git_commit: Optional[str] = None

    def to_json(self) -> str:
        return _canonical_json(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "RunManifest":
        return cls(**json.loads(data))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResponseCache:
    """Content-addressed cache for LLM responses.

    Key = sha256 of canonical JSON {model, system, user, params}.
    Backends: file-backed JSONL (default ``cache.jsonl``) or in-memory
    sqlite (``":memory:"``).
    """

    def __init__(self, backend: Any = ":memory:") -> None:
        if backend == ":memory:" or backend is None:
            self._db: Optional[sqlite3.Connection] = sqlite3.connect(":memory:")
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, "
                "response TEXT NOT NULL)"
            )
            self._db.commit()
            self._path: Optional[Path] = None
        else:
            self._path = Path(backend)
            self._db = None
            self._ensure_file()

    def _ensure_file(self) -> None:
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def _key(
        self,
        model: str,
        system: str,
        user: str,
        params: Optional[dict[str, Any]] = None,
    ) -> str:
        return content_hash(
            {
                "model": model,
                "system": system,
                "user": user,
                "params": params or {},
            }
        )

    def _file_get(self, key: str) -> Optional[str]:
        assert self._path is not None
        if not self._path.exists():
            return None
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("key") == key:
                    return rec.get("response")
        return None

    def _file_put(self, key: str, response: str) -> None:
        assert self._path is not None
        self._ensure_file()
        # JSONL is append-only; last write wins on read order is not
        # guaranteed, so rewrite the whole file to keep latest value.
        records: dict[str, str] = {}
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if isinstance(rec.get("key"), str):
                        records[rec["key"]] = rec.get("response", "")
                except json.JSONDecodeError:
                    continue
        records[key] = response
        with self._path.open("w", encoding="utf-8") as fh:
            for k, v in records.items():
                fh.write(_canonical_json({"key": k, "response": v}) + "\n")

    def get(
        self,
        key: str,
        *,
        model: str = "",
        system: str = "",
        user: str = "",
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Fetch a cached response. ``key`` may be the raw cache key, or
        omitted-style lookup via model/system/user/params."""
        if key:
            lookup = key
        else:
            lookup = self._key(model, system, user, params)
        if self._db is not None:
            row = self._db.execute(
                "SELECT response FROM cache WHERE key = ?", (lookup,)
            ).fetchone()
            return row[0] if row else None
        return self._file_get(lookup)

    def put(
        self,
        key: str,
        response: str,
        *,
        model: str = "",
        system: str = "",
        user: str = "",
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        lookup = key or self._key(model, system, user, params)
        if self._db is not None:
            self._db.execute(
                "INSERT OR REPLACE INTO cache (key, response) VALUES (?, ?)",
                (lookup, response),
            )
            self._db.commit()
        else:
            self._file_put(lookup, response)

    def key_for(
        self,
        model: str,
        system: str,
        user: str,
        params: Optional[dict[str, Any]] = None,
    ) -> str:
        return self._key(model, system, user, params)

    def clear(self) -> None:
        if self._db is not None:
            self._db.execute("DELETE FROM cache")
            self._db.commit()
        elif self._path is not None and self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def __len__(self) -> int:
        if self._db is not None:
            row = self._db.execute("SELECT COUNT(*) FROM cache").fetchone()
            return int(row[0])
        if self._path is None or not self._path.exists():
            return 0
        n = 0
        with self._path.open("r", encoding="utf-8") as fh:
            seen: set[str] = set()
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if isinstance(rec.get("key"), str):
                        seen.add(rec["key"])
                except json.JSONDecodeError:
                    continue
        n = len(seen)
        return n


class CachedLLM:
    """LLM wrapper that consults a ``ResponseCache`` before invoking
    ``backend_fn``. Guarantees deterministic replay: identical inputs
    always yield the first-recorded response."""

    def __init__(
        self,
        backend_fn: Callable[..., str],
        cache: Optional[ResponseCache] = None,
        model: str = "default",
    ) -> None:
        self._backend_fn = backend_fn
        self.cache = cache if cache is not None else ResponseCache()
        self.model = model

    def generate(
        self,
        *,
        system: str = "",
        user: str = "",
        params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        key = self.cache.key_for(self.model, system, user, params)
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        # kwargs are folded into params so they affect the cache key.
        merged_params = dict(params or {})
        merged_params.update(kwargs)
        if merged_params != (params or {}):
            key = self.cache.key_for(self.model, system, user, merged_params)
            hit = self.cache.get(key)
            if hit is not None:
                return hit
        response = self._backend_fn(system=system, user=user, **merged_params)
        self.cache.put(key, response)
        return response


class Watermark:
    """Invisible + visible provenance markers for text artifacts.

    The invisible marker encodes ``run_id`` (UTF-8 bytes) as a bitstream of
    ZWNJ/ZWJ characters between sentinel delimiters, so ``extract`` can
    recover the run_id from generated text without visible alteration.
    """

    _START = "​"  # U+200B zero-width space sentinel start
    _END = "﻿"  # U+FEFF zero-width no-break space sentinel end
    _BIT_0 = "‌"  # U+200C ZWNJ
    _BIT_1 = "‍"  # U+200D ZWJ
    _PREFIX = "[AI-SYNTHETIC: mirofish/"
    _SUFFIX = "]"

    @classmethod
    def embed(cls, text: str, run_id: str) -> str:
        """Append an invisible zero-width marker encoding ``run_id``."""
        payload = run_id.encode("utf-8")
        bits = "".join(f"{b:08b}" for b in payload)
        marker = cls._START + "".join(
            cls._BIT_1 if bit == "1" else cls._BIT_0 for bit in bits
        ) + cls._END
        return text + marker

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        """Recover the embedded run_id, or ``None`` if no valid marker."""
        start = text.find(cls._START)
        if start == -1:
            return None
        payload = text[start + len(cls._START) :]
        end = payload.find(cls._END)
        if end == -1:
            return None
        payload = payload[:end]
        # Only ZWNJ/ZWJ are valid payload chars; anything else invalidates.
        if not payload or any(
            ch not in (cls._BIT_0, cls._BIT_1) for ch in payload
        ):
            return None
        bits = "".join("1" if ch == cls._BIT_1 else "0" for ch in payload)
        if len(bits) % 8 != 0:
            return None
        raw = bytes(
            int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)
        )
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return None

    @staticmethod
    def label(text: str, run_id: Optional[str] = None) -> str:
        """Visible EU AI Act Art.50-style synthetic-content label."""
        rid = run_id if run_id else "unknown"
        return f"[AI-SYNTHETIC: mirofish/{rid}] {text}"

    @classmethod
    def extract_label(cls, text: str) -> Optional[str]:
        """Parse run_id out of a visible label, if present."""
        if not text.startswith(cls._PREFIX):
            return None
        rest = text[len(cls._PREFIX) :]
        end = rest.find("]")
        if end == -1:
            return None
        return rest[:end] or None


class ManifestStore:
    """Persists ``RunManifest`` objects under ``runs/<run_id>/manifest.json``."""

    def __init__(self, root: Any = "runs") -> None:
        self.root = Path(root)

    def _path(self, run_id: str) -> Path:
        return self.root / run_id / "manifest.json"

    def save(self, manifest: RunManifest) -> Path:
        path = self._path(manifest.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest.to_json() + "\n", encoding="utf-8")
        return path

    def load(self, run_id: str) -> RunManifest:
        path = self._path(run_id)
        return RunManifest.from_json(path.read_text(encoding="utf-8"))

    def exists(self, run_id: str) -> bool:
        return self._path(run_id).exists()

    def list_run_ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(
            p.name for p in self.root.iterdir() if (p / "manifest.json").exists()
        )
