"""
MiroFish Enterprise 9Router Standalone Daemon (Agent 20: DevOps & Failover Guard)
Exposes HTTP health/proxy interface on port 8787 for PM2 cluster management.
"""

import os
import sys
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.services.nine_router import get_nine_router

PORT = int(os.environ.get("ROUTER_PORT", os.environ.get("PORT", 8787)))
HOST = os.environ.get("ROUTER_HOST", "0.0.0.0")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [9ROUTER-DAEMON] %(message)s")


class NineRouterHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for 9Router daemon."""

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_GET(self):
        router = get_nine_router()
        if self.path in ("/health", "/status", "/v1/health"):
            telemetry = router.get_telemetry()
            self._send_json(200, {
                "status": "HEALTHY",
                "service": "9Router AI Failover Gateway",
                "telemetry": telemetry
            })
        elif self.path == "/v1/metrics":
            self._send_json(200, router.get_telemetry())
        else:
            self._send_json(404, {"error": "Not Found", "available_paths": ["/health", "/status", "/v1/metrics"]})

    def do_POST(self):
        router = get_nine_router()
        if self.path in ("/v1/reset-circuit", "/reset-circuit"):
            result = router.reset_circuit_breakers()
            self._send_json(200, result)
        elif self.path in ("/v1/chat/completions", "/chat/completions"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                messages = data.get("messages", [])
                model = data.get("model")
                temperature = float(data.get("temperature", 0.7))
                max_tokens = int(data.get("max_tokens", 2048))
                resp = router.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                self._send_json(200, resp)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self._send_json(404, {"error": "Endpoint not recognized"})

    def log_message(self, format, *args):
        # Suppress noisy standard request log to stderr
        pass


def run_daemon():
    server = HTTPServer((HOST, PORT), NineRouterHandler)
    logging.info(f"9Router Daemon active and listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("9Router Daemon stopping gracefully.")
        server.server_close()


if __name__ == "__main__":
    run_daemon()
