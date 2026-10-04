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

    backend_type = getattr(Config, "GRAPH_BACKEND", "graphiti").lower()
    if backend_type in ("graphiti", "graphiti_platform", "graphiti_falkordb"):
        control_plane_url = getattr(Config, "GRAPHITI_CONTROL_PLANE_URL", "http://127.0.0.1:8080")
        falkordb_host = getattr(Config, "FALKORDB_HOST", "127.0.0.1")
        falkordb_port = int(getattr(Config, "FALKORDB_PORT", 6379))
        _adapter_instance = GraphitiAdapter(
            control_plane_url=control_plane_url,
            falkordb_host=falkordb_host,
            falkordb_port=falkordb_port
        )
    else:
        api_key = getattr(Config, "ZEP_API_KEY", "") or "default_zep_key"
        _adapter_instance = ZepAdapter(api_key=api_key)

    return _adapter_instance
