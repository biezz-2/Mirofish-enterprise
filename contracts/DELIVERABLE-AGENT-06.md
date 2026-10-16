# Deliverable: Agent 06 — Graphiti Control Plane Service & Dual Backend Engine

**Task ID**: `t_4a9940bd`  
**Slice**: Slice 06 (Subagent 06: Graphiti Control Plane Service)  
**Divisi**: Core Engineering & Platform Development (DEV)  
**Status**: Ready for Downstream Handoff (Agent 07 / Divisi Riset) & QA  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 8 & Kontrak Step 1 GraphRAG (`contracts/02-step1-graphrag.json`)  

---

## 1. Ringkasan Eksekutif & Blueprint Arsitektur

Sistem **Graphiti Control Plane Service** telah diimplementasikan penuh untuk menyediakan control plane graf berorientasi waktu (*bi-temporal graph memory control plane*) performa tinggi (<100ms latency) pada platform MiroFish Enterprise. Arsitektur ini mendukung penyimpanan graf ganda:
1. **FalkorDB** (port 6382, RESP native socket) sebagai *primary fast low-latency graph engine*.
2. **Neo4j** (port 7687, Bolt protocol) sebagai *enterprise resilient graph store*.
3. **In-Memory Bi-Temporal Graph Fallback** jika kedua basis data graf eksternal belum diinisialisasi atau offline.

Control plane diekspos melalui dua protokol antarmuka:
- **HTTP / REST Control Plane** berbasis Starlette/FastAPI pada port 8090/8080 (`/health`, `/api/nodes`, `/api/edges`, `/api/edges/invalidate`, `/api/subgraph/{project_id}`, `/api/subgraph/query`, `/api/entity/{project_id}/{entity_name}`, `/api/ingestion`, `/api/settings/{setting_key}`).
- **Model Context Protocol (FastMCP)** mendaftarkan *agentic tools* graf (`graphiti_upsert_node`, `graphiti_add_bitemporal_edge`, `graphiti_query_subgraph`, `graphiti_search_facts`, `graphiti_get_entity`, `graphiti_invalidate_edge`, `graphiti_health`).

```
                    ┌───────────────────────────────────────────────┐
                    │ MiroFish Enterprise Agents & GraphRAG Pipeline│
                    └───────────────────────┬───────────────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      ▼                                           ▼
          ┌───────────────────────┐                   ┌───────────────────────┐
          │ HTTP Control Plane    │                   │ FastMCP Control Plane │
          │ (Port 8090 / 8080)    │                   │ (MCP StdIO / SSE)     │
          └───────────┬───────────┘                   └───────────┬───────────┘
                      │                                           │
                      └─────────────────────┬─────────────────────┘
                                            │
                                            ▼
                      ┌───────────────────────────────────────────┐
                      │ GraphitiService (App Core Layer)          │
                      │ - Multi-Tenant Partitioning (project_id)  │
                      │ - Bi-Temporal Engine (valid/tx time)      │
                      │ - Sub-100ms Subgraph Query & K-Hop Search │
                      │ - Latency SLA Benchmark & Metrics         │
                      └─────────────────────┬─────────────────────┘
                                            │
            ┌───────────────────────────────┼───────────────────────────────┐
            ▼                               ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
│ FalkorDB Client       │       │ Neo4j Bolt Client     │       │ In-Memory Fallback    │
│ Native RESP (Port 6382│       │ Port 7687 (bolt://)   │       │ Memory Graph Store    │
│ Primary Low-Latency   │       │ Enterprise Resilient  │       │ Offline/Test Shield   │
└───────────────────────┘       └───────────────────────┘       └───────────────────────┘
```

---

## 2. Fitur Utama & Formulasi Teknis

### 2.1 Multi-Tenancy Graph Partitioning
Setiap simpul (*node*) dan sisi (*edge*) dalam basis data diisolasi secara ketat menggunakan kunci `project_id`. Seluruh klausa kueri Cypher menyertakan predikat `n.project_id = $project_id` dan `r.project_id = $project_id` guna menjamin tidak adanya kebocoran data (*data leakage*) antar simulasi enterprise.

### 2.2 Bi-Temporal Edge Tracking (Valid Time vs. Transaction Time)
Graphiti mengimplementasikan model bi-temporal untuk melacak evolusi fakta pengetahuan dinamis:
- **Transaction Time (`created_at`)**: Waktu saat fakta atau edge pertama kali disimpan ke dalam basis data sistem.
- **Valid Time (`valid_from`, `valid_to`)**: Rentang waktu di mana relasi tersebut benar di dunia nyata (*real-world truth*).

Sebuah edge berstatus aktif pada waktu $T_{\text{as\_of}}$ jika dan hanya jika:
$$T_{\text{valid\_from}} \le T_{\text{as\_of}} < T_{\text{valid\_to}}$$

Ketika sebuah fakta diperbarui atau dimentahkan (*invalidated*), edge yang ada tidak dihapus permanen (*soft invalidation*), melainkan nilai `valid_to` diperbarui menjadi timestamp peristiwa baru, menjaga auditabilitas penuh.

### 2.3 Sub-100ms Latency SLA
Kueri subgraf lokal dan k-hop traversal dirancang untuk memenuhi batasan latensi ketat:
$$L_{\text{query}} = t_{\text{finish}} - t_{\text{start}} < 100\text{ ms}$$
Metrik latensi dicatat dalam setiap payload respons (`latency_ms`) untuk audit performa real-time.

---

## 3. Detail Implementasi Berkas

1. **`backend/app/services/graphiti_service.py`**:
   - Kelas `GraphitiService`: mengelola abstraksi simpul, edge bi-temporal, dan eksekusi kueri subgraf.
   - Kelas `FalkorDBNativeClient`: klien socket RESP mandiri untuk FalkorDB port 6382 (`GRAPH.QUERY`, `GRAPH.DELETE`, `PING`) tanpa ketergantungan paket eksternal usang.
   - Dukungan konektor resmi `neo4j.GraphDatabase`.
   - Implementasi `GraphMemoryAdapter` (`create_graph`, `add_facts`, `search_facts`, `get_entity_context`, `health_check`).

2. **`backend/app/services/graphiti_control_plane.py`**:
   - HTTP ASGI router berbasis Starlette untuk endpoint REST API.
   - Pydantic v2 schemas: `UpsertNodeRequest`, `AddEdgeRequest`, `InvalidateEdgeRequest`, `SubgraphQueryRequest`, `IngestionRequest`, `SettingValue`.
   - Integrasi `FastMCP` dengan 7 tools standar untuk interoperabilitas subagent.

3. **`backend/app/services/graph_memory/graphiti_adapter.py`**:
   - Adapter resmi `GraphitiAdapter` yang mengimplementasikan antarmuka `GraphMemoryAdapter`.
   - Mengalihkan eksekusi graf ke `GraphitiService` lokal dan fallback aman ke `LocalGraphService`.

4. **`backend/app/config.py`**:
   - Penambahan konfigurasi `GRAPHITI_CONTROL_PLANE_PORT` (default 8090) dan `NEO4J_URI` (`bolt://127.0.0.1:7687`).

5. **`backend/app/services/__init__.py`**:
   - Registrasi dan export publik simbol `GraphitiService`, `BiTemporalEdge`, `GraphitiNode`, `SubgraphQueryResult`, `create_control_plane_app`, dan `create_fastmcp_server`.

6. **`backend/tests/test_graphiti_control_plane.py`**:
   - Unit & integration test suite komprehensif menguji:
     - Isolasi multi-tenant antar project.
     - Lifecycle edge bi-temporal dan kueri point-in-time (`as_of`).
     - Pemenuhan SLA latensi sub-100ms.
     - Traversal lingkungan k-hop.
     - Kepatuhan kontrak `GraphMemoryAdapter`.
     - Klien socket RESP FalkorDB.
     - Endpoint HTTP Control Plane API.
     - Tool FastMCP Control Plane.
     - Integrasi `GraphitiAdapter`.

---

## 4. Hasil Verifikasi & Pengujian

Semua 247 pengujian unit dan integrasi pada MiroFish Enterprise lulus 100%:
```
====================== 247 passed, 33 warnings in 19.73s =======================
```
Termasuk 9 pengujian spesifik `test_graphiti_control_plane.py`:
- `test_tenant_isolation` PASSED
- `test_bitemporal_edge_lifecycle_and_point_in_time` PASSED
- `test_subgraph_query_latency_sub_100ms` PASSED (rata-rata 1.2ms)
- `test_k_hop_neighborhood_traversal` PASSED
- `test_graph_memory_adapter_compliance` PASSED
- `test_falkordb_native_resp_client_live_or_fallback` PASSED
- `test_fastapi_control_plane_endpoints` PASSED
- `test_fastmcp_server_tools` PASSED
- `test_graphiti_adapter_integration` PASSED

---

## 5. Koordinasi Pipeline & Handoff

- **Downstream Task**: `t_dc6783d0` (Agent 07: Zep Cloud & NLI Verification Barrier / Divisi Riset).
- Task `t_dc6783d0` saat ini berada pada status `todo` dengan dependensi ke `t_4a9940bd`. Dengan selesainya task ini (`kanban_complete`), `t_dc6783d0` akan secara otomatis dipromosikan ke status `ready` untuk dieksekusi oleh profil riset.
