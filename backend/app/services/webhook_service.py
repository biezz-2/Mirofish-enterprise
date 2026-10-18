"""
MiroFish Enterprise Distributed Webhook Engine (Agent 18: Divisi F)
Layanan Pengiriman Webhook Berkecepatan Tinggi:
- HMAC-SHA256 Payload Signature Generation & Verification (Anti-Replay Timestamp)
- Dead-Letter Queue (DLQ) dengan Replay / Re-drive & Inspection
- Retry Eksponensial dengan Jitter (P95 latency < 250ms target)
- Registri Langganan Webhook (Subscription Management & Broadcast)
- Kompatibilitas skema OpenAPI 3.1.0 / JSON Schema 2020-12
"""

import hmac
import json
import time
import uuid
import random
import hashlib
import logging
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger('mirofish.webhook')


class WebhookDeliveryAttempt(BaseModel):
    attempt_num: int
    timestamp: str
    status_code: Optional[int] = None
    success: bool
    error: Optional[str] = None
    duration_ms: float = 0.0


class WebhookEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:16]}")
    event_type: str
    payload: Dict[str, Any]
    target_url: Optional[str] = None
    secret_key: Optional[str] = "mirofish_default_secret_key"
    subscription_id: Optional[str] = None
    status: str = "PENDING"  # PENDING, DELIVERED, FAILED, DLQ
    attempts: List[WebhookDeliveryAttempt] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signature: Optional[str] = None
    timestamp: Optional[str] = None


class WebhookSubscription(BaseModel):
    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    target_url: str
    secret_key: str = Field(default_factory=lambda: f"whsec_{uuid.uuid4().hex}")
    subscribed_events: List[str] = Field(default_factory=lambda: ["*"])
    is_active: bool = True
    headers: Dict[str, str] = Field(default_factory=dict)
    description: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebhookDispatchResult(BaseModel):
    is_success: bool
    delivery_id: str
    status_code: Optional[int] = None
    attempts: int = 1
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    def __bool__(self) -> bool:
        return self.is_success


class WebhookDLQStats(BaseModel):
    total_dispatched: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    dlq_count: int = 0
    active_subscriptions: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0


class WebhookDispatcher:
    """High-performance distributed webhook dispatcher with HMAC signature, DLQ & Retries."""

    def __init__(
        self,
        max_retries: int = 3,
        timeout_s: float = 3.0,
        backoff_factor: float = 0.05,
        max_backoff_s: float = 2.0,
        initial_backoff_s: Optional[float] = None,
        backoff_multiplier: float = 2.0
    ):
        self.max_retries = max_retries
        self.timeout_s = timeout_s
        self.backoff_factor = initial_backoff_s if initial_backoff_s is not None else backoff_factor
        self.initial_backoff_s = self.backoff_factor
        self.max_backoff_s = max_backoff_s
        self.backoff_multiplier = backoff_multiplier
        self.dlq: List[WebhookEvent] = []
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.latencies_ms: List[float] = []
        self.total_dispatched: int = 0
        self.total_delivered: int = 0
        self.total_failed: int = 0
        self._lock = threading.RLock()
        self._in_memory_test_mode: bool = False
        self._simulated_latency_ms: float = 10.0
        self._simulated_failure_rate: float = 0.0

    def enable_in_memory_test_mode(self, simulated_latency_ms: float = 10.0, simulated_failure_rate: float = 0.0) -> None:
        """Aktifkan mode simulasi in-memory untuk benchmark latensi dan deterministic testing."""
        self._in_memory_test_mode = True
        self._simulated_latency_ms = simulated_latency_ms
        self._simulated_failure_rate = simulated_failure_rate

    def disable_in_memory_test_mode(self) -> None:
        """Nonaktifkan mode simulasi in-memory."""
        self._in_memory_test_mode = False

    def compute_backoff_delay(self, attempt: int) -> float:
        """Hitung jeda exponential backoff dengan full jitter (AWS / RFC standard recommendation)."""
        max_possible = min(self.max_backoff_s, self.backoff_factor * (self.backoff_multiplier ** (attempt - 1)))
        return random.uniform(0.0, max_possible)

    @staticmethod
    def generate_hmac_signature(
        payload_json: Union[str, bytes],
        secret_key: str,
        timestamp: Optional[Union[str, int, float]] = None
    ) -> str:
        """Menghasilkan tanda tangan HMAC-SHA256 untuk payload webhook."""
        secret_bytes = secret_key.encode('utf-8') if isinstance(secret_key, str) else secret_key
        payload_bytes = payload_json.encode('utf-8') if isinstance(payload_json, str) else payload_json
        signature = hmac.new(
            secret_bytes,
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @classmethod
    def verify_hmac_signature(
        cls,
        payload_json: Union[str, bytes],
        secret_key: str,
        signature: str,
        timestamp: Optional[Union[str, int, float]] = None,
        tolerance_seconds: int = 300
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifikasi tanda tangan HMAC-SHA256 dengan proteksi anti-replay timestamp.
        Returns: (is_valid, error_reason)
        """
        if not signature:
            return False, "Missing signature"
        if not secret_key:
            return False, "Missing secret key"

        # Timestamp verification (Anti-Replay Attack)
        if timestamp:
            try:
                # Try ISO format or numeric timestamp
                if isinstance(timestamp, (int, float)) or (isinstance(timestamp, str) and timestamp.replace('.', '', 1).isdigit()):
                    ts_float = float(timestamp)
                    ts_dt = datetime.fromtimestamp(ts_float, tz=timezone.utc)
                else:
                    ts_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                now = datetime.now(timezone.utc)
                diff = abs((now - ts_dt).total_seconds())
                if diff > tolerance_seconds:
                    return False, f"Timestamp expired or out of tolerance ({diff:.1f}s > {tolerance_seconds}s)"
            except Exception as e:
                return False, f"Invalid timestamp format: {str(e)}"

        payload_str = payload_json if isinstance(payload_json, str) else payload_json.decode('utf-8')
        expected_sig = cls.generate_hmac_signature(payload_str, secret_key)
        
        # Format comparison: handle both 'sha256=...' and raw hex
        sig_to_compare = signature.strip()
        expected_to_compare = expected_sig
        if not sig_to_compare.startswith("sha256="):
            sig_to_compare = f"sha256={sig_to_compare}"

        is_valid = hmac.compare_digest(expected_to_compare, sig_to_compare)
        if not is_valid:
            return False, "Signature mismatch"
        return True, None

    def register_subscription(
        self,
        target_url: str,
        secret_key: Optional[str] = None,
        subscribed_events: Optional[List[str]] = None,
        description: str = "",
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookSubscription:
        """Daftarkan langganan webhook baru."""
        with self._lock:
            sub = WebhookSubscription(
                target_url=target_url,
                secret_key=secret_key or f"whsec_{uuid.uuid4().hex}",
                subscribed_events=subscribed_events or ["*"],
                description=description,
                headers=headers or {}
            )
            self.subscriptions[sub.subscription_id] = sub
            logger.info(f"Registered webhook subscription {sub.subscription_id} -> {sub.target_url}")
            return sub

    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Ambil data langganan webhook berdasarkan ID."""
        with self._lock:
            return self.subscriptions.get(subscription_id)

    def list_subscriptions(self, active_only: bool = False) -> List[WebhookSubscription]:
        """Daftar semua langganan webhook."""
        with self._lock:
            subs = list(self.subscriptions.values())
            if active_only:
                subs = [s for s in subs if s.is_active]
            return subs

    def delete_subscription(self, subscription_id: str) -> bool:
        """Hapus langganan webhook."""
        with self._lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                return True
            return False

    def dispatch(
        self,
        target_or_event: Union[str, WebhookEvent],
        maybe_event: Optional[WebhookEvent] = None
    ) -> WebhookDispatchResult:
        """
        Kirim webhook ke endpoint target dengan retry eksponensial.
        Mendukung pemanggilan:
          - dispatch(event: WebhookEvent)
          - dispatch(url: str, event: WebhookEvent)
        """
        if isinstance(target_or_event, str):
            target_url = target_or_event
            event = maybe_event or WebhookEvent(
                event_type="GENERIC_EVENT",
                payload={},
                target_url=target_url
            )
            event.target_url = target_url
        else:
            event = target_or_event
            target_url = event.target_url or "http://127.0.0.1:8000/api/webhooks/mock"

        with self._lock:
            self.total_dispatched += 1

        payload_str = json.dumps(event.payload, sort_keys=True)
        secret_key = event.secret_key or "mirofish_default_secret_key"
        signature = self.generate_hmac_signature(payload_str, secret_key)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        event.signature = signature
        event.timestamp = now_iso
        delivery_id = f"del_{uuid.uuid4().hex[:16]}"

        headers = {
            "Content-Type": "application/json",
            "X-Mirofish-Signature": signature,
            "X-Signature-SHA256": signature,
            "X-Mirofish-Timestamp": now_iso,
            "X-Mirofish-Event": event.event_type,
            "X-Mirofish-Delivery": delivery_id,
            "User-Agent": "Mirofish-Enterprise-Webhook/3.2"
        }

        # Inject subscription custom headers if present
        if event.subscription_id and event.subscription_id in self.subscriptions:
            sub = self.subscriptions[event.subscription_id]
            headers.update(sub.headers)

        body = payload_str.encode('utf-8')
        backoff = self.backoff_factor
        last_error: Optional[str] = None
        last_status_code: Optional[int] = None
        start_time_all = time.perf_counter()

        max_attempts = 1 + self.max_retries
        for attempt in range(1, max_attempts + 1):
            t0 = time.perf_counter()
            if self._in_memory_test_mode:
                if self._simulated_latency_ms > 0:
                    time.sleep(self._simulated_latency_ms / 1000.0)
                if random.random() < self._simulated_failure_rate:
                    duration_ms = (time.perf_counter() - t0) * 1000.0
                    last_status_code = 500
                    last_error = "Simulated delivery failure in in-memory test mode"
                    event.attempts.append(WebhookDeliveryAttempt(
                        attempt_num=attempt,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        status_code=500,
                        success=False,
                        error=last_error,
                        duration_ms=duration_ms
                    ))
                else:
                    duration_ms = (time.perf_counter() - t0) * 1000.0
                    total_duration_ms = (time.perf_counter() - start_time_all) * 1000.0
                    event.status = "DELIVERED"
                    event.attempts.append(WebhookDeliveryAttempt(
                        attempt_num=attempt,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        status_code=200,
                        success=True,
                        duration_ms=duration_ms
                    ))
                    with self._lock:
                        self.total_delivered += 1
                        self.latencies_ms.append(total_duration_ms)
                        if len(self.latencies_ms) > 1000:
                            self.latencies_ms = self.latencies_ms[-1000:]
                    return WebhookDispatchResult(
                        is_success=True,
                        delivery_id=delivery_id,
                        status_code=200,
                        attempts=attempt,
                        duration_ms=total_duration_ms
                    )
            else:
                try:
                    req = urllib.request.Request(target_url, data=body, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                        duration_ms = (time.perf_counter() - t0) * 1000.0
                        total_duration_ms = (time.perf_counter() - start_time_all) * 1000.0
                        
                        if 200 <= resp.status < 300:
                            event.status = "DELIVERED"
                            event.attempts.append(WebhookDeliveryAttempt(
                                attempt_num=attempt,
                                timestamp=datetime.now(timezone.utc).isoformat(),
                                status_code=resp.status,
                                success=True,
                                duration_ms=duration_ms
                            ))
                            with self._lock:
                                self.total_delivered += 1
                                self.latencies_ms.append(total_duration_ms)
                                if len(self.latencies_ms) > 1000:
                                    self.latencies_ms = self.latencies_ms[-1000:]
                            return WebhookDispatchResult(
                                is_success=True,
                                delivery_id=delivery_id,
                                status_code=resp.status,
                                attempts=attempt,
                                duration_ms=total_duration_ms
                            )
                        else:
                            last_status_code = resp.status
                            last_error = f"HTTP {resp.status}"
                except urllib.error.HTTPError as e:
                    duration_ms = (time.perf_counter() - t0) * 1000.0
                    last_status_code = e.code
                    last_error = f"HTTP {e.code}: {e.reason}"
                    event.attempts.append(WebhookDeliveryAttempt(
                        attempt_num=attempt,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        status_code=e.code,
                        success=False,
                        error=last_error,
                        duration_ms=duration_ms
                    ))
                    # Client errors (4xx) should not be retried as they indicate bad payload/auth
                    if 400 <= e.code < 500:
                        break
                except Exception as e:
                    duration_ms = (time.perf_counter() - t0) * 1000.0
                    last_error = str(e)
                    event.attempts.append(WebhookDeliveryAttempt(
                        attempt_num=attempt,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        success=False,
                        error=last_error,
                        duration_ms=duration_ms
                    ))

            if attempt < max_attempts:
                delay = self.compute_backoff_delay(attempt)
                time.sleep(delay)

        # Seluruh percobaan gagal: masukkan ke Dead-Letter Queue (DLQ)
        total_duration_ms = (time.perf_counter() - start_time_all) * 1000.0
        event.status = "DLQ"
        with self._lock:
            self.total_failed += 1
            self.dlq.append(event)
            # Batasi ukuran memori DLQ maksimal 500 event
            if len(self.dlq) > 500:
                self.dlq.pop(0)

        logger.warning(
            f"Webhook {event.event_id} ({event.event_type}) gagal setelah {len(event.attempts)} percobaan, "
            f"dipindahkan ke DLQ: {last_error}"
        )
        return WebhookDispatchResult(
            is_success=False,
            delivery_id=delivery_id,
            status_code=last_status_code,
            attempts=len(event.attempts),
            error_message=last_error,
            duration_ms=total_duration_ms
        )

    def dispatch_async(
        self,
        target_or_event: Union[str, WebhookEvent],
        maybe_event: Optional[WebhookEvent] = None
    ) -> threading.Thread:
        """Kirim webhook secara non-blocking di latar belakang."""
        thread = threading.Thread(
            target=self.dispatch,
            args=(target_or_event, maybe_event),
            daemon=True
        )
        thread.start()
        return thread

    def broadcast(
        self,
        event_type: str,
        payload: Dict[str, Any],
        async_mode: bool = False
    ) -> List[WebhookDispatchResult]:
        """
        Kirim event ke seluruh langganan aktif yang sesuai dengan tipe event.
        """
        with self._lock:
            matching_subs = [
                sub for sub in self.subscriptions.values()
                if sub.is_active and ("*" in sub.subscribed_events or event_type in sub.subscribed_events)
            ]

        results: List[WebhookDispatchResult] = []
        for sub in matching_subs:
            evt = WebhookEvent(
                event_type=event_type,
                payload=payload,
                target_url=sub.target_url,
                secret_key=sub.secret_key,
                subscription_id=sub.subscription_id
            )
            if async_mode:
                self.dispatch_async(evt)
                results.append(WebhookDispatchResult(
                    is_success=True,
                    delivery_id=f"del_async_{evt.event_id}",
                    attempts=0
                ))
            else:
                res = self.dispatch(evt)
                results.append(res)
        return results

    def get_dlq(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Inspeksi item dalam Dead-Letter Queue."""
        with self._lock:
            items = self.dlq
            if event_type:
                items = [e for e in items if e.event_type == event_type]
            selected = items[offset:offset + limit]
            result = []
            for e in selected:
                d = e.model_dump()
                d["event"] = e.model_dump()
                d["attempts"] = len(e.attempts)
                result.append(d)
            return result

    def replay_dlq_event(self, event_id: str) -> WebhookDispatchResult:
        """Coba kirim ulang event spesifik dari DLQ."""
        with self._lock:
            target_event = None
            target_idx = -1
            for idx, e in enumerate(self.dlq):
                if e.event_id == event_id:
                    target_event = e
                    target_idx = idx
                    break

            if not target_event:
                return WebhookDispatchResult(
                    is_success=False,
                    delivery_id=f"del_notfound_{event_id}",
                    error_message=f"Event {event_id} not found in DLQ"
                )

        # Coba kirim ulang
        res = self.dispatch(target_event)
        if res.is_success:
            with self._lock:
                if target_idx < len(self.dlq) and self.dlq[target_idx].event_id == event_id:
                    self.dlq.pop(target_idx)
                logger.info(f"DLQ event {event_id} berhasil dikirim ulang dan dihapus dari DLQ.")
        return res

    def replay_all_dlq(self) -> List[WebhookDispatchResult]:
        """Coba kirim ulang seluruh event yang tertampung di DLQ."""
        with self._lock:
            events_to_replay = list(self.dlq)

        results = []
        for event in events_to_replay:
            res = self.replay_dlq_event(event.event_id)
            results.append(res)
        return results

    def clear_dlq(self) -> int:
        """Bersihkan seluruh isi DLQ."""
        with self._lock:
            count = len(self.dlq)
            self.dlq.clear()
            return count

    def delete_dlq_event(self, event_id: str) -> bool:
        """Hapus event tertentu dari DLQ."""
        with self._lock:
            for idx, e in enumerate(self.dlq):
                if e.event_id == event_id:
                    self.dlq.pop(idx)
                    return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Hitung statistik performa dan latensi P95 dispatcher."""
        with self._lock:
            lats = sorted(self.latencies_ms)
            p95 = 0.0
            avg_lat = 0.0
            if lats:
                idx = int(len(lats) * 0.95)
                idx = min(idx, len(lats) - 1)
                p95 = round(lats[idx], 2)
                avg_lat = round(sum(lats) / len(lats), 2)

            return {
                "total_dispatched": self.total_dispatched,
                "total_delivered": self.total_delivered,
                "total_failed": self.total_failed,
                "dlq_count": len(self.dlq),
                "active_subscriptions": len([s for s in self.subscriptions.values() if s.is_active]),
                "avg_latency_ms": avg_lat,
                "p95_latency_ms": p95,
                "max_retries": self.max_retries,
                "timeout_s": self.timeout_s
            }


# Global singleton dispatcher instance
webhook_dispatcher = WebhookDispatcher()
