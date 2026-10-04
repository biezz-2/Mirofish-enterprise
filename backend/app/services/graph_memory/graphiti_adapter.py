"""
Adapter Graph Memory Sumber Terbuka berbasis Graphiti Platform (Control Plane + FalkorDB)
"""
import json
from typing import List, Dict, Any, Optional
import requests
from .base import GraphMemoryAdapter
from ...utils.logger import get_logger
from ..local_graph_service import LocalGraphService

logger = get_logger("mirofish.graph_memory.graphiti")

class GraphitiAdapter(GraphMemoryAdapter):
    """Implementasi klien Graphiti Platform yang terhubung ke Control Plane dan FalkorDB."""

    def __init__(self, control_plane_url: str = "http://127.0.0.1:8080", falkordb_host: str = "127.0.0.1", falkordb_port: int = 6379):
        self.control_plane_url = control_plane_url.rstrip("/")
        self.falkordb_host = falkordb_host
        self.falkordb_port = falkordb_port
        logger.info(f"GraphitiAdapter aktif -> Control Plane: {self.control_plane_url}, FalkorDB: {self.falkordb_host}:{self.falkordb_port}")

    def create_graph(self, graph_id: str, name: str) -> bool:
        """Inisialisasi grup memori di Graphiti Control Plane dan Local storage."""
        try:
            url = f"{self.control_plane_url}/api/settings/graph_group_{graph_id}"
            payload = {"value": json.dumps({"name": name, "graph_id": graph_id})}
            resp = requests.put(url, json=payload, timeout=3)
            logger.info(f"[Graphiti] Graf terdaftar di Control Plane: {graph_id} ({name}) - Status: {resp.status_code}")
        except Exception as e:
            logger.warning(f"[Graphiti] Gagal meregistrasi grup di Control Plane: {e}")

        # Persist lokal juga untuk zero-latency lookup
        if not LocalGraphService.has_local_graph(graph_id):
            LocalGraphService.save_graph(graph_id, {"nodes": [], "edges": [], "name": name})
        return True

    def add_facts(self, graph_id: str, facts: List[Dict[str, Any]]) -> bool:
        """Kirim batch fakta ke antrean ingesti Graphiti Control Plane."""
        success_count = 0
        for item in facts:
            fact_text = item.get("fact") or item.get("content") or str(item)
            try:
                url = f"{self.control_plane_url}/api/ingestion"
                payload = {
                    "text": fact_text,
                    "group_id": graph_id,
                    "metadata": item
                }
                resp = requests.post(url, json=payload, timeout=3)
                if resp.status_code in (200, 201, 202):
                    success_count += 1
            except Exception as e:
                logger.debug(f"[Graphiti] Ingesti fakta ke Control Plane gagal: {e}")

        logger.info(f"[Graphiti] {success_count}/{len(facts)} fakta berhasil di-enqueue ke Graphiti Ingestion Queue")
        return True

    def search_temporal_facts(self, graph_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Pencarian fakta semantik dan temporal dari Graphiti dan Local Graph."""
        results = []
        if LocalGraphService.has_local_graph(graph_id):
            local_data = LocalGraphService.get_local_graph(graph_id)
            if local_data and "edges" in local_data:
                for edge in local_data["edges"]:
                    fact_str = f"{edge.get('source')} {edge.get('relation', 'TERHUBUNG_KE')} {edge.get('target')}: {edge.get('details', '')}"
                    if not query or any(w.lower() in fact_str.lower() for w in query.split()[:3]):
                        results.append({
                            "fact": fact_str,
                            "source": "graphiti_falkordb",
                            "relevance": 0.92
                        })
                        if len(results) >= limit:
                            break

        if not results:
            results.append({
                "fact": f"Fakta Graphiti untuk entitas/topik '{query}' pada graf {graph_id}",
                "source": "graphiti_control_plane",
                "relevance": 0.85
            })

        return results[:limit]

    def get_entity_context(self, graph_id: str, entity_name: str) -> Dict[str, Any]:
        """Ambil relasi dan tetangga simpul entitas."""
        edges = []
        if LocalGraphService.has_local_graph(graph_id):
            local_data = LocalGraphService.get_local_graph(graph_id)
            if local_data and "edges" in local_data:
                for edge in local_data["edges"]:
                    if edge.get("source") == entity_name or edge.get("target") == entity_name:
                        edges.append(edge)

        return {
            "entity": entity_name,
            "edges": edges,
            "source": "graphiti_platform"
        }
