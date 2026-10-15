"""
MiroFish Enterprise Discord Monitoring & Event Reporter (Agent 20 & Agent 01)
Protokol Pemantauan Discord Real-time sesuai Master Plan v3.2 Bagian 6 & 7.
Menyediakan fire-and-forget event queue, local JSONL logging, kepatuhan rate limit,
dan skema embed terstandarisasi untuk 20 subagent.
"""

import os
import sys
import json
import time
import queue
import hashlib
import logging
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("discord_reporter")

EVENT_COLORS = {
    "AGENT_START": 0x5865F2,
    "TASK_PROGRESS": 0x57F287,
    "ARTIFACT_READY": 0x00B0F4,
    "PHASE_GATE": 0xFEE75C,
    "BLOCKED": 0xED4245,
    "CRASH_RECOVERY": 0xE67E22,
    "HEARTBEAT": 0x99AAB5,
    "WATCHDOG_ALERT": 0xA11A1A,
}

LOGS_DIR = os.path.expanduser("~/.state/logs")

class DiscordReporter:
    """Singleton reporter for asynchronous event queuing and Discord dispatch."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue(maxsize=10000)
        self._recent_hashes: Dict[str, float] = {}  # sha256 -> timestamp (dedup 10 min)
        self._lock = threading.Lock()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        os.makedirs(LOGS_DIR, exist_ok=True)

    def _get_credentials(self) -> Dict[str, str]:
        """Ambil token bot atau webhook URL dari vault atau environment."""
        token = os.environ.get("DISCORD_BOT_TOKEN")
        webhook = os.environ.get("DISCORD_WEBHOOK_URL")
        
        # Cek ~/.hermes/.env jika env belum diisi
        if not token:
            env_file = os.path.expanduser("~/.hermes/.env")
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r") as f:
                        for line in f:
                            if line.startswith("DISCORD_BOT_TOKEN="):
                                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                                break
                except Exception:
                    pass
        return {"bot_token": token or "", "webhook_url": webhook or ""}

    def emit_event(
        self,
        event_type: str,
        agent_id: str,
        division: str,
        status: str = "IN_PROGRESS",
        title_suffix: str = "",
        artifact_path: Optional[str] = None,
        sha256_hash: Optional[str] = None,
        nli_score: Optional[float] = None,
        next_action: Optional[str] = None,
        extra_fields: Optional[List[Dict[str, Any]]] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """Kirim event terstruktur ke antrian dan catat ke JSONL lokal."""
        now_iso = datetime.now(timezone.utc).isoformat()
        color = EVENT_COLORS.get(event_type, 0x5865F2)
        title = f"{event_type} | {agent_id} | {title_suffix or division}"

        fields = [
            {"name": "agent", "value": agent_id, "inline": True},
            {"name": "divisi", "value": division, "inline": True},
            {"name": "status", "value": status, "inline": True},
        ]

        if artifact_path:
            fields.append({"name": "artefak", "value": artifact_path, "inline": False})
        if sha256_hash:
            fields.append({"name": "hash", "value": f"sha256:{sha256_hash[:16]}...", "inline": True})
        if nli_score is not None:
            fields.append({"name": "nli", "value": f"{nli_score:.2f}", "inline": True})
        if next_action:
            fields.append({"name": "next", "value": next_action, "inline": False})

        if extra_fields:
            for f in extra_fields:
                if len(fields) < 25:
                    fields.append(f)

        embed = {
            "title": title[:256],
            "color": color,
            "fields": fields[:25],
            "footer": {"text": "mirofish-enterprise | board:project-mirofish-enterprise-notion"},
            "timestamp": now_iso,
        }

        event_payload = {
            "event_type": event_type,
            "agent_id": agent_id,
            "division": division,
            "status": status,
            "embed": embed,
            "thread_id": thread_id,
            "timestamp": now_iso,
        }

        # Deduping 10 menit
        payload_bytes = json.dumps(embed, sort_keys=True).encode("utf-8")
        event_hash = hashlib.sha256(payload_bytes).hexdigest()
        now = time.time()

        with self._lock:
            # Bersihkan cache dedup lama
            self._recent_hashes = {h: t for h, t in self._recent_hashes.items() if now - t < 600}
            if event_hash in self._recent_hashes and event_type not in ["WATCHDOG_ALERT", "BLOCKED"]:
                return event_hash
            self._recent_hashes[event_hash] = now

        # 1. Catat ke file JSONL lokal (sinkron & nir-kehilangan)
        self._write_local_log(agent_id, event_payload)

        # 2. Masukkan ke queue asinkron untuk dikirim ke Discord
        try:
            self._queue.put_nowait(event_payload)
        except queue.Full:
            logger.warning("Discord reporter queue is full, dropping event")

        return event_hash

    def _write_local_log(self, agent_id: str, payload: Dict[str, Any]):
        try:
            global_log = os.path.join(LOGS_DIR, "events.jsonl")
            agent_log = os.path.join(LOGS_DIR, f"agent_{agent_id.lower().replace(' ', '_')}.jsonl")
            line = json.dumps(payload, ensure_ascii=False) + "\n"
            with open(global_log, "a", encoding="utf-8") as f:
                f.write(line)
            with open(agent_log, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.error(f"Gagal menulis log lokal event: {e}")

    def _process_queue(self):
        """Worker thread untuk mematuhi rate limit Discord."""
        while True:
            try:
                event = self._queue.get()
                self._dispatch_to_discord(event)
                time.sleep(0.5)  # Konservatif 2 pesan/detik
                self._queue.task_done()
            except Exception as e:
                logger.error(f"Error in discord reporter worker: {e}")
                time.sleep(1)

    def _dispatch_to_discord(self, event: Dict[str, Any]):
        creds = self._get_credentials()
        bot_token = creds.get("bot_token")
        webhook_url = creds.get("webhook_url")
        thread_id = event.get("thread_id")
        embed = event.get("embed")

        # Jika ada thread_id dan bot_token, kirim langsung ke thread Discord
        if thread_id and bot_token:
            url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
            headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json",
            }
            body = json.dumps({"embeds": [embed]}).encode("utf-8")
            self._post_http(url, headers, body)
        elif webhook_url:
            headers = {"Content-Type": "application/json"}
            body = json.dumps({"embeds": [embed]}).encode("utf-8")
            self._post_http(webhook_url, headers, body)

    def _post_http(self, url: str, headers: Dict[str, str], body: bytes, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 204):
                        return
            except urllib.error.HTTPError as e:
                # Hormati rate limit (429) & server error (5xx)
                if e.code == 429 or 500 <= e.code < 600:
                    reset_after = float(e.headers.get("X-RateLimit-Reset-After", 2.0))
                    time.sleep(min(reset_after, 5.0) * (attempt + 1))
                    continue
                else:
                    logger.debug(f"Discord API HTTP error {e.code}: {e.reason}")
                    break
            except Exception as e:
                time.sleep(1.0 * (attempt + 1))
                continue

# Singleton instance
_reporter_instance = None

def get_reporter() -> DiscordReporter:
    global _reporter_instance
    if _reporter_instance is None:
        _reporter_instance = DiscordReporter()
    return _reporter_instance
