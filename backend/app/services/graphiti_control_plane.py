"""
MiroFish Enterprise Graphiti Control Plane Server (Agent 06: Divisi B)
Menyediakan Starlette/FastAPI & FastMCP Control Plane pada port 8080/8090 untuk
operasi subgraf lokal performa tinggi (<100ms) terhubung ke FalkorDB & Neo4j.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette.exceptions import HTTPException

from .graphiti_service import (
    GraphitiService,
    GraphitiNode,
    BiTemporalEdge,
    SubgraphQueryResult
)

logger = logging.getLogger("mirofish.graphiti.control_plane")


# =============================================================================
# Pydantic Schemas for Control Plane API
# =============================================================================

class UpsertNodeRequest(BaseModel):
    project_id: str
    node_id: str
    labels: List[str] = Field(default_factory=lambda: ["Entity"])
    properties: Dict[str, Any] = Field(default_factory=dict)


class AddEdgeRequest(BaseModel):
    project_id: str
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class InvalidateEdgeRequest(BaseModel):
    project_id: str
    source_id: str
    target_id: str
    relation_type: str
    valid_to: Optional[str] = None


class SubgraphQueryRequest(BaseModel):
    project_id: str
    label_filter: Optional[str] = None
    limit: int = 100
    as_of: Optional[str] = None
    center_node_id: Optional[str] = None
    max_depth: int = 2


class IngestionRequest(BaseModel):
    text: str
    group_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SettingValue(BaseModel):
    value: str


# =============================================================================
# Starlette / ASGI Control Plane App
# =============================================================================

def create_control_plane_app(service: Optional[GraphitiService] = None) -> Starlette:
    """Factory untuk membuat aplikasi ASGI Graphiti Control Plane."""
    svc = service or GraphitiService()
    settings_store: Dict[str, str] = {}

    async def health(request: Request) -> JSONResponse:
        hc = svc.health_check()
        return JSONResponse(hc)

    async def api_upsert_node(request: Request) -> JSONResponse:
        body = await request.json()
        req = UpsertNodeRequest(**body)
        node = svc.upsert_node(
            project_id=req.project_id,
            node_id=req.node_id,
            labels=req.labels,
            properties=req.properties
        )
        return JSONResponse({"status": "ok", "node": node.model_dump()})

    async def api_add_edge(request: Request) -> JSONResponse:
        body = await request.json()
        req = AddEdgeRequest(**body)
        edge = svc.add_bitemporal_edge(
            project_id=req.project_id,
            source_id=req.source_id,
            target_id=req.target_id,
            relation_type=req.relation_type,
            properties=req.properties,
            valid_from=req.valid_from,
            valid_to=req.valid_to
        )
        return JSONResponse({"status": "ok", "edge": edge.model_dump()})

    async def api_invalidate_edge(request: Request) -> JSONResponse:
        body = await request.json()
        req = InvalidateEdgeRequest(**body)
        success = svc.invalidate_edge(
            project_id=req.project_id,
            source_id=req.source_id,
            target_id=req.target_id,
            relation_type=req.relation_type,
            valid_to=req.valid_to
        )
        return JSONResponse({"status": "ok", "invalidated": success})

    async def api_get_subgraph(request: Request) -> JSONResponse:
        project_id = request.path_params.get("project_id", "")
        params = request.query_params
        label_filter = params.get("label_filter")
        limit = int(params.get("limit", 100))
        as_of = params.get("as_of")
        center_node_id = params.get("center_node_id")
        max_depth = int(params.get("max_depth", 2))

        result = svc.query_subgraph(
            project_id=project_id,
            label_filter=label_filter,
            limit=limit,
            as_of=as_of,
            center_node_id=center_node_id,
            max_depth=max_depth
        )
        return JSONResponse(result.model_dump())

    async def api_query_subgraph(request: Request) -> JSONResponse:
        body = await request.json()
        req = SubgraphQueryRequest(**body)
        result = svc.query_subgraph(
            project_id=req.project_id,
            label_filter=req.label_filter,
            limit=req.limit,
            as_of=req.as_of,
            center_node_id=req.center_node_id,
            max_depth=req.max_depth
        )
        return JSONResponse(result.model_dump())

    async def api_get_entity(request: Request) -> JSONResponse:
        project_id = request.path_params.get("project_id", "")
        entity_name = request.path_params.get("entity_name", "")
        as_of = request.query_params.get("as_of")
        ctx = svc.get_entity_context(graph_id=project_id, entity_name=entity_name, as_of=as_of)
        return JSONResponse(ctx)

    async def api_ingest_fact(request: Request) -> JSONResponse:
        body = await request.json()
        req = IngestionRequest(**body)
        fact_item = {
            "source": req.metadata.get("source") or req.metadata.get("entity") or req.text[:40].strip(),
            "target": req.metadata.get("target") or req.metadata.get("value") or "EntityFact",
            "relation": req.metadata.get("relation") or "INGESTED_AS",
            "content": req.text,
            "metadata": req.metadata
        }
        svc.add_facts(graph_id=req.group_id, facts=[fact_item])
        return JSONResponse({"status": "enqueued", "group_id": req.group_id, "processed": 1})

    async def api_set_setting(request: Request) -> JSONResponse:
        setting_key = request.path_params.get("setting_key", "")
        body = await request.json()
        req = SettingValue(**body)
        settings_store[setting_key] = req.value
        if setting_key.startswith("graph_group_"):
            graph_id = setting_key.replace("graph_group_", "")
            try:
                data = json.loads(req.value)
                name = data.get("name", graph_id)
            except Exception:
                name = graph_id
            svc.create_graph(graph_id=graph_id, name=name)
        return JSONResponse({"status": "ok", "key": setting_key})

    async def api_get_setting(request: Request) -> JSONResponse:
        setting_key = request.path_params.get("setting_key", "")
        if setting_key not in settings_store:
            return JSONResponse({"detail": "Setting not found"}, status_code=404)
        return JSONResponse({"key": setting_key, "value": settings_store[setting_key]})

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/api/nodes", api_upsert_node, methods=["POST"]),
        Route("/api/edges", api_add_edge, methods=["POST"]),
        Route("/api/edges/invalidate", api_invalidate_edge, methods=["POST"]),
        Route("/api/subgraph/{project_id}", api_get_subgraph, methods=["GET"]),
        Route("/api/subgraph/query", api_query_subgraph, methods=["POST"]),
        Route("/api/entity/{project_id}/{entity_name}", api_get_entity, methods=["GET"]),
        Route("/api/ingestion", api_ingest_fact, methods=["POST"]),
        Route("/api/settings/{setting_key}", api_set_setting, methods=["PUT"]),
        Route("/api/settings/{setting_key}", api_get_setting, methods=["GET"]),
    ]

    return Starlette(debug=False, routes=routes)


# =============================================================================
# FastMCP Integration
# =============================================================================

def create_fastmcp_server(service: Optional[GraphitiService] = None):
    """Membuat instance FastMCP server untuk MiroFish Graphiti Control Plane."""
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        logger.warning("mcp.server.fastmcp tidak tersedia; FastMCP dinonaktifkan.")
        return None

    svc = service or GraphitiService()
    mcp = FastMCP("MiroFish-Graphiti-ControlPlane")

    @mcp.tool()
    def graphiti_upsert_node(project_id: str, node_id: str, labels: List[str], properties: Optional[Dict[str, Any]] = None) -> str:
        """Menyimpan simpul baru atau memperbarui properti simpul dalam subgraf project_id."""
        node = svc.upsert_node(project_id, node_id, labels, properties or {})
        return json.dumps(node.model_dump())

    @mcp.tool()
    def graphiti_add_bitemporal_edge(
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None
    ) -> str:
        """Menambahkan edge berorientasi waktu (bi-temporal) antara dua simpul."""
        edge = svc.add_bitemporal_edge(project_id, source_id, target_id, relation_type, properties or {}, valid_from, valid_to)
        return json.dumps(edge.model_dump())

    @mcp.tool()
    def graphiti_query_subgraph(
        project_id: str,
        label_filter: Optional[str] = None,
        limit: int = 100,
        as_of: Optional[str] = None,
        center_node_id: Optional[str] = None,
        max_depth: int = 2
    ) -> str:
        """Kueri subgraf terisolasi per project_id dengan filter label dan temporal snapshot as_of (<100ms)."""
        res = svc.query_subgraph(project_id, label_filter, limit, as_of, center_node_id, max_depth)
        return json.dumps(res.model_dump())

    @mcp.tool()
    def graphiti_search_facts(project_id: str, query: str, limit: int = 10, as_of: Optional[str] = None) -> str:
        """Pencarian fakta semantik/temporal berkecepatan tinggi."""
        facts = svc.search_temporal_facts(project_id, query, limit, as_of)
        return json.dumps(facts)

    @mcp.tool()
    def graphiti_get_entity(project_id: str, entity_name: str, as_of: Optional[str] = None) -> str:
        """Mengambil profil entitas beserta koneksi relasi aktifnya."""
        ctx = svc.get_entity_context(project_id, entity_name, as_of)
        return json.dumps(ctx)

    @mcp.tool()
    def graphiti_invalidate_edge(
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        valid_to: Optional[str] = None
    ) -> str:
        """Menandai berakhirnya masa berlaku (invalidation) sebuah edge bi-temporal."""
        ok = svc.invalidate_edge(project_id, source_id, target_id, relation_type, valid_to)
        return json.dumps({"invalidated": ok})

    @mcp.tool()
    def graphiti_health() -> str:
        """Memeriksa status kesehatan FalkorDB dan Control Plane."""
        return json.dumps(svc.health_check())

    return mcp


def register_graphiti_canonical_tools(mcp_instance: Any, service: Optional[GraphitiService] = None):
    """Mendaftarkan tool Graphiti ke instance FastMCP yang ada (Agent 17 Canonical FastMCP Server)."""
    svc = service or GraphitiService()

    @mcp_instance.tool(name="graphiti_query_subgraph", description="Kueri subgraf terisolasi per project_id dengan filter label dan temporal snapshot as_of.")
    def query_subgraph(project_id: str, label_filter: Optional[str] = None, limit: int = 100, as_of: Optional[str] = None) -> str:
        res = svc.query_subgraph(project_id, label_filter, limit, as_of)
        return json.dumps(res.model_dump())

    @mcp_instance.tool(name="graphiti_search_facts", description="Pencarian fakta semantik dan temporal Graphiti berkecepatan tinggi.")
    def search_facts(project_id: str, query: str, limit: int = 10, as_of: Optional[str] = None) -> str:
        facts = svc.search_temporal_facts(project_id, query, limit, as_of)
        return json.dumps(facts)



if __name__ == "__main__":
    import uvicorn
    listen_port = int(os.environ.get("GRAPHITI_CONTROL_PLANE_PORT", "8090"))
    app = create_control_plane_app()
    logger.info(f"Memulai Graphiti Control Plane pada port {listen_port}...")
    uvicorn.run(app, host="0.0.0.0", port=listen_port)
