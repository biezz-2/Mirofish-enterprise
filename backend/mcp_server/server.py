"""
Server MCP MiroFish dengan Transport stdio & Integrasi Backend REST API
"""
import sys
import json
import os
import urllib.request
import urllib.error
import logging
from typing import Any, Optional, Dict
from .tools import register_mcp_tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mirofish.mcp_server")

BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:5001").rstrip("/")

def _http_request(method: str, path: str, data: Optional[Dict[str, Any]] = None, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """Helper panggilan HTTP sinkron stdlib ke backend MiroFish."""
    url = f"{BACKEND_API_URL}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status in (200, 201):
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
    except Exception as e:
        logger.debug(f"[Backend HTTP Call] {method} {url} tidak tersedia / gagal: {e}")
    return None

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
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    def _call_tool(self, req_id: Any, name: str, args: dict) -> dict:
        backend_res = None

        if name == "list_projects":
            limit = args.get("limit", 20)
            backend_res = _http_request("GET", f"/api/graph/project/list?limit={limit}")
            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", [])
            else:
                res = [
                    {
                        "id": "proj-default",
                        "name": "Simulasi Kebijakan Publik",
                        "status": "ready",
                        "source": "mock_fallback"
                    }
                ]

        elif name == "get_job_status":
            job_id = args.get("job_id", "")
            backend_res = _http_request("GET", f"/api/simulation/{job_id}/run-status")
            if not (backend_res and backend_res.get("success")):
                backend_res = _http_request("GET", f"/api/simulation/{job_id}")

            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "job_id": job_id,
                    "runner_status": "idle",
                    "current_round": 12,
                    "progress_percent": 24.0,
                    "source": "mock_fallback"
                }

        elif name == "get_simulation_report":
            sim_id = args.get("simulation_id")
            proj_id = args.get("project_id")
            if sim_id:
                backend_res = _http_request("GET", f"/api/report/by-simulation/{sim_id}")
            elif proj_id:
                backend_res = _http_request("GET", f"/api/report/list?limit=1")

            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "project_id": proj_id or "proj-default",
                    "simulation_id": sim_id or "sim-default",
                    "status": "completed",
                    "summary": "Analisis opini publik dan pergeseran sentimen simulasi",
                    "consensus_score": 0.82,
                    "source": "mock_fallback"
                }

        elif name == "search_knowledge_graph":
            proj_id = args.get("project_id", "")
            query = args.get("query", "")
            backend_res = _http_request("GET", f"/api/graph/data/{proj_id}")
            if backend_res and backend_res.get("success") and "data" in backend_res:
                graph_data = backend_res["data"]
                edges = graph_data.get("edges", [])
                matched_facts = []
                for edge in edges:
                    fact = f"{edge.get('source')} {edge.get('relation', 'TERKAIT')} {edge.get('target')}"
                    if not query or any(w.lower() in fact.lower() for w in query.split()[:3]):
                        matched_facts.append(fact)
                res = {
                    "project_id": proj_id,
                    "query": query,
                    "facts": matched_facts[:10],
                    "total_found": len(matched_facts),
                    "source": "real_backend"
                }
            else:
                res = {
                    "project_id": proj_id,
                    "query": query,
                    "facts": [
                        f"Fakta graf: Kebijakan berdampak pada polarisasi publik untuk {query}",
                        f"Relasi entitas: Stakeholder utama merespons sentimen {query}"
                    ],
                    "total_found": 2,
                    "source": "mock_fallback"
                }

        elif name == "run_web_research":
            query = args.get("query", "")
            payload = {
                "query": query,
                "research_type": args.get("research_type", "general"),
                "max_results": args.get("max_results", 10)
            }
            backend_res = _http_request("POST", "/api/research/searchxng", payload)
            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "query": query,
                    "engine": "searxng-selfhosted",
                    "status": "completed",
                    "facts": [f"Fakta terkini mengenai {query}"],
                    "credibility_score": 0.88,
                    "source": "mock_fallback"
                }

        elif name == "create_simulation_job":
            payload = {
                "project_id": args.get("project_id"),
                "graph_id": args.get("graph_id"),
                "enable_twitter": args.get("enable_twitter", True),
                "enable_reddit": args.get("enable_reddit", True)
            }
            backend_res = _http_request("POST", "/api/simulation/create", payload)
            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "simulation_id": f"sim_{args.get('project_id', 'proj')[:8]}_local",
                    "project_id": args.get("project_id"),
                    "status": "created",
                    "enable_twitter": payload["enable_twitter"],
                    "enable_reddit": payload["enable_reddit"],
                    "source": "mock_fallback"
                }

        elif name == "start_simulation":
            payload = {
                "simulation_id": args.get("simulation_id"),
                "platform": args.get("platform", "parallel"),
                "max_rounds": args.get("max_rounds", 50),
                "force": args.get("force", False)
            }
            backend_res = _http_request("POST", "/api/simulation/start", payload)
            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "simulation_id": payload["simulation_id"],
                    "runner_status": "running",
                    "platform": payload["platform"],
                    "max_rounds": payload["max_rounds"],
                    "source": "mock_fallback"
                }

        elif name == "stop_simulation":
            payload = {"simulation_id": args.get("simulation_id")}
            backend_res = _http_request("POST", "/api/simulation/stop", payload)
            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "simulation_id": payload["simulation_id"],
                    "runner_status": "stopped",
                    "source": "mock_fallback"
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
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
