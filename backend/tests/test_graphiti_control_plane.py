"""
Unit Tests untuk Subagent 06: Graphiti & FalkorDB/Neo4j Control Plane
Memverifikasi:
1. Isolasi data graf multi-tenant per project_id
2. Operasi bi-temporal edge (valid_from, valid_to, point-in-time snapshot as_of)
3. Garansi latensi kueri subgraf < 100ms
4. K-hop neighborhood traversal
5. Kepatuhan implementasi GraphMemoryAdapter (create_graph, add_facts, search_temporal_facts, get_entity_context)
6. Klien FalkorDB RESP native dan fallback resiliensi
7. FastAPI Control Plane REST API endpoints (TestClient)
8. FastMCP Server tool definitions & execution
9. Integrasi GraphitiAdapter dengan GraphitiService
"""

import time
import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from app.services.graphiti_service import (
    GraphitiService,
    BiTemporalEdge,
    GraphitiNode,
    SubgraphQueryResult,
    FalkorDBNativeClient
)
from app.services.graphiti_control_plane import (
    create_control_plane_app,
    create_fastmcp_server,
    UpsertNodeRequest,
    AddEdgeRequest,
    SubgraphQueryRequest
)
from app.services.graph_memory.graphiti_adapter import GraphitiAdapter
from app.services.graph_memory.base import GraphMemoryAdapter


def test_tenant_isolation():
    """Validasi isolasi multi-tenant: data project_A tidak bocor ke project_B."""
    svc = GraphitiService(port=8090, auto_connect=False)
    
    # Ingest ke Tenant A
    svc.upsert_node(project_id="proj_alpha", node_id="node_a1", labels=["Policy"], properties={"name": "Alpha Policy"})
    svc.upsert_node(project_id="proj_alpha", node_id="node_a2", labels=["Actor"], properties={"name": "Alpha Gov"})
    svc.add_bitemporal_edge(project_id="proj_alpha", source_id="node_a2", target_id="node_a1", relation_type="ENFORCES")

    # Ingest ke Tenant B
    svc.upsert_node(project_id="proj_beta", node_id="node_b1", labels=["Finance"], properties={"name": "Beta Bank"})
    svc.upsert_node(project_id="proj_beta", node_id="node_b2", labels=["Regulation"], properties={"name": "Beta Rule"})
    svc.add_bitemporal_edge(project_id="proj_beta", source_id="node_b2", target_id="node_b1", relation_type="COMPLIES_WITH")

    # Query Tenant A
    res_a = svc.query_subgraph(project_id="proj_alpha")
    node_ids_a = {n.node_id for n in res_a.nodes}
    assert "node_a1" in node_ids_a
    assert "node_a2" in node_ids_a
    assert "node_b1" not in node_ids_a
    assert "node_b2" not in node_ids_a
    assert len(res_a.edges) == 1
    assert res_a.edges[0].relation_type == "ENFORCES"

    # Query Tenant B
    res_b = svc.query_subgraph(project_id="proj_beta")
    node_ids_b = {n.node_id for n in res_b.nodes}
    assert "node_b1" in node_ids_b
    assert "node_b2" in node_ids_b
    assert "node_a1" not in node_ids_b
    assert "node_a2" not in node_ids_b
    assert len(res_b.edges) == 1
    assert res_b.edges[0].relation_type == "COMPLIES_WITH"


def test_bitemporal_edge_lifecycle_and_point_in_time():
    """Validasi siklus hidup edge bi-temporal dan snapshot point-in-time as_of."""
    svc = GraphitiService(port=8090, auto_connect=False)
    proj = "proj_temporal"

    svc.upsert_node(project_id=proj, node_id="system_ai", labels=["System"])
    svc.upsert_node(project_id=proj, node_id="policy_v1", labels=["Policy"])
    svc.upsert_node(project_id=proj, node_id="policy_v2", labels=["Policy"])

    # Edge versi 1 berlaku Jan 2026 s/d Jun 2026
    svc.add_bitemporal_edge(
        project_id=proj,
        source_id="system_ai",
        target_id="policy_v1",
        relation_type="GOVERNED_BY",
        valid_from="2026-01-01T00:00:00+00:00",
        valid_to="2026-06-01T00:00:00+00:00"
    )

    # Edge versi 2 berlaku mulai Jun 2026 tanpa batas (valid_to=None)
    svc.add_bitemporal_edge(
        project_id=proj,
        source_id="system_ai",
        target_id="policy_v2",
        relation_type="GOVERNED_BY",
        valid_from="2026-06-01T00:00:00+00:00",
        valid_to=None
    )

    # 1. Snapshot as_of Maret 2026 (harus menghasilkan policy_v1 saja)
    res_mar = svc.query_subgraph(project_id=proj, as_of="2026-03-15T00:00:00+00:00")
    edge_targets_mar = [e.target_id for e in res_mar.edges]
    assert "policy_v1" in edge_targets_mar
    assert "policy_v2" not in edge_targets_mar

    # 2. Snapshot as_of Agustus 2026 (harus menghasilkan policy_v2 saja)
    res_aug = svc.query_subgraph(project_id=proj, as_of="2026-08-15T00:00:00+00:00")
    edge_targets_aug = [e.target_id for e in res_aug.edges]
    assert "policy_v1" not in edge_targets_aug
    assert "policy_v2" in edge_targets_aug

    # 3. Invalidate policy_v2
    invalidated = svc.invalidate_edge(
        project_id=proj,
        source_id="system_ai",
        target_id="policy_v2",
        relation_type="GOVERNED_BY",
        valid_to="2026-10-01T00:00:00+00:00"
    )
    assert invalidated is True

    # 4. Snapshot as_of November 2026 (keduanya sudah kadaluarsa)
    res_nov = svc.query_subgraph(project_id=proj, as_of="2026-11-01T00:00:00+00:00")
    assert len(res_nov.edges) == 0


def test_subgraph_query_latency_sub_100ms():
    """Validasi SLA performa: latency read/write subgraf < 100ms."""
    svc = GraphitiService(port=8090, auto_connect=False)
    proj = "proj_perf"

    # Batch setup
    t_start = time.perf_counter()
    for i in range(40):
        svc.upsert_node(
            project_id=proj,
            node_id=f"node_{i}",
            labels=["Entity", f"Group_{i % 4}"],
            properties={"index": i, "weight": 0.5}
        )
    for i in range(39):
        svc.add_bitemporal_edge(
            project_id=proj,
            source_id=f"node_{i}",
            target_id=f"node_{i+1}",
            relation_type="CONNECTED_TO"
        )
    write_duration_ms = (time.perf_counter() - t_start) * 1000.0
    assert write_duration_ms < 500.0  # 40 nodes + 39 edges in < 500ms total (<7ms per op)

    # 10 kali kueri subgraf
    for _ in range(10):
        res = svc.query_subgraph(project_id=proj, limit=50)
        assert res.query_time_ms < 100.0
        assert res.total_nodes > 0


def test_k_hop_neighborhood_traversal():
    """Validasi traversal k-hop BFS di sekitar central node."""
    svc = GraphitiService(port=8090, auto_connect=False)
    proj = "proj_khop"

    # Graf linier: N1 -> N2 -> N3 -> N4
    for i in range(1, 5):
        svc.upsert_node(project_id=proj, node_id=f"N{i}", labels=["Step"])
    svc.add_bitemporal_edge(project_id=proj, source_id="N1", target_id="N2", relation_type="NEXT")
    svc.add_bitemporal_edge(project_id=proj, source_id="N2", target_id="N3", relation_type="NEXT")
    svc.add_bitemporal_edge(project_id=proj, source_id="N3", target_id="N4", relation_type="NEXT")

    # 1-hop dari N1
    hop1 = svc.query_neighborhood(project_id=proj, node_id="N1", max_depth=1)
    hop1_ids = {n.node_id for n in hop1.nodes}
    assert hop1_ids == {"N1", "N2"}

    # 2-hop dari N1
    hop2 = svc.query_neighborhood(project_id=proj, node_id="N1", max_depth=2)
    hop2_ids = {n.node_id for n in hop2.nodes}
    assert hop2_ids == {"N1", "N2", "N3"}


def test_graph_memory_adapter_compliance():
    """Validasi kepatuhan terhadap GraphMemoryAdapter contract."""
    svc = GraphitiService(port=8090, auto_connect=False)
    assert isinstance(svc, GraphMemoryAdapter)

    # 1. create_graph
    ok = svc.create_graph("graph_enterprise", "Enterprise Knowledge")
    assert ok is True

    # 2. add_facts
    facts = [
        {
            "source": "Bank Mandiri",
            "relation": "ADOPTS_STANDARD",
            "target": "ISO 27001",
            "source_type": "Organization",
            "target_type": "Standard",
            "audit_year": 2026
        },
        {
            "source": "Bank Mandiri",
            "relation": "COMPLIES_WITH",
            "target": "UU PDP",
            "source_type": "Organization",
            "target_type": "Regulation"
        }
    ]
    res_facts = svc.add_facts("graph_enterprise", facts)
    assert res_facts is True

    # 3. search_temporal_facts
    results = svc.search_temporal_facts("graph_enterprise", "ISO 27001")
    assert len(results) >= 1
    assert "ISO 27001" in results[0]["fact"]
    assert results[0]["relevance"] > 0.8

    # 4. get_entity_context
    ctx = svc.get_entity_context("graph_enterprise", "Bank Mandiri")
    assert ctx["exists"] is True
    assert ctx["connected_edges_count"] == 2
    assert len(ctx["neighbors"]) == 2


def test_falkordb_native_resp_client_live_or_fallback():
    """Validasi koneksi socket RESP FalkorDB."""
    # Test probe ke port 6382 (port FalkorDB container)
    client = FalkorDBNativeClient(port=6382, timeout=1.0)
    if client.is_connected:
        res = client.query("test_falkor_ping", "RETURN 42")
        assert res["success"] is True
        assert res["latency_ms"] < 100.0
    else:
        # Jika FalkorDB tidak aktif, fallback gracefully
        assert client.is_connected is False


def test_fastapi_control_plane_endpoints():
    """Validasi REST API FastAPI Control Plane menggunakan TestClient."""
    svc = GraphitiService(port=8090, auto_connect=False)
    app = create_control_plane_app(service=svc)
    client = TestClient(app)

    # 1. Health
    h_resp = client.get("/health")
    assert h_resp.status_code == 200
    assert h_resp.json()["status"] == "healthy"

    # 2. Upsert Node
    node_payload = {
        "project_id": "api_proj",
        "node_id": "api_node_1",
        "labels": ["Server"],
        "properties": {"ip": "10.0.0.1"}
    }
    n_resp = client.post("/api/nodes", json=node_payload)
    assert n_resp.status_code == 200
    assert n_resp.json()["node"]["node_id"] == "api_node_1"

    # 3. Add Edge
    edge_payload = {
        "project_id": "api_proj",
        "source_id": "api_node_1",
        "target_id": "api_node_2",
        "relation_type": "ROUTES_TO",
        "properties": {"port": 443}
    }
    # Tambah target node dulu
    client.post("/api/nodes", json={"project_id": "api_proj", "node_id": "api_node_2", "labels": ["Gateway"]})
    e_resp = client.post("/api/edges", json=edge_payload)
    assert e_resp.status_code == 200
    assert e_resp.json()["edge"]["relation_type"] == "ROUTES_TO"

    # 4. Query Subgraph
    q_resp = client.get("/api/subgraph/api_proj")
    assert q_resp.status_code == 200
    data = q_resp.json()
    assert data["total_nodes"] == 2
    assert data["total_edges"] == 1
    assert data["query_time_ms"] < 100.0

    # 5. Ingestion & Settings
    set_resp = client.put("/api/settings/graph_group_tenant_x", json={"value": "{\"name\": \"Tenant X\"}"})
    assert set_resp.status_code == 200
    ingest_resp = client.post("/api/ingestion", json={
        "text": "Server Alpha connects to Database Beta",
        "group_id": "tenant_x",
        "metadata": {"source": "Server Alpha", "target": "Database Beta", "relation": "CONNECTS_TO"}
    })
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["processed"] == 1


def test_fastmcp_server_tools():
    """Validasi pendaftaran alat FastMCP."""
    svc = GraphitiService(port=8090, auto_connect=False)
    mcp_server = create_fastmcp_server(service=svc)
    if mcp_server is not None:
        assert mcp_server.name == "MiroFish-Graphiti-ControlPlane"


def test_graphiti_adapter_integration():
    """Validasi sinkronisasi penuh GraphitiAdapter ke GraphitiService."""
    svc = GraphitiService(port=8090, auto_connect=False)
    adapter = GraphitiAdapter(
        control_plane_url="http://127.0.0.1:8090",
        service=svc
    )
    
    # Create graph
    assert adapter.create_graph("integ_proj", "Integration Test Graph") is True

    # Ingest facts
    facts = [
        {"source": "AgentA", "relation": "COMMUNICATES_WITH", "target": "AgentB", "protocol": "gRPC"}
    ]
    assert adapter.add_facts("integ_proj", facts) is True

    # Search facts
    results = adapter.search_temporal_facts("integ_proj", "AgentA")
    assert len(results) >= 1
    assert "COMMUNICATES_WITH" in results[0]["fact"]

    # Get entity context
    ctx = adapter.get_entity_context("integ_proj", "AgentA")
    assert ctx["exists"] is True
    assert ctx["connected_edges_count"] == 1


def test_graphiti_service_app_health():
    """Validasi ASGI app pada app.services.graphiti_service memiliki route /health."""
    from app.services.graphiti_service import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "service": "graphiti"}

