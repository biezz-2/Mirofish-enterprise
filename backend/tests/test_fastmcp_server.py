"""
Unit & Integration Tests for Agent 17: Canonical FastMCP Server
Tests cover:
1. OAuth 2.1 RFC 7636 (PKCE S256) & RFC 7662 (Introspection) flows
2. FastMCP Streamable HTTP authentication gating (401 on missing/invalid token, 200 on valid)
3. Strict execution and Pydantic validation of all 11 Canonical Tools
4. BettaFish Downstream Analytics Tools (Agent 16)
5. ReAct Deduction Analyst tool dispatch integration
6. Legacy Stdio JSON-RPC 2.0 backward compatibility
7. Diagnostic health checks and port configuration
"""

import os
import json
import time
import pytest
import hashlib
from starlette.testclient import TestClient

# Ensure sys.path includes backend
import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from mcp_server.oauth import OAuth2Manager, base64url_encode
from mcp_server.server import create_fastmcp_app, MCPServer
from mcp_server.tools import (
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
    handle_bettafish_assess_corporate_risk,
)
from app.services.react_deduction_analyst import ReACTDeductionAnalyst, StrategicReport, ProvenanceChainSummary


@pytest.fixture
def test_client():
    """Test client with FastMCP and OAuth 2.1 routes."""
    app = create_fastmcp_app(
        require_auth=True,
        port=8080,
        disable_dns_protection_for_testing=True
    )
    with TestClient(app) as client:
        yield client


def test_oauth_metadata_rfc8414(test_client):
    """Verifikasi metadata server otorisasi OAuth 2.1 sesuai RFC 8414."""
    resp = test_client.get("/.well-known/oauth-authorization-server")
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_endpoint"].endswith("/oauth/token")
    assert data["authorization_endpoint"].endswith("/oauth/authorize")
    assert data["introspection_endpoint"].endswith("/oauth/introspect")
    assert "S256" in data["code_challenge_methods_supported"]
    assert "authorization_code" in data["grant_types_supported"]
    assert "client_credentials" in data["grant_types_supported"]


def test_oauth_pkce_authorization_code_flow(test_client):
    """Verifikasi alur Authorization Code dengan proteksi PKCE S256 (RFC 7636)."""
    # 1. Generate PKCE verifier and challenge
    code_verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    code_challenge = base64url_encode(hashlib.sha256(code_verifier.encode("ascii")).digest())

    # 2. Request Authorization Code
    auth_resp = test_client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": "hermes_agent",
            "redirect_uri": "http://127.0.0.1:8080/callback",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": "mcp:read mcp:write"
        },
        follow_redirects=False
    )
    assert auth_resp.status_code == 302
    redirect_loc = auth_resp.headers["location"]
    assert "code=" in redirect_loc
    import urllib.parse
    parsed_url = urllib.parse.urlparse(redirect_loc)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    auth_code = query_params["code"][0]

    # 3. Exchange code with wrong verifier -> harus ditolak (400)
    bad_token_resp = test_client.post(
        "/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://127.0.0.1:8080/callback",
            "client_id": "hermes_agent",
            "code_verifier": "invalid_verifier_should_fail"
        }
    )
    assert bad_token_resp.status_code == 400
    assert bad_token_resp.json()["error"] == "invalid_grant"

    # 4. Request second code for successful exchange (RFC single-use code semantics)
    auth_resp2 = test_client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": "hermes_agent",
            "redirect_uri": "http://127.0.0.1:8080/callback",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": "mcp:read mcp:write"
        },
        follow_redirects=False
    )
    parsed_url2 = urllib.parse.urlparse(auth_resp2.headers["location"])
    auth_code2 = urllib.parse.parse_qs(parsed_url2.query)["code"][0]

    # Exchange code with correct verifier -> sukses (200)
    good_token_resp = test_client.post(
        "/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": auth_code2,
            "redirect_uri": "http://127.0.0.1:8080/callback",
            "client_id": "hermes_agent",
            "code_verifier": code_verifier
        }
    )
    assert good_token_resp.status_code == 200
    token_data = good_token_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"
    assert token_data["expires_in"] == 3600

    # 5. Uji Token Introspection (RFC 7662)
    access_token = token_data["access_token"]
    intro_resp = test_client.post("/oauth/introspect", json={"token": access_token})
    assert intro_resp.status_code == 200
    intro_data = intro_resp.json()
    assert intro_data["active"] is True
    assert intro_data["client_id"] == "hermes_agent"
    assert "mcp:read" in intro_data["scope"]


def test_oauth_client_credentials_flow(test_client):
    """Verifikasi alur Client Credentials untuk client terdaftar."""
    # 1. Invalid client secret -> 401
    bad_resp = test_client.post(
        "/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": "hermes_agent",
            "client_secret": "wrong_secret"
        }
    )
    assert bad_resp.status_code == 401

    # 2. Valid client credentials -> 200
    good_resp = test_client.post(
        "/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": "hermes_agent",
            "client_secret": "hermes-mcp-secret-2026",
            "scope": "mcp:read mcp:write simulation:run"
        }
    )
    assert good_resp.status_code == 200
    data = good_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


def test_fastmcp_streamable_http_auth_enforcement(test_client):
    """Verifikasi proteksi otentikasi FastMCP pada endpoint /mcp."""
    # 1. Akses tanpa token -> 401
    resp_no_token = test_client.post("/mcp", json={})
    assert resp_no_token.status_code == 401
    assert "authentication required" in resp_no_token.text.lower() or "invalid_token" in resp_no_token.text.lower()

    # 2. Akses dengan token cacat/palsu -> 401
    resp_bad_token = test_client.post(
        "/mcp",
        headers={"Authorization": "Bearer fake.invalid.token"}
    )
    assert resp_bad_token.status_code == 401

    # 3. Akses dengan token valid dari OAuth server
    token_resp = test_client.post(
        "/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": "hermes_agent",
            "client_secret": "hermes-mcp-secret-2026",
            "scope": "mcp:read"
        }
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    # Kirim request dengan token sah (FastMCP streamable HTTP stream)
    resp_valid = test_client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {token}"}
    )
    # FastMCP streamable HTTP mengembalikan status non-401 saat bearer token terverifikasi
    assert resp_valid.status_code != 401


def test_diagnostics_and_health_endpoint(test_client):
    """Verifikasi endpoint diagnostik sistem /health."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["fastmcp_port"] == 8080
    assert data["active_tools_count"] == 11
    assert data["integrity_check"] == "PASSED"
    assert "oauth_2_1" in data


def test_canonical_11_tools_execution():
    """Uji eksekusi langsung 11 Canonical Tools dengan Pydantic schemas."""
    # 1. create_simulation_project
    res1 = handle_create_simulation_project(
        project_id="proj_test_01",
        name="Uji Simulasi FastMCP",
        description="Pengujian canonical tools",
        target_platforms=["twitter", "reddit"]
    )
    assert res1["project_id"] == "proj_test_01"
    assert res1["status"] == "initialized"

    # 2. trigger_web_research
    res2 = handle_trigger_web_research(query="regulasi AI 2026", max_results=3)
    assert res2["query"] == "regulasi AI 2026"
    assert res2["credibility_score"] >= 0.85
    assert len(res2["sanitized_facts"]) > 0

    # 3. build_knowledge_graph
    res3 = handle_build_knowledge_graph(
        project_id="proj_test_01",
        source_text="Regulasi AI Uni Eropa mewajibkan audit model fondasi dan kepatuhan transparansi data."
    )
    assert res3["project_id"] == "proj_test_01"
    assert res3["nodes_count"] >= 2
    assert res3["status"] == "indexed"
    assert len(res3["graph_digest_sha256"]) == 64

    # 4. generate_agent_profiles
    res4 = handle_generate_agent_profiles(project_id="proj_test_01", count=5, archetype="balanced")
    assert res4["agents_generated"] == 5
    assert len(res4["sample_profiles"]) > 0
    assert "mean_openness" in res4["ocean_summary"]

    # 5. calibrate_platform_algorithms
    res5 = handle_calibrate_platform_algorithms(platform="twitter", moral_emotional_weight=1.5, echo_damping=0.3)
    assert res5["platform"] == "twitter"
    assert res5["is_calibrated"] is True
    assert res5["calibration_weights"]["moral_emotional_weight"] == 1.5

    # 6. execute_parallel_simulation
    res6 = handle_execute_parallel_simulation(project_id="proj_test_01", simulation_id="sim_test_01", max_rounds=5)
    assert res6["rounds_completed"] == 5
    assert res6["runner_status"] == "completed"
    assert len(res6["checkpoint_hash_sha256"]) == 64

    # 7. fetch_simulation_stream
    res7 = handle_fetch_simulation_stream(simulation_id="sim_test_01", from_round=0, limit=10)
    assert res7["simulation_id"] == "sim_test_01"
    assert len(res7["events"]) > 0

    # 8. query_graph_insights
    res8 = handle_query_graph_insights(project_id="proj_test_01", query="Kebijakan AI")
    assert res8["total_found"] > 0
    assert res8["nli_confidence_avg"] >= 0.85

    # 9. generate_executive_report
    res9 = handle_generate_executive_report(topic="Stabilitas Swarm 2026", project_id="proj_test_01")
    assert "c_level_directives" in res9
    assert len(res9["sha256_digest"]) == 64
    assert len(res9["abstained_questions"]) > 0

    # 10. interview_simulation_agent
    res10 = handle_interview_simulation_agent(
        simulation_id="sim_test_01",
        agent_id="agent_test_001",
        question="Apa preferensi Anda terhadap kebijakan keamanan AI?"
    )
    assert res10["agent_id"] == "agent_test_001"
    assert "joy" in res10["emotional_state_ekman"]

    # 11. audit_system_diagnostics
    res11 = handle_audit_system_diagnostics(include_vault=True, include_backends=True)
    assert res11["status"] == "HEALTHY"
    assert res11["active_tools_count"] == 11


def test_bettafish_downstream_tools():
    """Uji perkakas analitik BettaFish downstream (Agent 16)."""
    # 1. Polar sentiment
    res_sent = handle_bettafish_analyze_polar_sentiment("Peluncuran sistem verifikasi berhasil optimal dan aman.")
    assert res_sent["polarity_score"] > 0.0
    assert res_sent["confidence"] > 0.80

    # 2. C-level report
    res_rep = handle_bettafish_generate_c_level_report(topic="Keandalan Swarm", claims=["Sistem stabil."])
    assert "executive_summary" in res_rep
    assert "c_level_directives" in res_rep
    assert len(res_rep["report_digest_sha256"]) == 64

    # 3. Corporate risk
    res_risk = handle_bettafish_assess_corporate_risk(polarity_score=-0.65, virality_potential=0.85)
    assert res_risk["risk_level"] == "CRITICAL"
    assert res_risk["early_warning_triggered"] is True


def test_react_deduction_analyst_dispatch_canonical_tool():
    """Verifikasi integrasi ReACT Analyst memanggil FastMCP Canonical Tools."""
    analyst = ReACTDeductionAnalyst()

    # Panggil tool melalui ReACT analyst
    res = analyst.dispatch_fastmcp_tool(
        tool_name="trigger_web_research",
        arguments={"query": "kedaulatan digital 2026", "max_results": 2}
    )
    assert "query" in res
    assert res["query"] == "kedaulatan digital 2026"
    assert res["credibility_score"] >= 0.85

    # Uji rekomendasi downstream handoff ke Agent 17
    mock_report = StrategicReport(
        report_id="rep_test_001",
        title="Laporan Uji",
        executive_summary="Ringkasan Uji",
        key_findings=["Temuan 1"],
        citations=[],
        abstained_questions=[],
        deduction_steps=[],
        hypotheses_deductions=[],
        markdown_content="Content",
        provenance_summary={
            "chain_status": "SHA-256_CHAIN_VERIFIED",
            "root_hash": "abcd",
            "total_citations": 1
        },
        downstream_parameters={}
    )
    handoff_17 = analyst.get_downstream_recommendations_agent_17(mock_report)
    assert handoff_17["target_subagent"] == "Agent 17: Canonical FastMCP Server Architect"
    assert handoff_17["fastmcp_tools_available"] == 11
    assert handoff_17["default_port"] == 8080


def test_legacy_stdio_backward_compatibility():
    """Uji kompatibilitas penuh MCPServer stdio JSON-RPC 2.0 untuk orkestrator legacy."""
    server = MCPServer()

    # 1. tools/list harus memuat 11 canonical tools + legacy tools
    list_res = server.handle_request({"jsonrpc": "2.0", "id": 10, "method": "tools/list"})
    tools = list_res["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    assert "create_simulation_project" in tool_names
    assert "trigger_web_research" in tool_names
    assert "generate_executive_report" in tool_names
    assert "list_projects" in tool_names
    assert "start_simulation" in tool_names

    # 2. tools/call canonical tool via stdio
    call_res = server.handle_request({
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "generate_agent_profiles",
            "arguments": {"project_id": "proj_stdio_01", "count": 3}
        }
    })
    content = call_res["result"]["content"]
    assert len(content) > 0
    parsed = json.loads(content[0]["text"])
    assert parsed["agents_generated"] == 3
    assert parsed["project_id"] == "proj_stdio_01"
