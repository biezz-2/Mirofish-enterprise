"""
Unit & Integration Test Suite for Agent 18:
Enterprise OpenAPI 3.1.0, JSON Schema 2020-12 Dialect, and
Distributed Webhook Delivery Engine with HMAC-SHA256, Anti-Replay, Jittered Backoff,
and Dead-Letter Queue (DLQ) Re-Drive.
"""

import os
import sys
import time
import json
import pytest
from datetime import datetime, timezone
from jsonschema import Draft202012Validator

# Ensure sys.path includes backend and root
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from app import create_app
from app.services.webhook_service import (
    WebhookDispatcher,
    WebhookEvent,
    WebhookSubscription,
    WebhookDispatchResult,
    webhook_dispatcher,
)
from app.services.openapi_engine import (
    OPENAPI_310_SPEC,
    get_openapi_spec,
    validate_json_schema_2020_12,
    SIMULATION_PROJECT_SCHEMA,
    WEBHOOK_SUBSCRIPTION_SCHEMA,
)


@pytest.fixture(scope="module")
def app():
    """Create Flask application test client."""
    flask_app = create_app()
    flask_app.testing = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Test Category 1: OpenAPI 3.1.0 Specification & Dialect Verification
# ---------------------------------------------------------------------------

def test_openapi_310_version_and_dialect():
    """OpenAPI version must be 3.1.0 and jsonSchemaDialect must be draft 2020-12."""
    spec = get_openapi_spec("dict")
    assert spec["openapi"] == "3.1.0"
    assert spec["jsonSchemaDialect"] == "https://json-schema.org/draft/2020-12/schema"
    assert "info" in spec
    assert spec["info"]["version"] == "3.2.0"
    assert "webhooks" in spec
    assert isinstance(spec["webhooks"], dict)


def test_openapi_top_level_webhooks_catalog():
    """Top-level webhooks object must declare required enterprise events."""
    spec = get_openapi_spec("dict")
    webhooks = spec.get("webhooks", {})
    expected_webhooks = [
        "bettafish_executive_report_generated",
        "bettafish_critical_risk_alert",
        "mcp_tool_invoked",
        "mcp_simulation_state_changed",
        "simulation_round_completed",
        "simulation_completed",
        "system_alert",
    ]
    for wh in expected_webhooks:
        assert wh in webhooks, f"Webhook '{wh}' must be declared in OpenAPI 3.1.0 top-level webhooks object"
        assert "post" in webhooks[wh], f"Webhook '{wh}' must declare POST operation"
        assert "requestBody" in webhooks[wh]["post"]


def test_openapi_components_schema_valid_draft202012():
    """All schemas under components.schemas must validate against JSON Schema 2020-12."""
    spec = get_openapi_spec("dict")
    schemas = spec.get("components", {}).get("schemas", {})
    assert len(schemas) > 0

    for name, schema in schemas.items():
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"Schema {name} missing draft 2020-12 dialect"
        Draft202012Validator.check_schema(schema)


def test_openapi_documentation_endpoints(client):
    """OpenAPI JSON, YAML, and Swagger UI routes must return HTTP 200."""
    # JSON endpoint
    res_json = client.get("/openapi.json")
    assert res_json.status_code == 200
    assert res_json.json["openapi"] == "3.1.0"

    # Blueprint JSON endpoint
    res_bp_json = client.get("/api/enterprise/openapi.json")
    assert res_bp_json.status_code == 200
    assert res_bp_json.json["openapi"] == "3.1.0"

    # YAML endpoint
    res_yaml = client.get("/openapi.yaml")
    assert res_yaml.status_code == 200
    assert "openapi: 3.1.0" in res_yaml.data.decode("utf-8")

    # Swagger UI documentation HTML
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200
    assert "SwaggerUIBundle" in res_docs.data.decode("utf-8")


def test_json_schema_2020_12_validation_utility():
    """validate_json_schema_2020_12 must accurately detect valid and invalid schemas."""
    valid_data = {
        "title": "Analisis Pasar Kripto Indonesia",
        "target_audience": "Fintech Regulators",
        "initial_agents_count": 50,
        "platforms": ["twitter_x", "tiktok"]
    }
    is_valid, errors = validate_json_schema_2020_12(valid_data, SIMULATION_PROJECT_SCHEMA)
    assert is_valid is True
    assert errors is None or len(errors) == 0

    invalid_data = {
        "title": "AB",  # minLength is 3
        "initial_agents_count": 0  # minimum is 1
    }
    is_valid_bad, errors_bad = validate_json_schema_2020_12(invalid_data, SIMULATION_PROJECT_SCHEMA)
    assert is_valid_bad is False
    assert errors_bad is not None and len(errors_bad) >= 1


# ---------------------------------------------------------------------------
# Test Category 2: Webhook HMAC-SHA256 & Anti-Replay Verification
# ---------------------------------------------------------------------------

def test_webhook_hmac_signature_generation_and_verification():
    """HMAC-SHA256 signature generation and strict match."""
    payload = json.dumps({"event": "TEST_EVENT", "value": 123}, sort_keys=True)
    secret = "test_super_secret_key"
    ts = int(time.time())

    sig = WebhookDispatcher.generate_hmac_signature(payload, secret, timestamp=ts)
    assert sig.startswith("sha256=")

    # Valid match
    is_valid, err = WebhookDispatcher.verify_hmac_signature(payload, secret, sig, timestamp=ts)
    assert is_valid is True
    assert err is None

    # Tampered payload
    tampered_payload = json.dumps({"event": "TEST_EVENT", "value": 999}, sort_keys=True)
    is_valid_tampered, err_tampered = WebhookDispatcher.verify_hmac_signature(tampered_payload, secret, sig, timestamp=ts)
    assert is_valid_tampered is False
    assert "mismatch" in err_tampered.lower()

    # Wrong secret
    is_valid_bad_secret, _ = WebhookDispatcher.verify_hmac_signature(payload, "wrong_secret", sig, timestamp=ts)
    assert is_valid_bad_secret is False


def test_webhook_anti_replay_timestamp_protection():
    """Signatures with expired or skewed timestamps must be rejected."""
    payload = json.dumps({"alert": "CRITICAL_DRIFT"}, sort_keys=True)
    secret = "anti_replay_secret"
    tolerance = 300  # 5 minutes

    # Stale timestamp: 400 seconds in the past
    stale_ts = int(time.time()) - 400
    stale_sig = WebhookDispatcher.generate_hmac_signature(payload, secret, timestamp=stale_ts)
    is_valid_stale, err_stale = WebhookDispatcher.verify_hmac_signature(
        payload, secret, stale_sig, timestamp=stale_ts, tolerance_seconds=tolerance
    )
    assert is_valid_stale is False
    assert err_stale is not None and any(term in err_stale.lower() for term in ["expired", "tolerance", "stale", "replay"])

    # Future skewed timestamp: 400 seconds in the future
    future_ts = int(time.time()) + 400
    future_sig = WebhookDispatcher.generate_hmac_signature(payload, secret, timestamp=future_ts)
    is_valid_future, err_future = WebhookDispatcher.verify_hmac_signature(
        payload, secret, future_sig, timestamp=future_ts, tolerance_seconds=tolerance
    )
    assert is_valid_future is False
    assert err_future is not None and any(term in err_future.lower() for term in ["expired", "tolerance", "future", "clock", "skew"])


def test_webhook_verify_endpoint_api(client):
    """Test POST /api/enterprise/webhooks/verify API endpoint."""
    secret = "api_secret_key"
    payload = {"status": "ACTIVE", "agents": 12}
    payload_str = json.dumps(payload, sort_keys=True)
    ts = int(time.time())
    sig = WebhookDispatcher.generate_hmac_signature(payload_str, secret, timestamp=ts)

    res = client.post("/api/enterprise/webhooks/verify", json={
        "payload": payload,
        "secret_key": secret,
        "signature": sig,
        "timestamp": ts,
        "tolerance_seconds": 300
    })
    assert res.status_code == 200
    assert res.json["is_valid"] is True


# ---------------------------------------------------------------------------
# Test Category 3: Exponential Backoff, Jitter & P95 Latency Target
# ---------------------------------------------------------------------------

def test_exponential_backoff_jitter_bounds():
    """Verify exponential backoff calculation remains strictly within jitter boundaries."""
    dispatcher = WebhookDispatcher(initial_backoff_s=0.01, max_backoff_s=0.5, backoff_multiplier=2.0)
    for attempt in range(1, 5):
        delay = dispatcher.compute_backoff_delay(attempt)
        max_possible = min(dispatcher.max_backoff_s, dispatcher.initial_backoff_s * (dispatcher.backoff_multiplier ** (attempt - 1)))
        assert 0.0 <= delay <= max_possible, f"Delay {delay} out of bounds for attempt {attempt}"


def test_webhook_p95_latency_benchmark():
    """Benchmark webhook delivery in fast test mode: P95 latency must be strictly < 250ms."""
    dispatcher = WebhookDispatcher(initial_backoff_s=0.001, max_backoff_s=0.01)
    dispatcher.enable_in_memory_test_mode(simulated_latency_ms=10.0, simulated_failure_rate=0.0)

    durations = []
    for i in range(50):
        event = WebhookEvent(
            event_type="BENCHMARK_EVENT",
            payload={"iteration": i, "timestamp": time.time()}
        )
        res = dispatcher.dispatch("http://test.internal/webhook", event)
        assert res.is_success is True
        durations.append(res.duration_ms)

    durations.sort()
    p95_idx = int(0.95 * len(durations))
    p95_latency = durations[p95_idx]

    # Target P95 latency < 250ms
    assert p95_latency < 250.0, f"P95 latency {p95_latency}ms exceeds 250ms target"

    stats = dispatcher.get_stats()
    assert stats["total_dispatched"] >= 50
    assert stats["p95_latency_ms"] < 250.0


# ---------------------------------------------------------------------------
# Test Category 4: Dead-Letter Queue (DLQ) & Re-Drive Mechanism
# ---------------------------------------------------------------------------

def test_webhook_dlq_capture_and_redrive():
    """Failed deliveries must be queued into DLQ and re-driven upon resolution."""
    dispatcher = WebhookDispatcher(max_retries=2, initial_backoff_s=0.001, max_backoff_s=0.005)
    # Configure simulated 100% failure mode
    dispatcher.enable_in_memory_test_mode(simulated_latency_ms=5.0, simulated_failure_rate=1.0)

    event = WebhookEvent(
        event_type="FAILING_EVENT",
        payload={"task": "critical_sync"},
        target_url="http://failing.service/webhook"
    )

    res = dispatcher.dispatch("http://failing.service/webhook", event)
    assert res.is_success is False
    assert res.attempts == 3  # 1 initial + 2 retries

    # Check DLQ status
    dlq_items = dispatcher.get_dlq()
    assert len(dlq_items) >= 1
    failed_item = next(item for item in dlq_items if item["event"]["event_id"] == event.event_id)
    assert failed_item["status"] == "DLQ"
    assert failed_item["attempts"] == 3

    # Now simulate recovery of downstream endpoint (0% failure)
    dispatcher.enable_in_memory_test_mode(simulated_latency_ms=5.0, simulated_failure_rate=0.0)

    # Re-drive single event
    redrive_res = dispatcher.replay_dlq_event(event.event_id)
    assert redrive_res.is_success is True

    # Confirm event is no longer in DLQ
    remaining_dlq = dispatcher.get_dlq()
    matching = [item for item in remaining_dlq if item["event"]["event_id"] == event.event_id]
    assert len(matching) == 0


def test_dlq_api_endpoints(client):
    """Test /api/enterprise/webhooks/dlq endpoints for inspection, replay, and purge."""
    # Ensure some item is in DLQ
    webhook_dispatcher.enable_in_memory_test_mode(simulated_latency_ms=2.0, simulated_failure_rate=1.0)
    evt = WebhookEvent(event_type="DLQ_API_TEST", payload={"id": "dlq_test_1"})
    webhook_dispatcher.dispatch("http://failing.api/webhook", evt)

    # 1. GET /api/enterprise/webhooks/dlq
    res_get = client.get("/api/enterprise/webhooks/dlq")
    assert res_get.status_code == 200
    assert res_get.json["success"] is True
    assert res_get.json["count"] >= 1

    # 2. POST /api/enterprise/webhooks/dlq/replay (with recovered endpoint)
    webhook_dispatcher.enable_in_memory_test_mode(simulated_latency_ms=2.0, simulated_failure_rate=0.0)
    res_replay = client.post("/api/enterprise/webhooks/dlq/replay", json={})
    assert res_replay.status_code == 200
    assert res_replay.json["success"] is True

    # 3. DELETE /api/enterprise/webhooks/dlq (purge)
    res_del = client.delete("/api/enterprise/webhooks/dlq")
    assert res_del.status_code == 200
    assert res_del.json["success"] is True


# ---------------------------------------------------------------------------
# Test Category 5: Webhook Subscriptions Management CRUD
# ---------------------------------------------------------------------------

def test_webhook_subscriptions_crud_lifecycle(client):
    """Test full CRUD lifecycle for webhook subscriptions."""
    # Create subscription
    sub_payload = {
        "target_url": "http://subscriber.enterprise.internal/hooks",
        "description": "Enterprise Monitoring Service",
        "subscribed_events": ["BETTAFISH_EXECUTIVE_REPORT_GENERATED", "BETTAFISH_CRITICAL_RISK_ALERT"],
        "secret_key": "sub_secret_999"
    }
    res_create = client.post("/api/enterprise/webhooks/subscriptions", json=sub_payload)
    assert res_create.status_code == 201
    sub_data = res_create.json["subscription"]
    sub_id = sub_data["subscription_id"]
    assert sub_data["target_url"] == sub_payload["target_url"]

    # List subscriptions
    res_list = client.get("/api/enterprise/webhooks/subscriptions")
    assert res_list.status_code == 200
    assert any(s["subscription_id"] == sub_id for s in res_list.json["subscriptions"])

    # Get single subscription
    res_get = client.get(f"/api/enterprise/webhooks/subscriptions/{sub_id}")
    assert res_get.status_code == 200
    assert res_get.json["subscription"]["subscription_id"] == sub_id

    # Delete subscription
    res_delete = client.delete(f"/api/enterprise/webhooks/subscriptions/{sub_id}")
    assert res_delete.status_code == 200
    assert res_delete.json["success"] is True

    # Confirm 404 after deletion
    res_get_deleted = client.get(f"/api/enterprise/webhooks/subscriptions/{sub_id}")
    assert res_get_deleted.status_code == 404


# ---------------------------------------------------------------------------
# Test Category 6: Mock Receiver End-to-End Delivery
# ---------------------------------------------------------------------------

def test_mock_webhook_receiver_end_to_end(client):
    """Verify mock receiver receives and logs webhook headers and payloads."""
    # Clear mock history
    client.delete("/api/enterprise/webhooks/mock-receiver/history")

    # Send directly to mock receiver
    payload = {"simulation_id": "sim_7788", "round": 3, "status": "COMPLETED"}
    headers = {
        "X-Mirofish-Signature": "sha256=1234567890abcdef",
        "X-Mirofish-Timestamp": str(int(time.time())),
        "X-Mirofish-Event": "SIMULATION_ROUND_COMPLETED",
        "X-Mirofish-Delivery": "del_mock_001"
    }
    res_send = client.post("/api/enterprise/webhooks/mock-receiver", json=payload, headers=headers)
    assert res_send.status_code == 200
    assert res_send.json["received"] is True

    # Verify history
    res_hist = client.get("/api/enterprise/webhooks/mock-receiver/history")
    assert res_hist.status_code == 200
    assert res_hist.json["count"] >= 1
    last_event = res_hist.json["history"][-1]
    assert last_event["event_type"] == "SIMULATION_ROUND_COMPLETED"
    assert last_event["payload"]["simulation_id"] == "sim_7788"


# ---------------------------------------------------------------------------
# Test Category 7: FastMCP REST Proxy & Tool Execution
# ---------------------------------------------------------------------------

def test_fastmcp_rest_proxy_and_health(client):
    """Test FastMCP REST tools catalog and health check."""
    # Tools endpoint
    res_tools = client.get("/api/mcp/tools")
    assert res_tools.status_code == 200
    assert res_tools.json["success"] is True
    assert res_tools.json["count"] >= 11
    tool_names = [t["name"] for t in res_tools.json["tools"]]
    assert "audit_system_diagnostics" in tool_names
    assert "bettafish_generate_c_level_report" in tool_names

    # Health endpoint
    res_health = client.get("/api/mcp/health")
    assert res_health.status_code == 200
    assert res_health.json["status"] == "healthy"


def test_fastmcp_tool_invocation_and_webhook_dispatch(client):
    """Invoking tool via REST must succeed and trigger MCP_TOOL_INVOKED webhook."""
    webhook_dispatcher.enable_in_memory_test_mode(simulated_latency_ms=2.0, simulated_failure_rate=0.0)

    invoke_payload = {
        "tool_name": "audit_system_diagnostics",
        "parameters": {},
        "broadcast_webhook": True
    }
    res_invoke = client.post("/api/enterprise/mcp/invoke", json=invoke_payload)
    assert res_invoke.status_code == 200
    assert res_invoke.json["success"] is True
    assert res_invoke.json["tool_name"] == "audit_system_diagnostics"
    assert res_invoke.json["result"]["status"] == "HEALTHY"
    assert res_invoke.json["webhook_dispatched"] is True


# ---------------------------------------------------------------------------
# Test Category 8: BettaFish Executive Report & Risk Alert Webhook Integration
# ---------------------------------------------------------------------------

def test_bettafish_executive_report_webhook_broadcast(client):
    """Generating C-Level executive report must automatically broadcast webhook."""
    webhook_dispatcher.enable_in_memory_test_mode(simulated_latency_ms=2.0, simulated_failure_rate=0.0)

    report_payload = {
        "topic": "Strategi Penetrasi Pasar AI Asia Tenggara",
        "broadcast_webhook": True
    }
    res = client.post("/api/enterprise/bettafish/executive-report", json=report_payload)
    assert res.status_code == 200
    assert res.json["success"] is True
    assert "report" in res.json
    assert res.json["webhook_dispatched"] is True
    assert res.json["report"]["provenance_chain_status"] == "SHA-256_CHAIN_VERIFIED"


def test_bettafish_critical_risk_alert_webhook(client):
    """High risk assessment must trigger BETTAFISH_CRITICAL_RISK_ALERT webhook."""
    webhook_dispatcher.enable_in_memory_test_mode(simulated_latency_ms=2.0, simulated_failure_rate=0.0)

    risk_payload = {
        "text": "BOIKOT TOTAL DAN RUNTUHKAN SERVER PERUSAHAAN INI!",
        "claim_polarities": [{"claim": "Skandal keamanan data masif", "polarity": -0.95}],
        "virality_potential": 0.98,
        "broadcast_webhook": True
    }
    res = client.post("/api/enterprise/bettafish/risk-assessment", json=risk_payload)
    assert res.status_code == 200
    assert res.json["success"] is True
    assert res.json["alert_dispatched"] is True
    assert res.json["risk_assessment"]["overall_risk_level"] in ("HIGH", "CRITICAL")
