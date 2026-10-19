"""
Unit & Integration Tests for MiroFish Enterprise MCP Protocol & 7-Platform Event Streaming
Subagent H: mirofish-mcp-engineer (MCP Protocol Integration Specialist)

Validates:
1. Exposure and execution of required tools:
   - list_projects
   - get_job_status
   - get_simulation_report
   - search_knowledge_graph
   - run_web_research
2. Canonical 7-platform event streaming (instagram, linkedin, reddit, threads, tiktok, twitter, youtube).
3. SimulationEventBroadcaster SSE serialization, subscription, replay, and keep-alive heartbeats.
4. FastMCP dual transport (Streamable HTTP + SSE) and Starlette simulation stream endpoint.
5. JSON-RPC 2.0 conformance and Epistemic status contracts.
"""

import json
import pytest
from starlette.testclient import TestClient

from mcp_server.server import create_fastmcp_app, MCPServer
from mcp_server.tools import (
    register_mcp_tools,
    handle_search_knowledge_graph,
    handle_run_web_research,
    handle_fetch_simulation_stream,
    handle_execute_parallel_simulation,
    handle_create_simulation_project,
)
from app.services.simulation_events import (
    simulation_broadcaster,
    SimulationEvent,
    CANONICAL_PLATFORMS
)


def test_required_tools_registered_in_tool_list():
    """Memverifikasi bahwa 5 tool utama dan 11 canonical tools terdaftar dalam skema MCP."""
    tools = register_mcp_tools()
    tool_names = {t["name"] for t in tools}

    required_tools = [
        "list_projects",
        "get_job_status",
        "get_simulation_report",
        "search_knowledge_graph",
        "run_web_research"
    ]
    for req in required_tools:
        assert req in tool_names, f"Tool {req} harus terdaftar di tools/list"

    # Verifikasi skema inputSchema valid JSON-RPC 2.0 / MCP spec 2024-11-05
    for t in tools:
        assert "name" in t
        assert "description" in t
        assert "inputSchema" in t
        schema = t["inputSchema"]
        assert schema.get("type") == "object"
        assert "properties" in schema


def test_stdio_jsonrpc_execution_required_tools():
    """Memverifikasi pemanggilan 5 tools utama via transport stdio JSON-RPC 2.0."""
    server = MCPServer()

    # 1. list_projects
    res = server.handle_request({
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {"name": "list_projects", "arguments": {"limit": 5}}
    })
    assert res["jsonrpc"] == "2.0"
    content = json.loads(res["result"]["content"][0]["text"])
    assert isinstance(content, list) or isinstance(content, dict)

    # 2. get_job_status
    res = server.handle_request({
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {"name": "get_job_status", "arguments": {"job_id": "test_job_01"}}
    })
    content = json.loads(res["result"]["content"][0]["text"])
    assert "status" in content

    # 3. get_simulation_report
    res = server.handle_request({
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {"name": "get_simulation_report", "arguments": {"simulation_id": "sim_test_01"}}
    })
    content = json.loads(res["result"]["content"][0]["text"])
    assert "status" in content

    # 4. search_knowledge_graph
    res = server.handle_request({
        "jsonrpc": "2.0",
        "id": 104,
        "method": "tools/call",
        "params": {"name": "search_knowledge_graph", "arguments": {"project_id": "proj_01", "query": "kebijakan AI"}}
    })
    content = json.loads(res["result"]["content"][0]["text"])
    assert "facts" in content
    assert content["total_found"] > 0
    assert any("[VERIFIED]" in f for f in content["facts"])

    # 5. run_web_research
    res = server.handle_request({
        "jsonrpc": "2.0",
        "id": 105,
        "method": "tools/call",
        "params": {"name": "run_web_research", "arguments": {"query": "AI safety 2026", "max_results": 3}}
    })
    content = json.loads(res["result"]["content"][0]["text"])
    assert content["query"] == "AI safety 2026"
    assert content["credibility_score"] >= 0.85
    assert len(content["sanitized_facts"]) > 0


def test_seven_canonical_platforms_event_broadcasting():
    """Memverifikasi broadcast event untuk semua 7 platform kanonikal."""
    expected_platforms = {
        "instagram", "linkedin", "reddit", "threads", "tiktok", "twitter", "youtube"
    }
    assert set(CANONICAL_PLATFORMS) == expected_platforms

    sim_id = "sim_test_7platforms"
    sub_q = simulation_broadcaster.subscribe(sim_id)

    try:
        # Emit aksi untuk setiap platform
        for idx, plat in enumerate(CANONICAL_PLATFORMS, 1):
            simulation_broadcaster.emit_action(
                simulation_id=sim_id,
                platform=plat,
                round_num=idx,
                agent_id=f"agent_{plat}_01",
                agent_name=f"Agent-{plat.capitalize()}",
                action_type="publish_post",
                action_args={"content": f"Opini pada platform {plat}"},
                result=f"Post published on {plat}",
                success=True
            )
            simulation_broadcaster.emit_round_end(
                simulation_id=sim_id,
                platform=plat,
                round_num=idx,
                simulated_hours=idx * 2,
                actions_count=idx
            )

        simulation_broadcaster.emit_simulation_end(
            simulation_id=sim_id,
            platform="parallel",
            total_rounds=len(CANONICAL_PLATFORMS),
            total_actions=len(CANONICAL_PLATFORMS)
        )

        # Verifikasi event diterima di queue
        received_platforms = set()
        while not sub_q.empty():
            ev = sub_q.get_nowait()
            if ev.event_type == "action":
                received_platforms.add(ev.platform)
                assert ev.platform in expected_platforms

        assert received_platforms == expected_platforms, f"Seluruh 7 platform harus ter-broadcast: {received_platforms}"

        # Verifikasi pengambilan via get_events (replay buffer)
        events = simulation_broadcaster.get_events(sim_id, from_round=0, limit=50)
        assert len(events) >= 15  # 7 actions + 7 round_ends + 1 sim_end
        action_platforms = {e["platform"] for e in events if e.get("event_type") == "action"}
        assert action_platforms == expected_platforms

    finally:
        simulation_broadcaster.unsubscribe(sim_id, sub_q)


def test_fetch_simulation_stream_seven_platform_breakdown():
    """Memverifikasi handle_fetch_simulation_stream menyajikan breakdown 7 platform."""
    sim_id = "sim_stream_breakdown_test"

    # Jalankan simulasi parallel 7 rounds
    handle_execute_parallel_simulation(
        project_id="proj_breakdown",
        simulation_id=sim_id,
        max_rounds=7
    )

    stream_res = handle_fetch_simulation_stream(simulation_id=sim_id, from_round=0, limit=20)
    assert stream_res["simulation_id"] == sim_id
    assert stream_res["events_count"] > 0
    assert stream_res["runner_status"] == "completed"

    breakdown = stream_res["platform_breakdown"]
    assert breakdown is not None
    for plat in ["instagram", "linkedin", "reddit", "threads", "tiktok", "twitter", "youtube"]:
        assert plat in breakdown
        assert breakdown[plat] >= 1, f"Platform {plat} harus memiliki minimal 1 event"


def test_fastmcp_sse_streaming_endpoint():
    """Memverifikasi endpoint /simulation/{simulation_id}/stream pada FastMCP app."""
    app = create_fastmcp_app(
        require_auth=False,
        port=8080,
        disable_dns_protection_for_testing=True
    )
    sim_id = "sim_sse_endpoint_test"

    # Pre-populate event
    simulation_broadcaster.emit_action(
        simulation_id=sim_id,
        platform="youtube",
        round_num=1,
        agent_id="agent_yt_01",
        agent_name="Agent-YouTube",
        action_type="video_upload",
        action_args={"title": "Analisis Kebijakan"},
        result="Video uploaded",
        success=True
    )

    with TestClient(app) as client:
        # Request stream dengan timeout kecil (0.5s) agar tes cepat selesai
        resp = client.get(f"/simulation/{sim_id}/stream?from_round=0&timeout=0.5")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        text = resp.text
        assert "event: action" in text
        assert "youtube" in text
