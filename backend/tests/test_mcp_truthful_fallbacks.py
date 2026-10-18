import json

from mcp_server.server import MCPServer


def _call(server, name, arguments):
    response = server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    return json.loads(response["result"]["content"][0]["text"])


def test_job_status_fallback_is_unavailable(monkeypatch):
    monkeypatch.setattr("mcp_server.server._http_request", lambda *args, **kwargs: None)
    result = _call(MCPServer(), "get_job_status", {"job_id": "unknown-job"})
    assert result["status"] == "unavailable"
    assert result["runner_status"] == "unavailable"
    assert result["source"] == "unavailable"
    assert "current_round" not in result


def test_stop_fallback_does_not_claim_stop(monkeypatch):
    monkeypatch.setattr("mcp_server.server._http_request", lambda *args, **kwargs: None)
    result = _call(MCPServer(), "stop_simulation", {"simulation_id": "sim-unknown"})
    assert result["status"] == "unavailable"
    assert result["runner_status"] == "unavailable"
    assert result["source"] == "unavailable"


def test_report_fallback_remains_unavailable(monkeypatch):
    monkeypatch.setattr("mcp_server.server._http_request", lambda *args, **kwargs: None)
    result = _call(MCPServer(), "get_simulation_report", {"simulation_id": "sim-unknown"})
    assert result["status"] == "unavailable"
    assert result["source"] == "unavailable"
    assert "consensus_score" not in result
    assert "sentiment_score" not in result
