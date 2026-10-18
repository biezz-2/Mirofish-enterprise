# backend/app/services/simulation/ethics_guard.py
"""
Ethics Guard & Sandbox Safety Engine:
1. Sandbox Lock: Menolak keras koneksi atau percobaan posting ke API platform media sosial nyata.
2. Mandatory Metadata: Menyematkan 'is_synthetic: true' pada setiap konten.
3. Export Watermark: 'HASIL SIMULASI — BUKAN DATA NYATA' pada semua format ekspor.
4. Audit Log: Pencatatan append-only untuk setiap siklus eksekusi simulasi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional

WATERMARK_TEXT = "HASIL SIMULASI — BUKAN DATA NYATA"

FORBIDDEN_LIVE_API_DOMAINS = [
    "api.twitter.com",
    "api.x.com",
    "upload.twitter.com",
    "oauth.reddit.com",
    "www.reddit.com/api",
    "open.tiktokapis.com",
    "graph.facebook.com",
    "graph.instagram.com",
    "graph.threads.net",
    "api.linkedin.com",
    "www.googleapis.com/youtube/v3",
]


class SandboxViolationError(RuntimeError):
    """Pengecualian keamanan ketika simulasi mencoba menyentuh API dunia nyata."""
    pass


@dataclass
class AuditLogRecord:
    simulation_id: str
    timestamp: str
    event_count: int
    agent_count: int
    watermark: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EthicsGuard:
    """Penjaga etika, sandbox isolator, dan watermark injector."""

    def __init__(self, strict_sandbox: bool = True):
        self.strict_sandbox = strict_sandbox
        self._audit_log: List[AuditLogRecord] = []

    def verify_sandbox_safety(self, target_endpoint_or_url: str) -> None:
        """Memverifikasi bahwa target URL/endpoint bukan merupakan API langsung platform nyata."""
        if not self.strict_sandbox:
            return

        target_lower = target_endpoint_or_url.lower()
        for forbidden in FORBIDDEN_LIVE_API_DOMAINS:
            if forbidden in target_lower:
                raise SandboxViolationError(
                    f"[SANDBOX LOCK] Upaya koneksi ke API publik nyata terdeteksi: '{target_endpoint_or_url}'. "
                    f"Simulasi MiroFish hanya diizinkan berjalan di lingkungan terisolasi sintetis."
                )

    def attach_mandatory_metadata(
        self,
        item: Dict[str, Any],
        simulation_id: str,
    ) -> Dict[str, Any]:
        """Menyematkan metadata wajib is_synthetic: true dan watermark pada setiap item simulasi."""
        item["is_synthetic"] = True
        item["simulation_id"] = simulation_id
        item["simulation_watermark"] = WATERMARK_TEXT
        if "generated_at" not in item:
            item["generated_at"] = datetime.now(timezone.utc).isoformat()
        return item

    def apply_export_watermark(self, export_payload: Any) -> Any:
        """Menambahkan watermark eksplisit pada data sebelum diekspor keluar."""
        if isinstance(export_payload, str):
            header = f"# ==========================================\n# {WATERMARK_TEXT}\n# ==========================================\n\n"
            return header + export_payload

        if isinstance(export_payload, dict):
            copy_dict = export_payload.copy()
            copy_dict["__NOTICE__"] = WATERMARK_TEXT
            copy_dict["is_synthetic_dataset"] = True
            return copy_dict

        if isinstance(export_payload, list):
            return {
                "__NOTICE__": WATERMARK_TEXT,
                "is_synthetic_dataset": True,
                "data": export_payload,
            }

        return export_payload

    def record_audit(
        self,
        simulation_id: str,
        event_count: int,
        agent_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogRecord:
        """Mencatat sesi simulasi ke dalam audit log append-only."""
        rec = AuditLogRecord(
            simulation_id=simulation_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_count=event_count,
            agent_count=agent_count,
            watermark=WATERMARK_TEXT,
            metadata=metadata or {},
        )
        self._audit_log.append(rec)
        return rec

    def get_audit_records(self) -> List[Dict[str, Any]]:
        return [
            {
                "simulation_id": r.simulation_id,
                "timestamp": r.timestamp,
                "event_count": r.event_count,
                "agent_count": r.agent_count,
                "watermark": r.watermark,
                "metadata": r.metadata,
            }
            for r in self._audit_log
        ]
