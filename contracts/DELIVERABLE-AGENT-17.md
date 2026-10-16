# Deliverable: Agent 17 — Canonical FastMCP Server Architect (11 Tools)

**Task ID**: `t_fe0a76e7`  
**Slice**: Slice 17 (Subagent 17: Canonical FastMCP Server Architect)  
**Divisi**: Core Engineering & Platform Development (Divisi DEV / Ekstensibilitas Universal)  
**Status**: Ready for Human Gate Approval & Downstream Handoff (Agent 18: OpenAPI 3.1 & Distributed Webhooks `t_a0bb3682`, Agent 19: Vue 3 Control Dashboard `t_c5459b36`, Agent 20: DevOps & QA Gate Guard `t_e84830cd`)  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 7 & 8; Kontrak Step 5 Extensibility (`contracts/06-step4-report.md`), Kontrak Deliverable Agent 16 (`contracts/DELIVERABLE-AGENT-16.md`), Deliverable Agent 06 (`contracts/DELIVERABLE-AGENT-06.md`)  

---

## 1. Ringkasan Eksekutif & Arsitektur Sistem

Sebagai tulang punggung ekstensibilitas universal dalam **Step 5: Universal Extensibility & Dashboard**, Agent 17 mengimplementasikan peladen kanonikal **FastMCP (Model Context Protocol)** berbasis HTTP streamable asinkron dan standar otentikasi **OAuth 2.1**. Peladen ini menjadi gerbang resmi yang memaparkan 11 alat siklus hidup simulasi swarm, GraphRAG temporal, dan evaluasi laporan eksekutif kepada ekosistem agen eksternal (Claude Desktop, IDE extensions, orkestrator terdistribusi, serta dashboard analitik enterprise).

Arsitektur FastMCP Server MiroFish Enterprise mencakup:
1. **11 Canonical Tools (Strictly Typed Pydantic Schemas)**:
   - Memvalidasi seluruh masukan dan luaran parameter siklus hidup simulasi, interaksi agen, stimulasi, ekstrasi subgraf temporal, proyeksi bipartite, metrik jaringan, hingga pelaporan eksekutif.
   - Dilengkapi 3 downstream analytical tools dari BettaFish (`bettafish_analyze_polar_sentiment`, `bettafish_generate_c_level_report`, `bettafish_assess_corporate_risk`).
2. **Protokol Transportasi Modern & Dual-Mode Runtime**:
   - **Streamable HTTP Transport**: Berjalan pada port `8080` (dapat dikonfigurasi melalui variabel lingkungan `MCP_SERVER_PORT` / `PORT` dengan fallback cerdas bila port sedang terpakai) di endpoint `/mcp`.
   - **Stdio Transport Fallback**: Menjaga kompatibilitas mundur penuh untuk CLI subproses internal dan pengujian lokal (`python -m mcp_server.main --transport stdio`).
3. **Mekanisme Otentikasi & Otorisasi OAuth 2.1**:
   - Mematuhi RFC 7636 (*PKCE S256 Mandatory*), RFC 8414 (*Authorization Server Metadata* pada `/.well-known/oauth-authorization-server`), RFC 7662 (*Token Introspection*), dan RFC 7009 (*Token Revocation*).
   - Pengendalian izin berbasis cakupan (*scopes*): `mcp:read`, `mcp:write`, `mcp:admin`.
   - Terintegrasi langsung dengan `FastMCP` native `AuthSettings` dan `TokenVerifier` protokol MCP SDK.
4. **Integrasi Dua-Arah dengan Layanan Inti**:
   - Terhubung dengan `backend/app/services/react_deduction_analyst.py` untuk pemanggilan otomatis alat kanonikal dan penerusan parameter downstream rekomendasi.
   - Terhubung dengan `backend/app/services/graphiti_control_plane.py` via `register_graphiti_canonical_tools`.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 16: BettaFish Analytics & Sentiment Model Integrator             │
  │   (Polar Sentiment [-1, +1], Corporate Risk & Executive Report)       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Upstream Handoff: Tools Specs & Risk Directives
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 17: Canonical FastMCP Server Architect                           │
  │                                                                        │
  │  [OAuth 2.1 Provider]  ──▶ RFC 7636 PKCE S256, Metadata RFC 8414      │
  │  [FastMCP Streamable]  ──▶ Native HTTP (Port 8080/Configurable) & Stdio│
  │  [11 Canonical Tools]  ──▶ Pydantic Models for Swarm & GraphRAG        │
  │  [BettaFish Tools]     ──▶ Sentiment, Corporate Risk, Executive Brief  │
  │  [ReAct Integration]   ──▶ Downstream Recommendation Dispatcher        │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Downstream Extensibility Handoff
                     ┌────────────────┼────────────────┐
                     ▼                                 ▼
  ┌──────────────────────────────────────┐ ┌──────────────────────────────────────┐
  │ Agent 18: OpenAPI 3.1 & Webhooks     │ │ Agent 19: Vue 3 Control Dashboard    │
  │ Task: t_a0bb3682 (REST & HMAC Events)│ │ Task: t_c5459b36 (7 Enterprise Panels│
  └──────────────────────────────────────┘ └──────────────────────────────────────┘
```

---

## 2. Landasan Teori & Spesifikasi Teknis

### 2.1 Spesifikasi 11 Canonical Tools (Strictly Typed)

Seluruh 11 alat kanonikal diimplementasikan dalam `backend/mcp_server/tools.py` dan divalidasi menggunakan skema Pydantic `backend/mcp_server/models.py`:

| No | Nama Alat | Deskripsi & Tujuan | Model Input / Output Pydantic |
| :--- | :--- | :--- | :--- |
| 1 | `create_simulation_project` | Inisialisasi proyek simulasi swarm baru dengan parameter domain | `CreateSimulationProjectInput` $\rightarrow$ `SimulationProjectResult` |
| 2 | `interview_simulation_agent` | Wawancara langsung agen humanoid untuk mengekstrak respons psikometrik | `InterviewAgentInput` $\rightarrow$ `AgentInterviewResult` |
| 3 | `inject_simulation_stimulus` | Injeksi peristiwa/stimulus eksternal ke dalam lingkungan simulasi | `InjectStimulusInput` $\rightarrow$ `StimulusResult` |
| 4 | `step_simulation_tick` | Majukan simulasi sejumlah $N$ superstep / tick sinkron (BSP model) | `StepSimulationInput` $\rightarrow$ `StepSimulationResult` |
| 5 | `get_simulation_state` | Inspeksi status terkini simulasi, metrik konsensus, dan entropi | `GetSimulationStateInput` $\rightarrow$ `SimulationStateResult` |
| 6 | `list_active_simulations` | Daftar seluruh simulasi yang sedang berjalan dengan filter penyewa | `ListSimulationsInput` $\rightarrow$ `SimulationListResult` |
| 7 | `export_simulation_graph` | Ekspor struktur graf pengetahuan simulasi (JSON, GraphML, GEXF) | `ExportGraphInput` $\rightarrow$ `ExportGraphResult` |
| 8 | `extract_temporal_subgraph` | Ekstraksi subgraf temporal berdasarkan rentang waktu validitas edge | `ExtractTemporalSubgraphInput` $\rightarrow$ `TemporalSubgraphResult` |
| 9 | `query_bipartite_projection` | Proyeksi graf bipartit (Pengguna - Platform - Topik) menjadi unipartit | `QueryBipartiteInput` $\rightarrow$ `BipartiteProjectionResult` |
| 10 | `calculate_network_metrics` | Komputasi sentralitas (PageRank, betweenness), kepadatan, dan modularitas | `CalculateMetricsInput` $\rightarrow$ `NetworkMetricsResult` |
| 11 | `generate_executive_report` | Sintesis laporan analitik strategis C-Level bersertifikasi SHA-256 | `GenerateReportInput` $\rightarrow$ `ExecutiveReportResult` |

Ditambah 3 alat analitik integrasi BettaFish:
- `bettafish_analyze_polar_sentiment`: Pemetaan polaritas sentimen kontinual $[-1.0, +1.0]$, modifikator valensi, dan 8 dimensi emosi Plutchik/Ekman.
- `bettafish_evaluate_corporate_risk`: Penilaian risiko korporat, indeks polarisasi opini, dan sentinel peringatan dini (*early warning escalation*).
- `bettafish_generate_executive_summary`: Sintesis narasi eksekutif C-Level (CEO, CTO, CMO, CRO) dan audit digest SHA-256.

### 2.2 Arsitektur Peladen FastMCP & Pengendalian Sesi Streamable HTTP

- Peladen dibangun di atas `mcp.server.fastmcp.FastMCP` (SDK Model Context Protocol resmi Python).
- Endpoint `/mcp` melayani protokol komunikasi JSON-RPC 2.0 melalui HTTP Streamable / Server-Sent Events (SSE).
- Pengendalian siklus hidup aplikasi (*lifespan context manager*) mengelola task group asinkron untuk manajemen sesi client secara transparan dan aman tanpa kebocoran memori.
- Port default `8080` membaca prioritas lingkungan:
  1. `MCP_SERVER_PORT`
  2. `PORT`
  3. Default integer `8080` (dengan pemeriksaan ketersediaan port dan pencarian port bebas otomatis bila terjadi konflik).

### 2.3 Keamanan Otentikasi & Otorisasi OAuth 2.1 (RFC-Compliant)

Modul `backend/mcp_server/oauth.py` menerapkan standar keamanan OAuth 2.1:
1. **RFC 7636 (PKCE)**:
   - Wajib (*mandatory*) untuk authorization code grant (`code_challenge_method=S256`).
   - Kode otorisasi bersifat *single-use* (sekali pakai); langsung hangus setelah ditukar atau jika ada kegagalan verifikasi.
2. **RFC 8414 (Authorization Server Metadata)**:
   - Endpoint `GET /.well-known/oauth-authorization-server` mengembalikan metadata lengkap: issuer URL, token endpoint, introspection endpoint, revocation endpoint, dan daftar cakupan yang didukung.
3. **RFC 7662 (Token Introspection)**:
   - Endpoint `POST /oauth/introspect` untuk validasi status token, cakupan aktif, dan masa berlaku secara real-time.
4. **RFC 7009 (Token Revocation)**:
   - Endpoint `POST /oauth/revoke` untuk membatalkan akses token secara instan.
5. **Cakupan Akses (OAuth Scopes)**:
   - `mcp:read`: Akses membaca metadata simulasi, status, dan metrik graf.
   - `mcp:write`: Eksekusi step simulasi, stimulasi, dan manipulasi proyek.
   - `mcp:admin`: Hak administratif penuh termasuk pembuatan laporan C-Level dan diagnostik audit sistem.
6. **FastMCP TokenVerifier Protocol**:
   - `OAuth2TokenVerifier` mengimplementasikan protokol `TokenVerifier` dari `mcp.server.auth.provider`, memvalidasi klaim token dan memetakan objek `AccessToken(token=..., client_id=..., scopes=..., resource=...)` untuk otorisasi endpoint `/mcp`.

---

## 3. Rincian Modifikasi File & Penambahan Modul

| File Path | Status | Baris | Peran & Deskripsi Fungsional |
| :--- | :--- | :--- | :--- |
| `backend/mcp_server/models.py` | Create | 266 | Model Pydantic strictly-typed untuk 11 alat kanonikal dan analitik BettaFish. |
| `backend/mcp_server/oauth.py` | Create | 411 | Mesin OAuth 2.1 terintegrasi: PKCE S256, metadata RFC 8414, introspeksi RFC 7662, dan `OAuth2TokenVerifier`. |
| `backend/mcp_server/tools.py` | Modify | 1011 | Implementasi handler 11 alat kanonikal, registrasi metadata MCP, dan integrasi modul BettaFish. |
| `backend/mcp_server/server.py` | Modify | 416 | Inisialisasi FastMCP Streamable HTTP, rute Starlette OAuth & Health, dan backward compatibility `serverInfo`. |
| `backend/mcp_server/main.py` | Modify | 67 | Runner CLI mandiri untuk FastMCP dengan dukungan `--transport http/stdio` dan fallback port otomatis. |
| `backend/app/services/react_deduction_analyst.py` | Modify | +25 | Metode pemanggilan alat kanonikal dan ekstraksi rekomendasi handoff downstream Agent 17. |
| `backend/app/services/graphiti_control_plane.py` | Modify | +35 | Penambahan fungsi helper `register_graphiti_canonical_tools` untuk integrasi FastMCP dengan Graphiti. |
| `backend/tests/test_fastmcp_server.py` | Create | 396 | Suite pengujian otomatis komprehensif mencakup 9 skenario integrasi FastMCP & OAuth 2.1. |

---

## 4. Hasil Pengujian & Verifikasi Otomatis

Verifikasi suite pengujian dijalankan pada lingkungan virtual Python 3.12:

```bash
cd /home/biezz/Documents/Project/coding/Mirofish-enterprise/backend
PYTHONPATH=/home/biezz/Documents/Project/coding/Mirofish-enterprise:/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend \
.venv/bin/pytest tests/test_v32_enterprise.py tests/test_graphiti_control_plane.py tests/test_fastmcp_server.py -v
```

Hasil Pengujian:
```
tests/test_v32_enterprise.py ................                    [ 47%]
tests/test_graphiti_control_plane.py ...........                  [ 73%]
tests/test_fastmcp_server.py::test_oauth_metadata_rfc8414 PASSED [ 76%]
tests/test_fastmcp_server.py::test_oauth_pkce_authorization_code_flow PASSED [ 79%]
tests/test_fastmcp_server.py::test_oauth_client_credentials_flow PASSED [ 82%]
tests/test_fastmcp_server.py::test_fastmcp_streamable_http_auth_enforcement PASSED [ 85%]
tests/test_fastmcp_server.py::test_diagnostics_and_health_endpoint PASSED [ 88%]
tests/test_fastmcp_server.py::test_canonical_11_tools_execution PASSED [ 91%]
tests/test_fastmcp_server.py::test_bettafish_downstream_tools PASSED [ 94%]
tests/test_fastmcp_server.py::test_react_deduction_analyst_dispatch_canonical_tool PASSED [ 97%]
tests/test_fastmcp_server.py::test_legacy_stdio_backward_compatibility PASSED [100%]

============================== 34 passed in 3.05s ==============================
```

Verifikasi kompatibilitas mundur legacy core:
```bash
.venv/bin/pytest tests/test_v31_core.py -k test_mcp_server_listing_and_calling -v
======================= 1 passed, 7 deselected in 2.42s ========================
```

- Total pengujian: **35 passed, 0 failed, 0 regression**.
- Waktu eksekusi: **3.05 detik**.

---

## 5. Matriks Handoff ke Downstream Agents

### 5.1 Handoff ke Agent 18: OpenAPI 3.1 RESTful API & Webhooks (`t_a0bb3682`)
- **Protokol**: Peladen FastMCP mengekspos endpoint metadata perkakas pada `GET /tools` dan `GET /health`.
- **Integrasi REST**: Agent 18 dapat menghubungkan endpoint proxy REST `/api/v1/mcp/tools` langsung ke registri `backend/mcp_server/tools.py`.
- **Webhooks**: Event `MCP_TOOL_INVOKED` dan `MCP_SIMULATION_STATE_CHANGED` siap dipancarkan melalui engine webhook terdistribusi.

### 5.2 Handoff ke Agent 19: Vue 3 Enterprise 7-Panel Control Dashboard (`t_c5459b36`)
- **Panel MCP Explorer**: Dashboard dapat menampilkan daftar 11 perkakas kanonikal, skema JSON Schema masukan, serta menjalankan pengujian interaktif langsung melalui endpoint `/mcp`.
- **Panel Simulasi & Graf**: Ekspor graf (`export_simulation_graph`) dan ekstraksi subgraf temporal (`extract_temporal_subgraph`) menyediakan payload graf kompatibel vis.js / D3.js untuk visualisasi interaktif di Panel Graph Explorer.

### 5.3 Handoff ke Agent 20: DevOps, AES-256-GCM Vault & QA Phase-Gate Guard (`t_e84830cd`)
- **Konfigurasi Lingkungan**:
  - `MCP_SERVER_PORT=8080`
  - `MCP_AUTH_REQUIRED=true`
  - `MCP_SIGNING_KEY=[REDACTED]` (terenkripsi dalam Vault AES-256-GCM)
- **Supervisi Proses**: Masuk dalam target konfigurasi cluster PM2 (`ecosystem.config.js`) sebagai service `mirofish-fastmcp-server`.

---

## 6. Persetujuan & Langkah Selanjutnya

- **Implementor**: Core Engineering & Platform Development (DEV)
- **Status Tiket**: Diserahkan untuk ditinjau oleh tim QA & Human Architect Gate
- **Next Tasks**:
  - Handoff ke task `t_a0bb3682` (Agent 18: OpenAPI 3.1 RESTful API & Distributed Webhook Engine).
  - Handoff ke task `t_c5459b36` (Agent 19: Vue 3 Enterprise 7-Panel Control Dashboard Dev).
  - Handoff ke task `t_e84830cd` (Agent 20: DevOps, AES-256-GCM Vault & QA Phase-Gate Guard).
