"""
Antarmuka Dasar Adapter Graph Memory (Temporal Knowledge Graph)
Memisahkan dependensi Zep Cloud dan Graphiti + Neo4j Community
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class GraphMemoryAdapter(ABC):
    """Antarmuka tunggal penyimpanan graf pengetahuan temporal."""

    @abstractmethod
    def create_graph(self, graph_id: str, name: str) -> bool:
        """Membuat graf atau sesi memori baru."""
        pass

    @abstractmethod
    def add_facts(self, graph_id: str, facts: List[Dict[str, Any]]) -> bool:
        """Menambahkan simpul fakta ke graf."""
        pass

    @abstractmethod
    def search_temporal_facts(self, graph_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Kueri fakta temporal berdasarkan relevansi semantik dan waktu."""
        pass

    @abstractmethod
    def get_entity_context(self, graph_id: str, entity_name: str) -> Dict[str, Any]:
        """Mengambil tetangga relasi simpul entitas pada graf."""
        pass
