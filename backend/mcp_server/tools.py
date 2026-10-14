"""
Definisi Alat-Alat Operasional MCP MiroFish (Protokol 2024-11-05)
"""
from typing import List, Dict, Any

def register_mcp_tools() -> List[Dict[str, Any]]:
    """Mendaftarkan definisi skema perkakas MCP MiroFish terstandarisasi."""
    tools = [
        {
            "name": "list_projects",
            "description": "Mendapatkan daftar proyek simulasi MiroFish dari backend atau cache",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Batas jumlah proyek", "default": 20}
                }
            }
        },
        {
            "name": "get_job_status",
            "description": "Mengambil status progres pekerjaan simulasi dan checkpoint ronde",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "ID pekerjaan atau ID simulasi"}
                },
                "required": ["job_id"]
            }
        },
        {
            "name": "get_simulation_report",
            "description": "Mengambil laporan prediksi sentimen dan dinamika opini publik berdasarkan project_id atau simulation_id",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID proyek MiroFish (opsional)"},
                    "simulation_id": {"type": "string", "description": "ID simulasi MiroFish (opsional)"}
                }
            }
        },
        {
            "name": "search_knowledge_graph",
            "description": "Mencari fakta temporal dan relasi entitas pada graf pengetahuan memori agen",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID proyek atau graf"},
                    "query": {"type": "string", "description": "Kata kunci pencarian fakta/entitas"}
                },
                "required": ["project_id", "query"]
            }
        },
        {
            "name": "run_web_research",
            "description": "Menjalankan riset web privat Langkah 0 via SearXNG MiroFish tanpa pelacakan",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topik atau kueri riset"},
                    "research_type": {"type": "string", "enum": ["general", "news", "images"], "default": "general"},
                    "max_results": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        },
        {
            "name": "create_simulation_job",
            "description": "Membuat konfigurasi dan pekerjaan simulasi baru untuk suatu proyek",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID proyek MiroFish"},
                    "graph_id": {"type": "string", "description": "ID graf pengetahuan (opsional)"},
                    "enable_twitter": {"type": "boolean", "default": True, "description": "Aktifkan platform Twitter/X"},
                    "enable_reddit": {"type": "boolean", "default": True, "description": "Aktifkan platform Reddit"}
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "start_simulation",
            "description": "Memulai atau melanjutkan jalannya simulasi OASIS multi-platform",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "simulation_id": {"type": "string", "description": "ID simulasi MiroFish"},
                    "platform": {"type": "string", "description": "Platform simulasi (parallel, twitter, reddit)", "default": "parallel"},
                    "max_rounds": {"type": "integer", "description": "Batas ronde simulasi", "default": 50},
                    "force": {"type": "boolean", "description": "Paksa restart simulasi dari awal", "default": False}
                },
                "required": ["simulation_id"]
            }
        },
        {
            "name": "stop_simulation",
            "description": "Menghentikan simulasi yang sedang berjalan",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "simulation_id": {"type": "string", "description": "ID simulasi MiroFish"}
                },
                "required": ["simulation_id"]
            }
        }
    ]
    # Dukungan kompatibilitas ganda untuk parameters & inputSchema
    for tool in tools:
        tool["parameters"] = tool["inputSchema"]
    return tools
