"""
MiroFish Enterprise - FastMCP Server (Agent 17: Canonical FastMCP Server Architect)
Exposes FastMCP Streamable HTTP / SSE transport on port 8080 (configurable)
with OAuth 2.1 Authentication (RFC 7636 PKCE S256 & RFC 7662 Introspection),
Strictly-Typed Pydantic Schemas for 11 Canonical Tools + BettaFish Downstream Analytics,
and backward-compatible stdio transport for legacy orchestration.
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Optional, Dict, List

# FastMCP native imports
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

# Local module imports
from mcp_server.oauth import (
    OAuth2Manager,
    oauth_token_endpoint,
    oauth_authorize_endpoint,
    oauth_introspect_endpoint,
    oauth_metadata_endpoint
)
from mcp_server.tools import (
    register_canonical_tools,
    register_mcp_tools,
    handle_create_simulation_project,
    handle_trigger_web_research,
    handle_build_knowledge_graph,
    handle_generate_agent_profiles,
    handle_calibrate_platform_algorithms,
    handle_execute_parallel_simulation,
    handle_fetch_simulation_stream,
    handle_query_graph_insights,
    handle_generate_executive_report,
    handle_interview_simulation_agent,
    handle_audit_system_diagnostics,
    handle_bettafish_analyze_polar_sentiment,
    handle_bettafish_generate_c_level_report,
    handle_bettafish_assess_corporate_risk
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mirofish.fastmcp_server")

DEFAULT_PORT = int(os.environ.get("MCP_SERVER_PORT", os.environ.get("PORT", "8080")))
DEFAULT_HOST = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000").rstrip("/")


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


def create_fastmcp_server(
    require_auth: bool = True,
    port: Optional[int] = None,
    host: Optional[str] = None
) -> tuple[FastMCP, OAuth2Manager]:
    """
    Inisialisasi server FastMCP dengan OAuth 2.1 Provider dan pendaftaran 11 Canonical Tools.
    """
    p = port or DEFAULT_PORT
    h = host or DEFAULT_HOST
    server_url = f"http://localhost:{p}"

    oauth_mgr = OAuth2Manager(server_url=server_url)

    if require_auth:
        auth_settings = AuthSettings(
            issuer_url=AnyHttpUrl(server_url),
            resource_server_url=AnyHttpUrl(server_url),
            validate_token_resource=False
        )
        token_verifier = oauth_mgr.get_token_verifier()
        fastmcp = FastMCP(
            name="MiroFish-Enterprise-Canonical-FastMCP",
            auth=auth_settings,
            token_verifier=token_verifier
        )
    else:
        fastmcp = FastMCP(name="MiroFish-Enterprise-Canonical-FastMCP")

    # Registrasi 11 Canonical Tools + BettaFish Downstream
    register_canonical_tools(fastmcp)
    return fastmcp, oauth_mgr


def create_fastmcp_app(
    require_auth: bool = True,
    port: Optional[int] = None,
    host: Optional[str] = None,
    disable_dns_protection_for_testing: bool = False
) -> Starlette:
    """
    Membuat Starlette ASGI Application lengkap dengan FastMCP Streamable HTTP mount
    dan rute OAuth 2.1 RFC 7636 / RFC 7662.
    """
    p = port or DEFAULT_PORT
    h = host or DEFAULT_HOST
    fastmcp, oauth_mgr = create_fastmcp_server(require_auth=require_auth, port=p, host=h)

    # Konfigurasi security settings untuk FastMCP app
    transport_sec = None
    if disable_dns_protection_for_testing:
        transport_sec = TransportSecuritySettings(enable_dns_rebinding_protection=False)

    # FastMCP Streamable HTTP app
    app = fastmcp.streamable_http_app(transport_security=transport_sec)

    async def health_endpoint(request: Request) -> JSONResponse:
        diag = handle_audit_system_diagnostics(include_vault=True, include_backends=True)
        diag["status"] = "healthy"
        diag["service"] = "mirofish-mcp-server"
        diag["transport"] = "streamable-http"
        diag["fastmcp_port"] = p
        diag["oauth_required"] = require_auth
        return JSONResponse(diag)

    async def list_tools_endpoint(request: Request) -> JSONResponse:
        tools = register_mcp_tools()
        return JSONResponse({
            "tools": tools,
            "total_canonical": 11,
            "total_registered": len(tools)
        })

    async def oauth_metadata_wrapper(request: Request) -> Response:
        return await oauth_metadata_endpoint(request, oauth_mgr)

    async def oauth_authorize_wrapper(request: Request) -> Response:
        return await oauth_authorize_endpoint(request, oauth_mgr)

    async def oauth_token_wrapper(request: Request) -> Response:
        return await oauth_token_endpoint(request, oauth_mgr)

    async def oauth_introspect_wrapper(request: Request) -> Response:
        return await oauth_introspect_endpoint(request, oauth_mgr)

    # Rute Health & Tools Metadata
    app.add_route("/health", health_endpoint, methods=["GET"])
    app.add_route("/tools", list_tools_endpoint, methods=["GET"])

    # Rute OAuth 2.1 RFC-compliant
    app.add_route("/.well-known/oauth-authorization-server", oauth_metadata_wrapper, methods=["GET"])
    app.add_route("/oauth/authorize", oauth_authorize_wrapper, methods=["GET", "POST"])
    app.add_route("/oauth/token", oauth_token_wrapper, methods=["POST"])
    app.add_route("/oauth/introspect", oauth_introspect_wrapper, methods=["POST"])

    # Simpan referensi objek untuk pengujian
    app.state.fastmcp = fastmcp
    app.state.oauth_mgr = oauth_mgr
    return app


# ---------------------------------------------------------------------------
# Legacy Stdio / Backward-Compatible MCPServer Implementation
# ---------------------------------------------------------------------------

class MCPServer:
    """
    Server MCP Kompatibel Stdio & JSON-RPC 2.0 untuk orkestrasi internal MiroFish.
    Mendukung 11 Canonical Tools baru secara langsung dan backward-compatible.
    """
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
        # Canonical 11 Tools Handlers
        if name == "create_simulation_project":
            res = handle_create_simulation_project(
                project_id=args.get("project_id", "proj_default"),
                name=args.get("name", "Simulation Project"),
                description=args.get("description", ""),
                target_platforms=args.get("target_platforms")
            )
        elif name == "trigger_web_research":
            res = handle_trigger_web_research(
                query=args.get("query", ""),
                project_id=args.get("project_id", "proj_default"),
                max_results=args.get("max_results", 10),
                search_type=args.get("search_type", "general")
            )
        elif name == "build_knowledge_graph":
            res = handle_build_knowledge_graph(
                project_id=args.get("project_id", "proj_default"),
                source_text=args.get("source_text", ""),
                group_id=args.get("group_id"),
                extract_relations=args.get("extract_relations", True)
            )
        elif name == "generate_agent_profiles":
            res = handle_generate_agent_profiles(
                project_id=args.get("project_id", "proj_default"),
                count=args.get("count", 10),
                archetype=args.get("archetype", "balanced"),
                target_platforms=args.get("target_platforms")
            )
        elif name == "calibrate_platform_algorithms":
            res = handle_calibrate_platform_algorithms(
                platform=args.get("platform", "parallel"),
                moral_emotional_weight=args.get("moral_emotional_weight"),
                outgroup_penalty=args.get("outgroup_penalty"),
                echo_damping=args.get("echo_damping")
            )
        elif name == "execute_parallel_simulation":
            res = handle_execute_parallel_simulation(
                project_id=args.get("project_id", "proj_default"),
                simulation_id=args.get("simulation_id", "sim_default"),
                max_rounds=args.get("max_rounds", 10),
                platform=args.get("platform", "parallel"),
                run_bsp_barrier=args.get("run_bsp_barrier", True)
            )
        elif name == "fetch_simulation_stream":
            res = handle_fetch_simulation_stream(
                simulation_id=args.get("simulation_id", "sim_default"),
                from_round=args.get("from_round", 0),
                limit=args.get("limit", 50)
            )
        elif name == "query_graph_insights":
            res = handle_query_graph_insights(
                project_id=args.get("project_id", "proj_default"),
                query=args.get("query", ""),
                limit=args.get("limit", 10),
                as_of=args.get("as_of")
            )
        elif name == "generate_executive_report":
            res = handle_generate_executive_report(
                topic=args.get("topic", "Executive Report"),
                project_id=args.get("project_id"),
                simulation_id=args.get("simulation_id"),
                verified_only=args.get("verified_only", True)
            )
        elif name == "interview_simulation_agent":
            res = handle_interview_simulation_agent(
                simulation_id=args.get("simulation_id", "sim_default"),
                agent_id=args.get("agent_id", "agent_001"),
                question=args.get("question", ""),
                max_tokens=args.get("max_tokens", 256)
            )
        elif name == "audit_system_diagnostics":
            res = handle_audit_system_diagnostics(
                include_vault=args.get("include_vault", True),
                include_backends=args.get("include_backends", True)
            )

        # BettaFish Downstream Tools
        elif name == "bettafish_analyze_polar_sentiment":
            res = handle_bettafish_analyze_polar_sentiment(args.get("text", ""))
        elif name == "bettafish_generate_c_level_report":
            res = handle_bettafish_generate_c_level_report(args.get("topic", ""), args.get("claims"))
        elif name == "bettafish_assess_corporate_risk":
            res = handle_bettafish_assess_corporate_risk(
                args.get("polarity_score", 0.0),
                args.get("virality_potential", 0.0)
            )

        # Legacy Tools Handlers
        elif name == "list_projects":
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
                    "runner_status": "unavailable",
                    "status": "unavailable",
                    "error": "backend_error",
                    "source": "unavailable"
                }

        elif name == "get_simulation_report":
            sim_id = args.get("simulation_id")
            proj_id = args.get("project_id")
            backend_res = None
            if sim_id:
                backend_res = _http_request("GET", f"/api/report/by-simulation/{sim_id}")
            elif proj_id:
                backend_res = _http_request("GET", f"/api/report/list?limit=1")

            if backend_res and backend_res.get("success"):
                res = backend_res.get("data", {})
            else:
                res = {
                    "project_id": proj_id,
                    "simulation_id": sim_id,
                    "status": "unavailable",
                    "error": "backend_error",
                    "source": "unavailable"
                }
        elif name == "search_knowledge_graph":
            proj_id = args.get("project_id", "")
            query = args.get("query", "")
            res = handle_query_graph_insights(proj_id, query)

        elif name == "run_web_research":
            query = args.get("query", "")
            res = handle_trigger_web_research(query, max_results=args.get("max_results", 10), search_type=args.get("research_type", "general"))

        elif name == "create_simulation_job":
            proj_id = args.get("project_id", "proj-default")
            raw_platforms = args.get("platforms")
            from app.services.simulation_manager import normalize_platforms
            resolved_platforms = normalize_platforms(
                raw_platforms,
                enable_twitter=args.get("enable_twitter", True),
                enable_reddit=args.get("enable_reddit", True),
            )
            res = handle_create_simulation_project(project_id=proj_id, name=f"Sim-{proj_id}", target_platforms=resolved_platforms)

        elif name == "start_simulation":
            sim_id = args.get("simulation_id", "sim-default")
            res = handle_execute_parallel_simulation(project_id="proj_default", simulation_id=sim_id, max_rounds=args.get("max_rounds", 50), platform=args.get("platform", "parallel"))

        elif name == "stop_simulation":
            sim_id = args.get("simulation_id", "sim-default")
            res = {
                "simulation_id": sim_id,
                "runner_status": "unavailable",
                "status": "unavailable",
                "error": "backend_error",
                "source": "unavailable"
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
        logger.info("Server FastMCP MiroFish berjalan pada mode stdio...")
        for line in sys.stdin:
            line = line.strip().lstrip("\ufeff")
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
