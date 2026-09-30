"""
Definisi Alat-Alat Operasional MCP MiroFish
"""
from typing import List, Dict, Any

def register_mcp_tools() -> List[Dict[str, Any]]:
    """Mendaftarkan definisi skema perkakas MCP MiroFish."""
    return [
        {
            "name": "list_projects",
            "description": "Mendapatkan daftar proyek simulasi MiroFish",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Batas jumlah proyek", "default": 20}
                }
            }
        },
        {
            "name": "get_job_status",
            "description": "Mengambil status progres pekerjaan simulasi dan checkpoint ronde",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "ID pekerjaan simulasi"}
                },
                "required": ["job_id"]
            }
        },
        {
            "name": "get_simulation_report",
            "description": "Mengambil laporan prediksi sentimen dan dinamika opini publik",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID proyek MiroFish"}
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "search_knowledge_graph",
            "description": "Mencari fakta temporal pada graf pengetahuan memori agen",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID proyek"},
                    "query": {"type": "string", "description": "Kata kunci pencarian"}
                },
                "required": ["project_id", "query"]
            }
        },
        {
            "name": "run_web_research",
            "description": "Menjalankan riset web Langkah 0 via SearXNG privat tanpa pelacakan",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topik riset"},
                    "research_type": {"type": "string", "enum": ["general", "news", "images"], "default": "general"},
                    "max_results": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        }
    ]
