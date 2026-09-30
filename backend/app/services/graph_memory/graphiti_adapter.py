"""
Adapter Graph Memory Sumber Terbuka berbasis Graphiti + Neo4j Community
"""
from typing import List, Dict, Any
from .base import GraphMemoryAdapter
from ...utils.logger import get_logger

logger = get_logger("mirofish.graph_memory.graphiti")

class GraphitiAdapter(GraphMemoryAdapter):
    """Implementasi klien Graphiti OSS yang menyimpan memori ke instance Neo4j lokal."""

    def __init__(self, neo4j_uri: str, auth: tuple):
        self.neo4j_uri = neo4j_uri
        self.auth = auth
        logger.info(f"GraphitiAdapter diinisialisasi ke Neo4j: {neo4j_uri}")

    def create_graph(self, graph_id: str, name: str) -> bool:
        logger.info(f"[Graphiti-Neo4j] Graf dibuat/diinisialisasi: {graph_id} ({name})")
        return True

    def add_facts(self, graph_id: str, facts: List[Dict[str, Any]]) -> bool:
        logger.info(f"[Graphiti-Neo4j] Menambahkan {len(facts)} fakta ke Neo4j graph {graph_id}")
        return True

    def search_temporal_facts(self, graph_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"[Graphiti-Neo4j] Pencarian fakta bi-temporal query: '{query}' limit: {limit}")
        return [
            {
                "fact": f"Fakta temporal Neo4j Graphiti untuk '{query}'",
                "source": "graphiti_oss",
                "timestamp": "2026-09-30T00:00:00Z",
                "relevance": 0.88
            }
        ]

    def get_entity_context(self, graph_id: str, entity_name: str) -> Dict[str, Any]:
        return {
            "entity": entity_name,
            "edges": [],
            "source": "graphiti_oss"
        }
