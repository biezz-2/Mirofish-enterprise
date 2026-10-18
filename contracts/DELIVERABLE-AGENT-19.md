# Deliverable: Agent 19 — Single Pane of Glass 7-Panel Enterprise Vue 3 Dashboard

**Task ID**: `t_c5459b36`  
**Slice**: Slice 19 (Subagent 19: Vue 3 Enterprise Dashboard with 7-Panel Control Center, RecSys Calibration Matrix, D3 Force GraphRAG Explorer, Swarm Telemetry, Webhook/DLQ Management, FastMCP Sandbox, and Cryptographic Security Audit)  
**Divisi**: Core Engineering & Platform Development (Divisi DEV / Ekstensibilitas Universal & Antarmuka Platform)  
**Status**: Ready for Human Gate Approval & Downstream Handoff (Agent 20: DevOps, Production Hardening & QA Gate Guard `t_e84830cd`)  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 7 & 8; Kontrak Step 5 Extensibility (`contracts/06-step4-report.md`), Kontrak Deliverable Agent 18 (`contracts/DELIVERABLE-AGENT-18.md`), Kontrak Deliverable Agent 17 (`contracts/DELIVERABLE-AGENT-17.md`), Kontrak Deliverable Agent 16 (`contracts/DELIVERABLE-AGENT-16.md`)  

---

## 1. Ringkasan Eksekutif & Arsitektur Single Pane of Glass

Sebagai puncak antarmuka operasional enterprise platform dalam **Step 5: Universal Extensibility & Dashboard**, Agent 19 mengimplementasikan antarmuka terpadu **Single Pane of Glass (SPOG)** berbasis Vue 3 Composition API, Vite, Tailwind CSS, Vue Router, Vue I18n, dan D3.js v7. Dashboard enterprise ini menyatukan 7 pilar observabilitas, intervensi, orkestrasi, dan tata kelola keamanan MiroFish Enterprise ke dalam satu konsol operasional terpadu yang responsif, berlatar belakang gelap bertema enterprise (*cyber-slate dark theme*), dan berkemampuan trilingual penuh (*English*, *Bahasa Indonesia*, *Mandarin/中文*).

Arsitektur 7-Panel Single Pane of Glass MiroFish Enterprise mencakup:
1. **Panel 1 — RecSys Algorithm Calibration Matrix & Pareto Frontier Simulation**:
   - Visualisasi parameter bobot algoritma rekomendasi multi-platform (TikTok, X / Twitter, Instagram, Reddit, YouTube, Threads, LinkedIn).
   - Pengaturan interaktif koefisien polarisasi, virality bias, content diversity, dan echo chamber damping.
   - Radar diagram SVG multi-sumbu dinamis dan kalkulator *Pareto-optimal efficiency frontier* ($\alpha = 1.25, \varepsilon = 0.05$) untuk menguji trade-off keterlibatan vs. polarisasi opini sebelum simulasi dieksekusi.
2. **Panel 2 — Knowledge Graph & GraphRAG Explorer (D3.js Force-Directed Dual Engine)**:
   - Visualisasi graf relasional pengetahuan entitas interaktif berkemampuan zoom, pan, drag-and-drop node, serta deteksi komunitas klaster.
   - Mendukung dua sumber data graf sekaligus: *GraphRAG Knowledge Graph* (`/api/graph/data/:graphId`) dan *Graphiti Temporal Subgraphs* (`/api/enterprise/graphiti/subgraph`).
   - Node Inspector samping yang membedah properti entitas, bobot relasi, ringkasan kontekstual, dan metadata fakta terhubung.
3. **Panel 3 — Live Swarm Simulation Console & Timeline Scrubbing**:
   - Pengendalian siklus hidup simulasi swarm agen cerdas (Start, Pause, Resume, Reset, Step-by-Step Tick).
   - Timeline scrubber putaran (*rounds scrubber*) dengan visualisasi grafik evolusi sentimen polarisasi per ronde interaksi BSP (*Bulk Synchronous Parallel*).
   - Multi-platform post feed live yang membedah persebaran opini simulasi per saluran (Twitter, Reddit, TikTok, News, Facebook).
4. **Panel 4 — Webhook Subscriptions, HMAC-SHA256 Stats & DLQ Re-Drive**:
   - Manajemen siklus hidup langganan webhook enterprise (URL endpoint, secret key, daftar subscription event).
   - Pengukur SLA latensi pengiriman P95 (< 250ms), tingkat keberhasilan pengiriman (*delivery success rate*), dan volume event terdistribusi.
   - Inspektur *Dead-Letter Queue (DLQ)* dengan pengujian dispatch manual berstempel HMAC-SHA256 dan tombol aksi *Re-Drive* pengiriman ulang terdistribusi.
5. **Panel 5 — FastMCP 22 Canonical Tools Catalog & Interactive Invoker Sandbox**:
   - Direktori lengkap 22 perkakas kanonikal Model Context Protocol (FastMCP) yang terdaftar di sistem.
   - Inspeksi skema JSON parameter input (`inputSchema`) untuk setiap perkakas.
   - Sandbox eksekusi interaktif dengan editor parameter JSON, tombol *Invoke Tool*, indikator eksekusi instan, dan penampil respons terformat syntax-highlighted.
6. **Panel 6 — Cryptographic Audit, CaMeL 3-Layer Shield & Enterprise Contracts**:
   - Pengujian keamanan prompt interaktif terhadap ancaman *Jailbreak*, *Prompt Injection*, dan *Data Exfiltration* menggunakan mesin CaMeL 3-Layer Prompt Guard.
   - Visualisasi penandaan *Spotlight XML Delimiter Wrapping* dan deteksi pola berbahaya secara real-time.
   - Registri kontrak pipeline berstempel SHA-256 untuk memverifikasi integritas deliverable antar-subagent.
7. **Panel 7 — Microservices Cluster Health & Orchestrator Watchdog**:
   - Telemetri status kesehatan klaster layanan mikro (FastMCP HTTP Server, OAuth 2.1 Auth Server, SearXNG Search, Graphiti FalkorDB, Redis Cache, Envelope AES-256-GCM Vault).
   - Monitor antrean tugas aktif (*Active Jobs*) dan status pemulihan crash Write-Ahead Log (WAL).
   - Pemicu ping diagnostik sistem secara instan.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 18: OpenAPI 3.1 RESTful API & Distributed Webhook Engine         │
  │   (OpenAPI 3.1, JSON Schema 2020-12, HMAC-SHA256, DLQ Re-drive)       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Upstream API, Events & Subgraphs
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 19: Single Pane of Glass 7-Panel Enterprise Vue 3 Dashboard     │
  │                                                                        │
  │  [P1: Calibration Matrix] ──▶ RecSys Sliders, SVG Radar, Pareto Frontier│
  │  [P2: GraphRAG Explorer]  ──▶ D3.js Force Simulation, Dual Subgraphs   │
  │  [P3: Swarm Console]      ──▶ Round Scrubbers, Feed, Sentiment History │
  │  [P4: Webhook Manager]    ──▶ HMAC-SHA256 Verification, DLQ Re-Drive   │
  │  [P5: FastMCP Sandbox]    ──▶ 22 Tools Catalog, Live Invocation Engine │
  │  [P6: Audit & Security]   ──▶ CaMeL 3-Layer Shield, Contract Registry  │
  │  [P7: System Health]      ──▶ Cluster Health, Watchdog & WAL Recovery  │
  │                                                                        │
  │  [Enterprise API Client]  ──▶ frontend/src/api/enterprise.js           │
  │  [Trilingual i18n]        ──▶ en.json, id.json, zh.json (100% keys)    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Frontend Production Artifacts & Tests
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 20: DevOps, Hardening & Automated QA Gate Guard                  │
  │ Task: t_e84830cd (AES-256-GCM Vault, Discord Reporter, CI/CD Gate)     │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Landasan Teori & Spesifikasi Teknis Komponen 7-Panel

### 2.1 Panel 1: RecSys Algorithm Calibration Matrix & Pareto Frontier
Mekanisme rekomendasi platform media sosial dalam MiroFish mensimulasikan dinamika distribusi konten melalui fungsi utilitas terkalibrasi:
$$U(c) = w_v \cdot V(c) + w_d \cdot D(c) + w_f \cdot F(c) - w_p \cdot P(c)$$
Di mana:
- $V(c)$: Skor virality konten (berdasarkan laju share/repost Hawkes process)
- $D(c)$: Diversitas perspektif konten
- $F(c)$: Fairness keterpaparan kreator kecil
- $P(c)$: Penalti polarisasi echo-chamber

Komponen `Panel1CalibrationMatrix.vue` menyediakan:
- Sliders interaktif $[0.0, 1.0]$ untuk setiap koefisien bobot algoritma.
- Selector platform algoritma bawaan (TikTok For You, X / Twitter Algorithmic Feed, Instagram Explore/Reels, Reddit Hot/Top, YouTube Recommendation).
- SVG Radar Chart dinamis yang memetakan matriks bobot per platform secara visual.
- Simulator Pareto Frontier (`POST /api/enterprise/platforms/simulate-pareto`) yang menghitung kompromi optimal Pareto antara tingkat jangkauan virality dan koefisien polarisasi opini masyarakat.

### 2.2 Panel 2: Knowledge Graph & GraphRAG Explorer
Komponen `Panel2GraphExplorer.vue` memadukan kemampuan D3.js v7 force-directed simulation (`d3-force`) dengan arsitektur dual-data source MiroFish:
1. **GraphRAG Knowledge Graph**: Mengambil data entitas dan relasi ontologis dari endpoint `/api/graph/data/:graphId`.
2. **Graphiti Temporal Subgraphs**: Mengambil subgraf relasi dinamis berbasis proyek dari endpoint `/api/enterprise/graphiti/subgraph?project_id=:projectId`.

Fitur D3 Force Simulation:
- Gaya fisika partikel: `d3.forceManyBody().strength(-300)`, `d3.forceLink().distance(80)`, `d3.forceCenter()`, dan `d3.forceCollide(30)`.
- Navigasi SVG interaktif dengan dukungan *smooth zoom and pan* melalui `d3.zoom()`.
- Node drag-and-drop behavior dengan penyesuaian suhu simulasi (`alphaTarget(0.3).restart()`).
- Indikator komunitas berbasis pewarnaan palet entitas (`Organization`, `Policy`, `Person`, `Metric`, `Concept`).
- Panel samping *Entity Inspector* yang memaparkan atribut lengkap entitas yang dipilih, daftar relasi keluar (*outgoing edges*), dan ringkasan fakta.

### 2.3 Panel 3: Live Swarm Simulation Console & Timeline Scrubbing
Komponen `Panel3SwarmConsole.vue` menyajikan kontrol langsung terhadap mesin simulasi swarm agen cerdas:
- Kontrol state mesin: *Run*, *Pause*, *Reset*, *Step Tick*.
- Timeline scrubber: Penggeser putaran simulasi (*round slider*) yang memungkinkan operator melompat ke putaran tertentu dan mengamati perubahan sentimen rata-rata serta polarisasi agen secara temporal.
- Multi-Platform Posts Feed: Filter feed berbasis tab (All, Twitter/X, Reddit, TikTok) yang menampilkan kiriman agen, skor sentimen, dan interaksi komentar.
- Telemetri metrik real-time: Jumlah agen aktif, total putaran komputasi, rata-rata sentimen populasi, dan indeks polarisasi saat ini.

### 2.4 Panel 4: Webhook Subscriptions, HMAC-SHA256 & DLQ Re-Drive
Komponen `Panel4WebhookManager.vue` terintegrasi langsung dengan mesin webhook terdistribusi Agent 18:
- Pendaftaran langganan webhook baru melalui form modal terverifikasi: Endpoint URL, Secret Key (dengan generator otomatis), dan multi-select event tags.
- Tabel daftar subscription aktif beserta status aktif, tanggal dibuat, dan tombol hapus/deaktivasi.
- Metrik performa delivery: Pengukur latensi P95 (< 250ms SLA), tingkat keberhasilan delivery, dan total pesan terkirim.
- Dead-Letter Queue (DLQ) Inspector: Menampilkan pesan-pesan webhook yang gagal terkirim beserta alasan kegagalan, kode HTTP, dan jumlah percobaan (*retry attempts*).
- Tombol aksi *Re-Drive All Failed Events* (`POST /api/enterprise/webhooks/dlq/redrive`) yang memicu pengiriman ulang terdistribusi seketika.

### 2.5 Panel 5: FastMCP 22 Canonical Tools Catalog & Sandbox
Komponen `Panel5McpSandbox.vue` menghubungkan operator dengan server FastMCP Streamable HTTP (Port 8080):
- Katalog 22 perkakas kanonikal MCP dengan pencarian cepat (*fuzzy filter*) berdasarkan nama perkakas atau deskripsi.
- Inspeksi skema perkakas: Menampilkan parameter yang diwajibkan (*required*) dan tipe data skema JSON Draft 2020-12.
- Interactive Parameter Editor: Editor parameter JSON dengan template parameter default bawaan.
- Sandbox Execution Engine (`POST /api/enterprise/mcp/invoke`): Menjalankan perkakas secara aman dan menampilkan payload hasil eksekusi dalam format JSON terstruktur dengan pewarnaan sintaks.

### 2.6 Panel 6: Cryptographic Audit, CaMeL 3-Layer Shield & Enterprise Contracts
Komponen `Panel6AuditSecurity.vue` mengawal kepatuhan keamanan korporat:
- CaMeL 3-Layer Prompt Shield Tester: Antarmuka pengujian prompt interaktif untuk menguji teks terhadap filter injeksi prompt, ekstraksi data kredensial, dan jailbreak (`POST /api/enterprise/shield/sanitize`).
- Penampil hasil sanitasi XML: Memperlihatkan hasil pembungkusan teks ke dalam format aman `<spotlight>` untuk mencegah pembobolan konteks LLM.
- Enterprise Contracts Ledger (`GET /api/enterprise/contracts`): Daftar verifikasi rantai kontrak antar-subagent lengkap dengan stempel SHA-256 dan status kepatuhan.

### 2.7 Panel 7: Microservices Cluster Health & Orchestrator Watchdog
Komponen `Panel7SystemHealth.vue` memantau kestabilan infrastruktur tingkat sistem:
- Klaster Service Health Cards: Pemantauan status live untuk Backend Core API, FastMCP Server, OAuth 2.1 Server, Graphiti FalkorDB, SearXNG Search, Redis Cache, dan AES-256-GCM Vault.
- Watchdog Health & WAL State: Menampilkan informasi pemulihan crash Write-Ahead Log (WAL) dan metrik thread eksekusi simulasi aktif.
- Tombol *Run Diagnostic Ping* untuk memverifikasi latensi koneksi ujung-ke-ujung seketika.

---

## 3. Arsitektur Modul Enterprise API Client (`frontend/src/api/enterprise.js`)

Untuk memastikan decoupling yang bersih (*separation of concerns*) antara logika antarmuka komponen Vue dan lapisan komunikasi jaringan HTTP, seluruh endpoint enterprise diisolasi dalam modul `frontend/src/api/enterprise.js`.

Metode yang diekspor meliputi:
- **Platform RecSys**: `getPlatforms()`, `simulatePareto(platform, alpha, epsilon, weights)`
- **GraphRAG & Graphiti**: `getGraphProjects()`, `getGraphData(graphId)`, `getGraphitiSubgraph(projectId)`
- **Swarm Simulation**: `getSimulationPosts(simId, platform)`, `getSimulationTimeline(simId)`, `getAgentStats(simId)`
- **Webhooks & DLQ**: `getWebhookStats()`, `getWebhookSubscriptions()`, `createWebhookSubscription(payload)`, `deleteWebhookSubscription(subId)`, `getWebhookDlq()`, `redriveDlq(eventIds)`
- **FastMCP Sandbox**: `getMcpTools()`, `invokeMcpTool(toolName, parameters)`
- **Security & Shield**: `sanitizePrompt(text)`, `getEnterpriseContracts()`, `getWatchdogStatus()`
- **System Health**: `getSystemHealth()`, `getActiveJobs()`

---

## 4. Lokalisasi Trilingual (EN, ID, ZH)

Seluruh 7 panel dan antarmuka dashboard mengimplementasikan standar lokalisasi trilingual tanpa teks *hardcoded*, tersinkronisasi di 3 berkas translasi:
- `locales/en.json`: Kamus bahasa Inggris
- `locales/id.json`: Kamus bahasa Indonesia
- `locales/zh.json`: Kamus bahasa Mandarin (Simplified)

Struktur kunci namespace `dashboard.*` mencakup:
```json
{
  "dashboard": {
    "title": "Enterprise Control Center",
    "subtitle": "Single Pane of Glass: RecSys Calibration, GraphRAG, Swarm Telemetry & Security Audit",
    "allPanels": "All Panels (7)",
    "nav": { "dashboard": "Enterprise Dashboard", "home": "Simulation Home" },
    "p1": { "title": "Platform Algorithm Calibration Matrix", "subtitle": "..." },
    "p2": { "title": "Knowledge Graph & GraphRAG Explorer", "subtitle": "..." },
    "p3": { "title": "Live Swarm Simulation Console & Timeline", "subtitle": "..." },
    "p4": { "title": "Webhook Manager & Dead-Letter Queue (DLQ)", "subtitle": "..." },
    "p5": { "title": "FastMCP Canonical Tools Registry & Invoker Sandbox", "subtitle": "..." },
    "p6": { "title": "Cryptographic Audit, CaMeL Shield & Contracts", "subtitle": "..." },
    "p7": { "title": "System Health, Cluster Topology & Orchestrator Watchdog", "subtitle": "..." }
  }
}
```

---

## 5. Hasil Pengujian Verifikasi & Quality Gates

Pengujian verifikasi otomatis dijalankan melalui script `tests/test_agent_19_dashboard.py` menggunakan interpreter virtual environment Python backend (`backend/.venv/bin/python`).

### Ringkasan Eksekusi Test:
```
======================================================================
Ran 10 tests in 2.136s

OK
======================================================================
```

| ID Test | Cakupan Uji | Status | Waktu |
|---|---|:---:|:---:|
| `test_01_frontend_components_exist` | Keberadaan seluruh 9 berkas Vue & API enterprise | **PASS** | 0.002s |
| `test_02_frontend_build_artifacts` | Integritas build produksi Vite (`dist/index.html`, bundle JS/CSS) | **PASS** | 0.001s |
| `test_03_trilingual_i18n_completeness` | Kelengkapan kunci trilingual (`en`, `id`, `zh`) pada 7 panel | **PASS** | 0.008s |
| `test_04_panel1_recsys_calibration_api` | Matriks platform & simulasi Pareto efficiency frontier | **PASS** | 0.095s |
| `test_05_panel2_graph_data_api` | Katalog projek graf & ekstraksi graf relasional GraphRAG | **PASS** | 0.012s |
| `test_06_panel3_swarm_simulation_api` | Postingan simulasi agen, timeline putaran, dan feed multi-platform | **PASS** | 0.008s |
| `test_07_panel4_webhooks_and_dlq_api` | CRUD pendaftaran webhook, inspeksi stats, dan re-drive DLQ | **PASS** | 0.045s |
| `test_08_panel5_mcp_tools_and_sandbox_api` | Katalog perkakas FastMCP dan eksekusi diagnostik sandbox | **PASS** | 0.015s |
| `test_09_panel6_audit_security_and_shield_api` | CaMeL prompt sanitization, spotlight XML, dan kontrak audit | **PASS** | 0.018s |
| `test_10_panel7_system_health_and_jobs_api` | Status kesehatan klaster microservices dan jobs recovery | **PASS** | 0.004s |

### Frontend Build Validation:
```bash
$ cd frontend && npm run build
vite v7.1.3 building for production...
transforming...
✓ 125 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.82 kB │ gzip:  0.44 kB
dist/assets/index-BbV32eJ7.css   31.20 kB │ gzip:  5.40 kB
dist/assets/index-CWGqXh1L.js   342.15 kB │ gzip: 112.30 kB
✓ built in 383ms
```

---

## 6. Manifest Berkas Deliverable

Berikut adalah daftar berkas yang diimplementasikan, dimodifikasi, dan diverifikasi oleh Agent 19:

1. **Komponen Dashboard Frontend (`frontend/src/components/dashboard/`)**:
   - `Panel1CalibrationMatrix.vue`: Visualisasi matriks kalibrasi RecSys, slider interaktif, SVG radar chart, dan simulator Pareto frontier.
   - `Panel2GraphExplorer.vue`: Visualisasi graf D3 force-directed untuk GraphRAG dan Graphiti subgraph, dilengkapi node inspector dan kontrol zoom/pan.
   - `Panel3SwarmConsole.vue`: Konsol kendali simulasi, timeline scrubber putaran, telemetri sentimen temporal, dan live multi-platform post feed.
   - `Panel4WebhookManager.vue`: Manajemen langganan webhook enterprise, generator secret key, metrik P95, dan inspektor serta re-drive DLQ.
   - `Panel5McpSandbox.vue`: Direktori 22 perkakas FastMCP, penampil skema input parameter, dan sandbox pemanggilan tool interaktif.
   - `Panel6AuditSecurity.vue`: Diagnostik CaMeL Prompt Guard, penampil spotlight XML sanitization, dan registri verifikasi kontrak.
   - `Panel7SystemHealth.vue`: Kartu telemetri klaster layanan mikro, status orchestrator watchdog, WAL crash recovery, dan aksi diagnostic ping.
2. **Tampilan Utama & Navigasi**:
   - `frontend/src/views/DashboardView.vue`: Halaman utama Single Pane of Glass yang merangkai ke-7 panel dalam layout responsif dengan sticky navigation bar, filter tab, dan tombol aksi cepat.
   - `frontend/src/views/Home.vue`: Integrasi tautan navigasi langsung ke Enterprise Dashboard pada bilah navigasi utama.
3. **Lapisan Komunikasi Jaringan Enterprise**:
   - `frontend/src/api/enterprise.js`: Wrapper modular untuk pemanggilan seluruh endpoint enterprise backend.
4. **Kamus Internasionalisasi Trilingual**:
   - `locales/en.json`: Kamus bahasa Inggris diperbarui untuk seluruh 7 panel.
   - `locales/id.json`: Kamus bahasa Indonesia diperbarui untuk seluruh 7 panel.
   - `locales/zh.json`: Kamus bahasa Mandarin diperbarui untuk seluruh 7 panel.
5. **Skrip Pengujian Verifikasi & Dokumen Kontrak**:
   - `tests/test_agent_19_dashboard.py`: Skrip pengujian otomatis 10 test suite menyeluruh.
   - `contracts/DELIVERABLE-AGENT-19.md`: Dokumen kontrak spesifikasi deliverable resmi Agent 19.

---

## 7. Kepatuhan Keamanan & Sanitasi Kredensial

Sesuai dengan protokol keamanan platform MiroFish Enterprise:
- Tidak ada API key, token rahasia, kata sandi, atau connection string plaintext yang disimpan dalam berkas antarmuka frontend maupun deliverable kontrak.
- Seluruh rahasia yang ditampilkan dalam antarmuka UI (seperti secret key webhook) disamarkan menggunakan format masking `whsec_...` dan diperlakukan sebagai nilai tersanitasi.
- Seluruh uji injeksi prompt dan CaMeL shield diverifikasi aman dari eksekusi instruksi arbitrer.

---

## 8. Handoff ke Agent 20 (DevOps, Production Hardening & QA Gate Guard)

Deliverable Agent 19 telah terverifikasi secara penuh dan siap untuk diserahterimakan kepada **Agent 20 (DevOps, Production Hardening & QA Gate Guard - Task `t_e84830cd`)**:
1. **Bundle Produksi Frontend**: Berkas siap saji di `frontend/dist/` siap dibungkus dalam container NGINX / Docker production image.
2. **Kesiapan Verifikasi CI/CD**: Skrip `tests/test_agent_19_dashboard.py` dapat langsung diintegrasikan ke dalam automated pipeline verification test suite.
3. **Pilar Observabilitas**: Ke-7 panel dashboard enterprise siap menerima telemetri live dari produksi setelah deployment tahap akhir.
