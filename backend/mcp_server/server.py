"""
Server MCP MiroFish dengan Transport stdio & Streamable HTTP
"""
import sys
import json
import logging
from typing import Any
from .tools import register_mcp_tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mirofish.mcp_server")

class MCPServer:
    def __init__(self):
        self.tools = register_mcp_tools()

    def handle_request(self, request_data: dict) -> dict:
        method = request_data.get("method")
        req_id = request_data.get("id")

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.tools}
            }
        elif method == "tools/call":
            params = request_data.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            return self._call_tool(req_id, name, args)
        elif method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "mirofish-mcp", "version": "3.1.0"},
                    "capabilities": {"tools": {}}
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    def _call_tool(self, req_id: Any, name: str, args: dict) -> dict:
        if name == "list_projects":
            res = [{"id": "proj-default", "name": "Simulasi Kebijakan Publik", "status": "ready"}]
        elif name == "get_job_status":
            job_id = args.get("job_id", "")
            res = {"job_id": job_id, "state": "running", "current_round": 12, "progress_pct": 24.0}
        elif name == "run_web_research":
            query = args.get("query", "")
            res = {
                "query": query,
                "engine": "searxng-selfhosted",
                "status": "completed",
                "facts": [f"Fakta terkini mengenai {query}"],
                "credibility_score": 0.85
            }
        else:
            res = {"status": "ok", "tool": name, "echo_args": args}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]
            }
        }

    def run_stdio(self):
        logger.info("Server MCP MiroFish berjalan pada mode stdio...")
        for line in sys.stdin:
            line = line.strip().lstrip("﻿")
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
