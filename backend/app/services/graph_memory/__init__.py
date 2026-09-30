"""
Pabrik Adapter Graph Memory MiroFish
"""
from typing import Optional
from .base import GraphMemoryAdapter
from .zep_adapter import ZepAdapter
from .graphiti_adapter import GraphitiAdapter
from ...config import Config

_adapter_instance: Optional[GraphMemoryAdapter] = None

def get_graph_adapter() -> GraphMemoryAdapter:
    """Mengembalikan adapter graph aktif berdasarkan konfigurasi backend."""
    global _adapter_instance
    if _adapter_instance is not None:
        return _adapter_instance

    backend_type = getattr(Config, "GRAPH_BACKEND", "zep").lower()
    if backend_type == "graphiti_neo4j":
        neo4j_uri = getattr(Config, "NEO4J_URI", "bolt://127.0.0.1:7687")
        user = getattr(Config, "NEO4J_USER", "neo4j")
        password = getattr(Config, "NEO4J_PASSWORD", "mirofish_secret")
        _adapter_instance = GraphitiAdapter(neo4j_uri=neo4j_uri, auth=(user, password))
    else:
        api_key = getattr(Config, "ZEP_API_KEY", "") or "default_zep_key"
        _adapter_instance = ZepAdapter(api_key=api_key)

    return _adapter_instance
