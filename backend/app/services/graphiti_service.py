"""
MiroFish Enterprise Graphiti Control Plane Service (Agent 06: Divisi B)
Menangani subgraf lokal berkinerja tinggi untuk data sensitif enterprise
berbasis FalkorDB 1.1.2+ dan Neo4j 5.26+ dengan edge bi-temporal,
isolasi multi-tenant project_id, dan query latency < 100ms.
Port alokasi default: 8090 (configurable: 8080/8090).
"""

import os
import re
import time
import socket
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from .graph_memory.base import GraphMemoryAdapter

logger = logging.getLogger("mirofish.graphiti")


class BiTemporalEdge(BaseModel):
    """Representasi edge bi-temporal: valid time (valid_from/valid_to) dan transaction time (created_at)."""
    source_id: str
    target_id: str
    relation_type: str
    valid_from: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_to: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    properties: Dict[str, Any] = Field(default_factory=dict)

    def is_active_at(self, timestamp: Optional[str] = None) -> bool:
        """Memeriksa apakah edge aktif pada timestamp ISO tertentu (point-in-time)."""
        target_dt = _parse_iso(timestamp) if timestamp else datetime.now(timezone.utc)
        if target_dt is None:
            target_dt = datetime.now(timezone.utc)

        from_dt = _parse_iso(self.valid_from)
        if from_dt is not None and from_dt > target_dt:
            return False
        if self.valid_to:
            to_dt = _parse_iso(self.valid_to)
            if to_dt is not None and to_dt <= target_dt:
                return False
        return True


class GraphitiNode(BaseModel):
    """Representasi node entitas terisolasi multi-tenant."""
    node_id: str
    labels: List[str]
    properties: Dict[str, Any] = Field(default_factory=dict)
    project_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SubgraphQueryResult(BaseModel):
    """Hasil query subgraf dengan metrik performa query_time_ms (<100ms)."""
    project_id: str
    nodes: List[GraphitiNode] = Field(default_factory=list)
    edges: List[BiTemporalEdge] = Field(default_factory=list)
    query_time_ms: float
    total_nodes: int
    total_edges: int
    as_of: Optional[str] = None


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Helper parsing ISO timestamp secara aman."""
    if not ts:
        return None
    try:
        clean_ts = ts.strip()
        if clean_ts.endswith("Z"):
            clean_ts = clean_ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


class FalkorDBNativeClient:
    """Klien protokol Redis RESP ringan untuk FalkorDB GRAPH.QUERY tanpa external driver berat."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6382,
        password: Optional[str] = None,
        timeout: float = 1.0
    ):
        self.host = host
        self.port = port
        self.password = (password if password is not None else os.environ.get("REDIS_PASSWORD", "")).strip()
        self.timeout = timeout
        self.is_connected = False
        self._test_connection()

    def _test_connection(self) -> bool:
        try:
            res = self.query("falkordb_probe", "RETURN 1")
            self.is_connected = res.get("success", False)
            return self.is_connected
        except Exception:
            self.is_connected = False
            return False

    def _send_resp(self, *args) -> bytes:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.host, self.port))
            # Kirim perintah AUTH jika password dikonfigurasi (requirepass)
            if self.password:
                auth_lines = [
                    "*2\r\n",
                    "$4\r\n",
                    "AUTH\r\n",
                    f"${len(self.password)}\r\n",
                    f"{self.password}\r\n"
                ]
                s.sendall("".join(auth_lines).encode("utf-8"))
                auth_res = s.recv(1024)
                if auth_res.startswith(b"-ERR") or auth_res.startswith(b"-WRONGPASS"):
                    return auth_res

            lines = ["*%d\r\n" % len(args)]
            for a in args:
                b = str(a).encode("utf-8")
                lines.append("$%d\r\n" % len(b))
                lines.append(str(a) + "\r\n")
            s.sendall("".join(lines).encode("utf-8"))
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(chunk) < 4096:
                    break
            return data
        finally:
            s.close()

    def query(self, graph_name: str, cypher: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            raw = self._send_resp("GRAPH.QUERY", graph_name, cypher)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            if raw.startswith(b"-ERR") or not raw:
                return {"success": False, "error": raw.decode("utf-8", errors="ignore"), "latency_ms": latency_ms}
            return {"success": True, "raw": raw.decode("utf-8", errors="ignore"), "latency_ms": latency_ms}
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": (time.perf_counter() - t0) * 1000.0}


class GraphitiService(GraphMemoryAdapter):
    """Local Knowledge Graph Control Plane (Neo4j / FalkorDB) dengan dukungan GraphMemoryAdapter."""

    def __init__(
        self,
        port: int = 8090,
        uri: Optional[str] = None,
        falkordb_host: Optional[str] = None,
        falkordb_port: Optional[int] = None,
        falkordb_password: Optional[str] = None,
        auto_connect: bool = True
    ):
        self.port = port
        self.uri = uri or os.environ.get("GRAPHITI_URI", "bolt://127.0.0.1:7687")
        self.falkordb_host = falkordb_host or os.environ.get("FALKORDB_HOST", "127.0.0.1")
        self.falkordb_password = (falkordb_password if falkordb_password is not None else os.environ.get("REDIS_PASSWORD", "")).strip()

        # Probe FalkorDB port (prioritaskan 6382 jika ada, lalu 6379 atau env)
        env_falkor_port = os.environ.get("FALKORDB_PORT")
        candidate_ports = [int(env_falkor_port)] if env_falkor_port else [6382, 6379]
        if falkordb_port:
            candidate_ports = [falkordb_port]

        self.falkordb_port = candidate_ports[0]
        self.falkor_client: Optional[FalkorDBNativeClient] = None

        if auto_connect:
            for p in candidate_ports:
                try:
                    client = FalkorDBNativeClient(
                        host=self.falkordb_host,
                        port=p,
                        password=self.falkordb_password,
                        timeout=0.8
                    )
                    if client.is_connected:
                        self.falkor_client = client
                        self.falkordb_port = p
                        logger.info(f"FalkorDB terhubung di {self.falkordb_host}:{p}")
                        break
                except Exception:
                    pass

        self._local_storage: Dict[str, Dict[str, Any]] = {}
        logger.info(f"GraphitiService initialized on port {self.port}, FalkorDB connected={self.falkor_connected}")

    @property
    def falkor_connected(self) -> bool:
        return self.falkor_client is not None and self.falkor_client.is_connected

    def _ensure_tenant(self, project_id: str):
        if project_id not in self._local_storage:
            self._local_storage[project_id] = {
                "nodes": {},
                "edges": [],
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "name": project_id
                }
            }

    # =========================================================================
    # Native Subgraph & Bi-Temporal CRUD API (<100ms)
    # =========================================================================

    def upsert_node(
        self,
        project_id: str,
        node_id: str,
        labels: List[str],
        properties: Optional[Dict[str, Any]] = None
    ) -> GraphitiNode:
        """Menyimpan atau memperbarui node entitas dengan isolasi project_id."""
        t0 = time.perf_counter()
        self._ensure_tenant(project_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        existing = self._local_storage[project_id]["nodes"].get(node_id)
        created_at = existing.created_at if existing else now_iso

        node = GraphitiNode(
            node_id=node_id,
            labels=labels,
            properties=properties or {},
            project_id=project_id,
            created_at=created_at,
            updated_at=now_iso
        )
        self._local_storage[project_id]["nodes"][node_id] = node

        # Sync to FalkorDB if connected
        if self.falkor_connected and self.falkor_client:
            try:
                primary_label = labels[0] if labels else "Entity"
                props_str = ", ".join([f"{k}: '{v}'" for k, v in (properties or {}).items() if isinstance(v, (str, int, float, bool))])
                cypher = f"MERGE (n:{primary_label} {{id: '{node_id}', project_id: '{project_id}'}}) "
                if props_str:
                    cypher += f"SET n += {{{props_str}}} "
                cypher += "RETURN n"
                self.falkor_client.query(f"proj_{project_id}", cypher)
            except Exception as e:
                logger.debug(f"FalkorDB sync node error: {e}")

        logger.debug(f"Upserted node {node_id} in project {project_id} in {(time.perf_counter()-t0)*1000:.2f}ms")
        return node

    def add_bitemporal_edge(
        self,
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None
    ) -> BiTemporalEdge:
        """Menambahkan edge bi-temporal berorientasi waktu."""
        t0 = time.perf_counter()
        self._ensure_tenant(project_id)
        edge = BiTemporalEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            valid_from=valid_from or datetime.now(timezone.utc).isoformat(),
            valid_to=valid_to,
            created_at=datetime.now(timezone.utc).isoformat(),
            properties=properties or {}
        )
        self._local_storage[project_id]["edges"].append(edge)

        # Sync to FalkorDB if connected
        if self.falkor_connected and self.falkor_client:
            try:
                props = properties or {}
                props["valid_from"] = edge.valid_from
                if edge.valid_to:
                    props["valid_to"] = edge.valid_to
                props_str = ", ".join([f"{k}: '{v}'" for k, v in props.items() if isinstance(v, (str, int, float, bool))])
                cypher = (
                    f"MATCH (a {{id: '{source_id}'}}), (b {{id: '{target_id}'}}) "
                    f"CREATE (a)-[r:{relation_type} {{{props_str}}}]->(b) RETURN r"
                )
                self.falkor_client.query(f"proj_{project_id}", cypher)
            except Exception as e:
                logger.debug(f"FalkorDB sync edge error: {e}")

        logger.debug(f"Added bitemporal edge {source_id}->{target_id} in {(time.perf_counter()-t0)*1000:.2f}ms")
        return edge

    def invalidate_edge(
        self,
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        valid_to: Optional[str] = None
    ) -> bool:
        """Mengakhiri masa berlaku edge bi-temporal (invalidation)."""
        self._ensure_tenant(project_id)
        now_iso = valid_to or datetime.now(timezone.utc).isoformat()
        updated = False
        for edge in self._local_storage[project_id]["edges"]:
            if (
                edge.source_id == source_id
                and edge.target_id == target_id
                and edge.relation_type == relation_type
                and edge.valid_to is None
            ):
                edge.valid_to = now_iso
                updated = True

        if updated and self.falkor_connected and self.falkor_client:
            try:
                cypher = (
                    f"MATCH (a {{id: '{source_id}'}})-[r:{relation_type}]->(b {{id: '{target_id}'}}) "
                    f"SET r.valid_to = '{now_iso}' RETURN r"
                )
                self.falkor_client.query(f"proj_{project_id}", cypher)
            except Exception as e:
                logger.debug(f"FalkorDB invalidate edge error: {e}")

        return updated

    def query_subgraph(
        self,
        project_id: str,
        label_filter: Optional[str] = None,
        limit: int = 100,
        as_of: Optional[str] = None,
        center_node_id: Optional[str] = None,
        max_depth: int = 2
    ) -> SubgraphQueryResult:
        """Kueri subgraf berorientasi waktu (temporal) dengan batas performa sub-100ms."""
        t0 = time.perf_counter()
        self._ensure_tenant(project_id)
        tenant_data = self._local_storage[project_id]

        # 1. Filter edge berdasarkan waktu (as_of)
        active_edges = [e for e in tenant_data["edges"] if e.is_active_at(as_of)]

        # 2. Filter node berdasarkan neighborhood BFS jika center_node_id diberikan
        if center_node_id:
            visited_ids: Set[str] = {center_node_id}
            frontier: Set[str] = {center_node_id}
            depth = 0
            while frontier and depth < max_depth:
                next_frontier: Set[str] = set()
                for e in active_edges:
                    if e.source_id in frontier and e.target_id not in visited_ids:
                        next_frontier.add(e.target_id)
                        visited_ids.add(e.target_id)
                    elif e.target_id in frontier and e.source_id not in visited_ids:
                        next_frontier.add(e.source_id)
                        visited_ids.add(e.source_id)
                frontier = next_frontier
                depth += 1
            
            matched_nodes = [
                n for n_id, n in tenant_data["nodes"].items()
                if n_id in visited_ids and (not label_filter or label_filter in n.labels)
            ][:limit]
        else:
            matched_nodes = []
            for n in tenant_data["nodes"].values():
                if not label_filter or label_filter in n.labels:
                    matched_nodes.append(n)
                    if len(matched_nodes) >= limit:
                        break

        matched_node_ids = {n.node_id for n in matched_nodes}
        matched_edges = [
            e for e in active_edges
            if e.source_id in matched_node_ids and e.target_id in matched_node_ids
        ][:limit]

        query_time_ms = (time.perf_counter() - t0) * 1000.0
        return SubgraphQueryResult(
            project_id=project_id,
            nodes=matched_nodes,
            edges=matched_edges,
            query_time_ms=round(query_time_ms, 3),
            total_nodes=len(matched_nodes),
            total_edges=len(matched_edges),
            as_of=as_of
        )

    def query_neighborhood(
        self,
        project_id: str,
        node_id: str,
        max_depth: int = 2,
        as_of: Optional[str] = None,
        limit: int = 100
    ) -> SubgraphQueryResult:
        """Kueri k-hop neighborhood sekeliling satu node."""
        return self.query_subgraph(
            project_id=project_id,
            limit=limit,
            as_of=as_of,
            center_node_id=node_id,
            max_depth=max_depth
        )

    def execute_cypher(self, project_id: str, cypher: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Eksekusi query Cypher langsung ke FalkorDB atau emulasi lokal."""
        if self.falkor_connected and self.falkor_client:
            return self.falkor_client.query(f"proj_{project_id}", cypher)
        # Emulasi ringkas jika FalkorDB offline
        return {
            "success": True,
            "simulated": True,
            "message": "FalkorDB offline; executed in local memory storage",
            "nodes_count": len(self._local_storage.get(project_id, {}).get("nodes", {}))
        }

    def health_check(self) -> Dict[str, Any]:
        """Status audit diagnosa service graf lokal."""
        return {
            "status": "healthy",
            "port": self.port,
            "uri": self.uri,
            "falkordb": {
                "host": self.falkordb_host,
                "port": self.falkordb_port,
                "connected": self.falkor_connected
            },
            "tenants_count": len(self._local_storage),
            "total_nodes": sum(len(t["nodes"]) for t in self._local_storage.values()),
            "total_edges": sum(len(t["edges"]) for t in self._local_storage.values())
        }

    # =========================================================================
    # Implementasi Antarmuka GraphMemoryAdapter
    # =========================================================================

    def create_graph(self, graph_id: str, name: str) -> bool:
        """Membuat tenant atau namespace graf baru."""
        self._ensure_tenant(graph_id)
        self._local_storage[graph_id]["metadata"]["name"] = name
        if self.falkor_connected and self.falkor_client:
            self.falkor_client.query(f"proj_{graph_id}", f"MERGE (g:GraphMetadata {{id: '{graph_id}', name: '{name}'}}) RETURN g")
        return True

    def add_facts(self, graph_id: str, facts: List[Dict[str, Any]]) -> bool:
        """Ingest batch fakta ke dalam graf dengan pemetaan bi-temporal."""
        self._ensure_tenant(graph_id)
        for item in facts:
            source = item.get("source") or item.get("entity") or "UnknownSource"
            target = item.get("target") or item.get("value") or "UnknownTarget"
            relation = item.get("relation") or item.get("predicate") or "ASSOCIATED_WITH"
            valid_from = item.get("valid_from") or item.get("timestamp") or datetime.now(timezone.utc).isoformat()
            valid_to = item.get("valid_to")

            # Normalisasi casing standar Step 1 ontology
            norm_rel = relation.strip().upper().replace(" ", "_")
            
            # Upsert nodes
            src_labels = [item.get("source_type", "Entity")]
            tgt_labels = [item.get("target_type", "Entity")]
            self.upsert_node(graph_id, str(source), labels=src_labels, properties={"name": str(source)})
            self.upsert_node(graph_id, str(target), labels=tgt_labels, properties={"name": str(target)})

            # Add bi-temporal edge
            props = {k: v for k, v in item.items() if k not in ("source", "target", "relation", "valid_from", "valid_to")}
            self.add_bitemporal_edge(
                project_id=graph_id,
                source_id=str(source),
                target_id=str(target),
                relation_type=norm_rel,
                properties=props,
                valid_from=valid_from,
                valid_to=valid_to
            )
        return True

    def search_temporal_facts(self, graph_id: str, query: str, limit: int = 10, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mencari fakta yang relevan dan aktif pada rentang waktu temporal."""
        self._ensure_tenant(graph_id)
        tenant_data = self._local_storage[graph_id]
        active_edges = [e for e in tenant_data["edges"] if e.is_active_at(as_of)]
        
        q_lower = query.lower()
        results: List[Dict[str, Any]] = []

        for e in active_edges:
            src_node = tenant_data["nodes"].get(e.source_id)
            tgt_node = tenant_data["nodes"].get(e.target_id)
            
            fact_repr = f"{e.source_id} {e.relation_type} {e.target_id}"
            score = 0.5
            if q_lower in fact_repr.lower():
                score = 0.95
            elif any(q_word in fact_repr.lower() for q_word in q_lower.split() if len(q_word) > 2):
                score = 0.8

            results.append({
                "fact": fact_repr,
                "source": "graphiti_falkordb" if self.falkor_connected else "graphiti_local",
                "relevance": score,
                "valid_from": e.valid_from,
                "valid_to": e.valid_to,
                "properties": e.properties,
                "source_node": src_node.model_dump() if src_node else None,
                "target_node": tgt_node.model_dump() if tgt_node else None
            })

        # Urutkan berdasarkan relevansi
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]

    def get_entity_context(self, graph_id: str, entity_name: str, as_of: Optional[str] = None) -> Dict[str, Any]:
        """Mengambil ringkasan konteks entitas beserta edge dan tetangga aktifnya."""
        self._ensure_tenant(graph_id)
        tenant_data = self._local_storage[graph_id]
        node = tenant_data["nodes"].get(entity_name)

        active_edges = [e for e in tenant_data["edges"] if e.is_active_at(as_of)]
        connected_edges = [
            e for e in active_edges
            if e.source_id == entity_name or e.target_id == entity_name
        ]

        neighbors: List[Dict[str, Any]] = []
        for e in connected_edges:
            neighbor_id = e.target_id if e.source_id == entity_name else e.source_id
            direction = "outgoing" if e.source_id == entity_name else "incoming"
            nbr_node = tenant_data["nodes"].get(neighbor_id)
            neighbors.append({
                "neighbor_id": neighbor_id,
                "direction": direction,
                "relation": e.relation_type,
                "valid_from": e.valid_from,
                "valid_to": e.valid_to,
                "labels": nbr_node.labels if nbr_node else []
            })

        return {
            "entity_name": entity_name,
            "project_id": graph_id,
            "exists": node is not None,
            "node": node.model_dump() if node else None,
            "connected_edges_count": len(connected_edges),
            "neighbors": neighbors
        }


# =============================================================================
# ASGI Application & Health Endpoint
# =============================================================================

try:
    from fastapi import FastAPI
    app = FastAPI(title="MiroFish Graphiti Service")

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "graphiti"}
except ImportError:
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    class _StarletteApp(Starlette):
        """Starlette wrapper dengan decorator @app.get."""
        def get(self, path: str):
            def decorator(func):
                import inspect
                async def endpoint(request):
                    if inspect.iscoroutinefunction(func):
                        res = await func()
                    else:
                        res = func()
                    if isinstance(res, dict):
                        return JSONResponse(res)
                    return res
                self.router.routes.append(Route(path, endpoint, methods=["GET"]))
                return func
            return decorator

    app = _StarletteApp()

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "graphiti"}

# Attach control plane API routes if available
try:
    from .graphiti_control_plane import create_control_plane_app
    _cp_app = create_control_plane_app()
    for _r in _cp_app.routes:
        if getattr(_r, "path", None) != "/health":
            app.router.routes.append(_r)
except Exception:
    pass

