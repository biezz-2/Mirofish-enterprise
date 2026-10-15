# Master Plan: Implementasi Konfigurasi Notion MiroFish Enterprise v3.1 (20 Subagent Swarm)

- **Project ID**: `project-mirofish-enterprise-notion`
- **Repositori Target**: `biezz-2/Mirofish-enterprise`
- **Basis Rujukan**: 9 Dokumen Riset Notion MiroFish Enterprise + *Discrete Choice Methods with Simulation* (Train)
- **Target Distribusi**: 20 Subagent Otonom (6 Divisi Spesialisasi)
- **Status Protokol**: `PLAN_APPROVED` (Mengikuti Master Agent Operating Protocol AGENTS.md)

---

## 1. Tujuan & Kriteria Keberhasilan (Objective & Success Criteria)

### Tujuan:
Menerapkan seluruh konfigurasi, spesifikasi matematis, algoritma rekomendasi, pertahanan anti-injeksi, pemodelan psikologi agen, dan arsitektur ekstensibilitas universal dari 9 Dokumen Notion MiroFish Enterprise v3.1 ke dalam repositori secara terstruktur, teruji, dan siap-produksi.

### Kriteria Keberhasilan (Testable & Observable):
1. **Step 0 (Web Research)**: Klaster SearXNG privat berfungsi tanpa pelacakan (*zero-tracking*), dilindungi oleh 3-Layer Shield CaMeL (DeepMind) dan domain credibility scoring ($\ge 0.7$).
2. **Step 1 (GraphRAG)**: Integrasi dual-backend (Graphiti FalkorDB/Neo4j & Zep Cloud) dengan Graph Readiness Barrier dan evaluasi NLI (*Natural Language Inference*) untuk menjamin *zero fabricated data*.
3. **Step 2 (OCEAN & Humanoid)**: Agen terkonfigurasi dengan Whole Trait Theory ($s = \text{trait} + \text{noise}$), Cybernetic Big Five, kebutuhan dasar System 1 (ODE $dN/dt = -\lambda N$), 7 emosi Ekman, dan Nested Logit.
4. **Step 3 (Parallel Simulation)**: Swarm BSP berjalan sinkron pada 7 platform (Twitter, X, Reddit, TikTok, Instagram, Facebook, Threads) ditenagai 3-Stage RecSys Funnel (Candidate Gen, Heavy Ranking, Re-Ranking dengan damping 0.40–0.80) serta model viralitas Hawkes/Granovetter.
5. **Step 4 (ReportAgent)**: Analisis intelijen prediktif ReACT mengadopsi BettaFish ReportEngine, sitasi graf terverifikasi `[VERIFIED]`, dan safe abstention.
6. **Step 5 (Universal Extensibility)**: MCP Server 11 canonical tools aktif, REST API OpenAPI 3.1.0 (JSON Schema 2020-12), Distributed Webhooks (HMAC-SHA256 & DLQ), dan 7-Panel Vue 3 Enterprise Dashboard.
7. **Ketahanan & Keamanan**: Enkripsi envelope AES-256-GCM pada credentials, Crash Recovery Scanner otomatis dari ronde terakhir ($R_{last}$), dan 9Router LLM failover gateway.

---

## 2. Matriks Pembagian Tugas 20 Subagent (6 Divisi Spesialisasi)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   DIVISI A: RISET WEB & KEAMANAN (STEP 0)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agent 01: Lead Orchestrator & Swarm Dispatcher                              │
│ Agent 02: SearXNG Private Search & Metasearch Ingestion Specialist          │
│ Agent 03: CaMeL 3-Layer Prompt Shield & Content Sanitizer Guard             │
│ Agent 04: Domain Credibility Scorer & Epistemic Grounding Validator        │
├─────────────────────────────────────────────────────────────────────────────┤
│               DIVISI B: KNOWLEDGE ENGINEERING & GRAPHRAG (STEP 1)           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agent 05: GraphRAG Ontology & Adaptive Text Chunking Specialist             │
│ Agent 06: Graphiti & FalkorDB/Neo4j Control Plane Engineer                  │
│ Agent 07: Zep Cloud & NLI Verification Barrier Specialist                   │
├─────────────────────────────────────────────────────────────────────────────┤
│              DIVISI C: PSIKOMETRI & PERILAKU AGEN (STEP 2 - HUMANOID)       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agent 08: Whole Trait Theory & Cybernetic Big Five Personality Modeler      │
│ Agent 09: Humanoid ODE Basic Needs & Ekman Affective State Engine           │
│ Agent 10: Nested Logit & DDM / Prospect Theory Self-Censorship Engineer     │
├─────────────────────────────────────────────────────────────────────────────┤
│             DIVISI D: RECSYS FUNNEL & DINAMIKA VIRAL (STEP 3 - SWARM)       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agent 11: 3-Stage RecSys Funnel Engineer (Candidate, Rank, Re-Rank)        │
│ Agent 12: 7-Platform Algorithm Calibration Matrix Specialist                │
│ Agent 13: Hawkes Process & Rescorla-Wagner Viral Cascade Modeler            │
│ Agent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery Specialist     │
├─────────────────────────────────────────────────────────────────────────────┤
│             DIVISI E: ANALITIK PREDIKTIF & REPORTING (STEP 4 & 5)           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agent 15: ReACT ReportAgent Multi-Turn Investigation & Deduction Analyst    │
│ Agent 16: BettaFish Analytics & Sentiment Model Integration Engineer        │
├─────────────────────────────────────────────────────────────────────────────┤
│            DIVISI F: EKSTENSIBILITAS UNIVERSAL & DASHBOARD (STEP 5)         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agent 17: Canonical Model Context Protocol (MCP) Server Architect           │
│ Agent 18: OpenAPI 3.1 RESTful API & Distributed Webhook Engine Architect   │
│ Agent 19: Vue 3 Enterprise 7-Panel Control Dashboard Frontend Developer     │
│ Agent 20: DevOps, AES-256-GCM Vault & QA Phase-Gate Verification Guard      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Rincian Teknis, Kontrak & Deliverable Tiap Subagent

### [DIVISI A: Riset Web & Keamanan - Step 0]

#### Subagent 01: Lead Orchestrator & Swarm Dispatcher
- **Fokus**: Tata kelola orkestrasi master, state machine 6-langkah, pelacakan kanban board `.state/boards/`, dan manajemen hand-off antar-agen.
- **Deliverable**:
  - `backend/app/services/orchestrator.py`: Sinkronisasi siklus hidup proyek (Init -> Research -> Graph -> Setup -> Simulation -> Report).
  - Skrip automasi pipeline hand-off kontrak JSON di `contracts/pipeline/`.
- **Kriteria Validasi**: State transition konsisten, tidak ada deadlocks antar-agen, checkpoint status tercatat di database WAL.

#### Subagent 02: SearXNG Private Search & Metasearch Ingestion Specialist
- **Fokus**: Implementasi Dokumen 4 & 8 — metasearch privat tanpa pelacakan (*zero-tracking*), multi-engine routing.
- **Deliverable**:
  - `searchxng/settings.yml`: Konfigurasi engine privat (Google, Bing, DuckDuckGo, Brave, arXiv).
  - `backend/app/services/searxng_client.py`: Client asinkron dengan rotasi user-agent, fallback query, dan rate-limiting.
- **Kriteria Validasi**: Query dieksekusi tanpa kebocoran IP klien, latensi rata-rata < 1.2s per batch pencarian.

#### Subagent 03: CaMeL 3-Layer Prompt Shield & Content Sanitizer Guard
- **Fokus**: Implementasi Dokumen 4 — Arsitektur CaMeL DeepMind untuk eliminasi risiko prompt injection dari korpus web.
- **Deliverable**:
  - `backend/app/services/anti_injection.py`:
    - Lapisan 1: Regex & HTML sanitizer (membersihkan payload skrip, inline CSS, zero-width chars).
    - Lapisan 2: Spotlighting dengan tag pembatas XML terstruktur (`<untrusted_content_data>`).
    - Lapisan 3: Ekstraktor deterministik pasif tanpa tool-call (LLM pasif dilarang mengeksekusi aksi/perintah).
- **Kriteria Validasi**: Lulus 100% test case uji injeksi prompt (jailbreak prompt, indirect injection, delimiter breaking).

#### Subagent 04: Domain Credibility Scorer & Epistemic Grounding Validator
- **Fokus**: Implementasi Dokumen 8 — Penilaian kredibilitas sumber web dan tagging status epistemik.
- **Deliverable**:
  - `backend/app/services/web_research_service.py`: Modul penilaian kredibilitas domain ($\ge 0.7$ untuk media kredibel/jurnal, $< 0.5$ untuk forum anonim).
  - Penandaan label epistemik eksplisit: `[VERIFIED]`, `[UNVERIFIED]`, `[ASSUMED]`.
- **Kriteria Validasi**: Setiap fakta dalam korpus web memiliki skor kredibilitas numerik terlampir dan sitasi domain asli.

---

### [DIVISI B: Knowledge Engineering & GraphRAG - Step 1]

#### Subagent 05: GraphRAG Ontology & Adaptive Text Chunking Specialist
- **Fokus**: Implementasi Dokumen 8 — Ekstraksi entitas & relasi graf terstruktur dengan pemotongan teks adaptif.
- **Deliverable**:
  - `backend/app/services/graph_builder.py`: Semantic chunker berbasis batas paragraf dan kohesi topikal.
  - Skema ontologi ketat: Node `PascalCase` (`Person`, `Organization`, `Policy`), Relasi `SCREAMING_SNAKE` (`SUPPORTS`, `OPPOSES`, `AFFILIATED_WITH`).
- **Kriteria Validasi**: Ekstraksi entitas konsisten, nol token redundan, pemetaan skema tervalidasi Pydantic.

#### Subagent 06: Graphiti & FalkorDB/Neo4j Control Plane Engineer
- **Fokus**: Implementasi Dokumen 8 — Control plane graf lokal performa tinggi untuk retensi data sensitif enterprise.
- **Deliverable**:
  - FastMCP / FastAPI Control Plane pada port 8080 terhubung ke FalkorDB/Redis (port 6379) atau Neo4j lokal (port 7474/7687).
  - `backend/app/services/graphiti_service.py`: Adapter GraphMemoryAdapter dengan dukungan kueri subgraf berorientasi waktu.
- **Kriteria Validasi**: Operasi write/read subgraf sub-100ms, data graf terisolasi per `project_id`.

#### Subagent 07: Zep Cloud & NLI Verification Barrier Specialist
- **Fokus**: Implementasi Dokumen 8 — Integrasi Zep Cloud Episode Batch API dan evaluasi inferensi semantik (NLI).
- **Deliverable**:
  - `backend/app/services/zep_adapter.py`: Pipeline batch episode ingestion ke Zep Cloud Graph.
  - **Graph Readiness Barrier**: Memastikan graf terindeks 100% sebelum simulasi dimulai.
  - **NLI Verifier**: Evaluasi premise-hypothesis entailment pada fakta graf untuk menjamin *zero fabricated entities*.
- **Kriteria Validasi**: Graf dinyatakan `READY` hanya jika indeks Zep sinkron dan skor NLI $\ge 0.85$.

---

### [DIVISI C: Psikometri & Perilaku Agen - Step 2]

#### Subagent 08: Whole Trait Theory & Cybernetic Big Five Modeler
- **Fokus**: Implementasi Dokumen 1, 3, & 6 — Kepribadian dinamis non-statis.
- **Deliverable**:
  - `backend/app/services/psychometrics.py`:
    - Distribusi keadaan dinamis Fleeson: $s = \text{trait} + \text{noise}$, di mana noise berdistribusi Gauss terikat deviasi standar $\sigma$.
    - Pemetaan Cybernetic Big Five DeYoung (O: eksplorasi kognitif, C: regulasi target, E: ganjaran sosial, A: afiliasi altruistik, N: sensitivitas ancaman/stres).
- **Kriteria Validasi**: Trait agen berfluktuasi realistis sepanjang ronde tanpa kehilangan identitas inti karakter.

#### Subagent 09: Humanoid ODE Basic Needs & Ekman Affective State Engine
- **Fokus**: Implementasi Dokumen 6 — Kebutuhan dasar System 1 dan emosi afektif.
- **Deliverable**:
  - `backend/app/services/humanoid_needs.py`:
    - Persamaan diferensial peluruhan kebutuhan: $dN_i/dt = -\lambda_i N_i$ (sosial, energi, pemenuhan informasi).
    - 7 Model emosi dasar Paul Ekman (Joy, Sadness, Anger, Fear, Disgust, Surprise, Trust) dan skala kedekatan sosial (0–30).
    - Jam biologis / siklus sirkadian untuk probabilitas aktivitas per jam.
- **Kriteria Validasi**: Tingkat kelelahan/stres mempengaruhi keputusan agen secara deterministik; agen tidur di jam istirahat.

#### Subagent 10: Nested Logit & DDM / Prospect Theory Self-Censorship Engineer
- **Fokus**: Implementasi Dokumen 3 & Referensi Kenneth Train — Pengambilan keputusan rasional berbatas.
- **Deliverable**:
  - `backend/app/services/decision_engine.py`:
    - **Nested Logit Engine**: Pemilihan bertingkat (Tingkat 1: Aktif vs Lurker; Tingkat 2: Konsumsi vs Produksi; Tingkat 3: Like, Repost, Komentar, Quote).
    - **Ratcliff Drift-Diffusion Model (DDM)**: Kalkulasi latensi perhatian (*dwell time*) dan kecepatan baca feed.
    - **Kahneman-Tversky Prospect Theory**: Kurva nilai asimetris ($S$-shaped) untuk memodelkan keengganan risiko sosial dan sensor-diri (*self-censorship*).
- **Kriteria Validasi**: Mengeliminasi cacat asumsi IIA pada softmax datar; persentase lurker sesuai rasio Pareto empiris (90-9-1).

---

### [DIVISI D: RecSys Funnel & Dinamika Viral - Step 3]

#### Subagent 11: 3-Stage RecSys Funnel Engineer
- **Fokus**: Implementasi Dokumen 7 — Corong algoritma rekomendasi feed 3-tahap.
- **Deliverable**:
  - `backend/app/services/recsys_funnel.py`:
    - Tahap 1 (*Candidate Generation*): Retrieval cepat berbasis homofili graf jaringan dan kemiripan kosinus embedding semantik.
    - Tahap 2 (*Heavy Ranking*): Multi-task scoring terbobot spesifik per platform.
    - Tahap 3 (*Re-Ranking & Diversity*): Time-decay eksponensial, peredaman ruang gema (*echo chamber damping* 0.40–0.80), dan $\epsilon$-greedy exploration ($\epsilon = 0.05$).
- **Kriteria Validasi**: Feed agen tidak monoton, distribusi paparan seimbang antara konten serupa dan konten eksploratif.

#### Subagent 12: 7-Platform Algorithm Calibration Matrix Specialist
- **Fokus**: Implementasi Dokumen 2 & 7 — Kalibrasi spesifik algoritma 7 platform.
- **Deliverable**:
  - `backend/app/services/platform_matrix.py`:
    - **Twitter / X**: Pembobotan emosi moral tinggi, rasio quote-tweet, penalti tautan luar.
    - **Reddit**: Upvote/downvote ratio, karma threshold, penalti subreddit rule violation.
    - **TikTok**: Completion rate video, loop count, dwell time dominan.
    - **Instagram**: Visual affinity, hashtag clustering, DM share weight.
    - **Facebook**: Family/friends graph closeness, reaksi emosional ganda (*Care*, *Angry*).
    - **Threads**: Interkoneksi feed berbasis teks cepat, peredaman konten politis agresif.
- **Kriteria Validasi**: Metrik keterlibatan pada masing-masing platform menunjukkan korelasi statistik dengan benchmark platform riil.

#### Subagent 13: Hawkes Process & Rescorla-Wagner Viral Cascade Modeler
- **Fokus**: Implementasi Dokumen 3 — Pemodelan kaskade viralitas dan lonjakan dopamin keterlibatan.
- **Deliverable**:
  - `backend/app/services/cascade_dynamics.py`:
    - **Rescorla-Wagner Reward Prediction Error**: $V \leftarrow V + \alpha(R - V)$ untuk memodelkan kecanduan notifikasi dan lonjakan frekuensi unggah.
    - **Hawkes Self-Exciting Point Process**: Intensitas bersyarat $\lambda(t) = \mu + \sum_{t_i < t} \alpha e^{-\beta(t - t_i)}$ untuk penularan informasi lintas klaster.
    - **Granovetter Threshold Model**: Aktivasi partisipasi kolektif setelah ambang batas tetangga terpenuhi.
- **Kriteria Validasi**: Mampu mereplikasi kurva kurva viralitas nyata (lonjakan eksponensial diikuti peluruhan ekor panjang / *long-tail decay*).

#### Subagent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery Specialist
- **Fokus**: Implementasi Dokumen 2 — Mesin eksekusi massal paralel dengan jaminan pemulihan nir-kehilangan (*zero-loss*).
- **Deliverable**:
  - `backend/scripts/run_parallel_simulation.py` & `simulation_runner.py`:
    - Sinkronisasi Bulk Synchronous Parallel (BSP) per-ronde.
    - Snapshot status agen, memori graf, dan aksi ke SQLite WAL per akhir ronde.
    - SHA-256 state hashing untuk verifikasi integritas snapshot.
    - Auto-resume scanner yang mendeteksi ronde terakhir ($R_{last}$) pasca crash tanpa pengulangan dari awal.
- **Kriteria Validasi**: Penghentian paksa simulasi pada ronde N dapat dilanjutkan seketika ke ronde N+1 dengan state 100% identik.

---

### [DIVISI E: Analitik Prediktif & Pelaporan - Step 4 & 5]

#### Subagent 15: ReACT ReportAgent Multi-Turn Investigation & Deduction Analyst
- **Fokus**: Implementasi Dokumen 2 & 4 — Agen analis otonom berbasis ReACT loop terpandu ontologi.
- **Deliverable**:
  - `backend/app/services/report_agent.py`:
    - ReACT loop dengan pemanggilan instrumen investigasi (InsightForge, Panorama, Search, Agen Interview IPC).
    - Klausul *safe abstention*: menolak spekulasi tanpa bukti empiris pada data simulasi/graf.
    - Sitasi wajib ke simpul graf terverifikasi (`[VERIFIED]`).
- **Kriteria Validasi**: Laporan analitik bebas dari fabrikasi data, setiap klaim memiliki sitasi simpul graf dan trace log simulasi.

#### Subagent 16: BettaFish Analytics & Sentiment Model Integration Engineer
- **Fokus**: Implementasi Dokumen 5 — Adopsi pola arsitektur BettaFish ke MiroFish Enterprise.
- **Deliverable**:
  - `backend/app/services/bettafish_adapter.py`:
    - Porting *ReportEngine* BettaFish untuk ringkasan eksekutif berstandar C-level.
    - Integrasi *SentimentAnalysisModel* untuk polarisasi polar/multi-dimensi.
    - *InsightEngine* untuk ingestion data privat/konfidensial klien.
- **Kriteria Validasi**: Format laporan eksekutif modular, skor sentimen terkalibrasi pada sentimen spesifik domain publik/bisnis.

---

### [DIVISI F: Ekstensibilitas Universal & Antarmuka - Step 5]

#### Subagent 17: Canonical Model Context Protocol (MCP) Server Architect
- **Fokus**: Implementasi Dokumen 9 — Ekosistem MCP Server untuk integrasi native dengan AI coding agents.
- **Deliverable**:
  - `backend/mcp_server/`: Server FastMCP/Streamable HTTP dengan 11 canonical tools strictly-typed:
    1. `create_simulation_project`
    2. `trigger_web_research`
    3. `build_knowledge_graph`
    4. `generate_agent_profiles`
    5. `calibrate_platform_algorithms`
    6. `execute_parallel_simulation`
    7. `fetch_simulation_stream`
    8. `query_graph_insights`
    9. `generate_executive_report`
    10. `interview_simulation_agent`
    11. `audit_system_diagnostics`
  - Autentikasi OAuth 2.1 & scoped bearer tokens.
- **Kriteria Validasi**: Seluruh 11 tools terdaftar dan dapat dipanggil secara deterministik melalui AI client eksternal (Claude/Hermes).

#### Subagent 18: OpenAPI 3.1 RESTful API & Distributed Webhook Engine Architect
- **Fokus**: Implementasi Dokumen 9 — RESTful API modern dan sistem webhook terdistribusi.
- **Deliverable**:
  - `backend/app/api/`: Endpoint OpenAPI 3.1.0 terikat JSON Schema 2020-12 dengan SSE stream untuk event linimasa real-time.
  - `backend/app/services/webhook_service.py`: Webhook dispatcher asinkron dengan tanda tangan HMAC-SHA256, automatic retry exponential backoff, dan Dead Letter Queue (DLQ).
- **Kriteria Validasi**: Validasi payload 100% lolos JSON Schema, webhook terkirim andal dengan toleransi kegagalan jaringan.

#### Subagent 19: Vue 3 Enterprise 7-Panel Control Dashboard Frontend Developer
- **Fokus**: Implementasi Dokumen 9 (Bab 5) — Antarmuka terpadu (*single pane of glass*) 7 panel.
- **Deliverable**:
  - `frontend/src/views/`:
    - Panel 1: Platform Algorithm Calibration Matrix
    - Panel 2: GraphRAG & Knowledge Explorer (D3.js / 3D Canvas)
    - Panel 3: Live Swarm Simulation Console (Playback & feed stream)
    - Panel 4: API, MCP & Webhook Manager
    - Panel 5: MCP Tool Catalog & Interactive Sandbox
    - Panel 6: Audit & Security Center (AES-256-GCM Vault monitor)
    - Panel 7: System Health & Engine Diagnostics (SearXNG, Redis, Zep)
  - Dukungan multibahasa menyeluruh (`vue-i18n`): Bahasa Indonesia (PUEBI), English, Mandarin.
- **Kriteria Validasi**: Bebas blank screen, routing SPA terproteksi, responsif pada resolusi desktop enterprise, zero console error.

#### Subagent 20: DevOps, AES-256-GCM Vault & QA Phase-Gate Verification Guard
- **Fokus**: Dokumen 9 & Standar Operasional Enterprise — Infrastruktur, keamanan rahasia, dan audit kualitas.
- **Deliverable**:
  - `docker-compose.yml` & `ecosystem.config.js`: Orkestrasi multi-service (Backend, Frontend, SearXNG, Redis, Neo4j).
  - `backend/app/utils/vault.py`: Enkripsi envelope AES-256-GCM untuk API keys dan webhook secrets.
  - `backend/tests/`: Rangkaian automated unit test & integration test untuk seluruh 6 langkah kanonikal.
- **Kriteria Validasi**: Seluruh service dapat berjalan otomatis dalam satu perintah (`pm2 start` / `docker compose up`), 100% tes lulus tanpa regresi.

---

## 4. Urutan Eksekusi & Hand-off Pipeline (Execution Flow)

```
[Minggu 1: Fondasi & Grounding]
Subagent 01, 20 (Setup Board & Infra)
       │
       ▼
Subagent 02, 03, 04 (SearXNG, CaMeL Shield, Credibility Scorer) ──► 01-step0-research.json
       │
       ▼
[Minggu 2: Rekayasa Pengetahuan & Graf]
Subagent 05, 06, 07 (Ontology, Graphiti, Zep NLI Barrier) ────────► 02-step1-graphrag.json
       │
       ▼
[Minggu 3: Psikometri & Engine Rekomendasi]
Subagent 08, 09, 10 (Whole Trait, Humanoid ODE, Nested Logit) ─────► 03-step2-agents.json
Subagent 11, 12, 13 (RecSys Funnel, Platform Matrix, Hawkes) ──────► 04-step3-recsys.json
       │
       ▼
[Minggu 4: Eksekusi Swarm & Intelijen Pelaporan]
Subagent 14 (BSP Parallel Runner & Crash Recovery) ────────────────► 05-step3-simulation.jsonl
Subagent 15, 16 (ReportAgent ReACT & BettaFish) ───────────────────► 06-step4-report.md
       │
       ▼
[Minggu 5: Ekstensibilitas Enterprise & Dashboard]
Subagent 17, 18 (Canonical MCP & OpenAPI REST/Webhooks) ───────────► 07-step5-api-mcp.json
Subagent 19 (Vue 3 7-Panel Control Dashboard) ─────────────────────► 08-step5-dashboard.dist
       │
       ▼
[Final Gate: Phase-Gate Audit V1-V8]
Subagent 20 & Evaluator Independen (PASS / CONDITIONAL / FAIL)
```

---

## 5. Protokol Phase-Gate Validation (V1 - V8)
Setiap fase transisi wajib melalui validasi skeptis senior engineer:
- **V1 (Spec Completeness)**: Kesesuaian 100% terhadap 9 dokumen Notion.
- **V2 (Logic Correctness)**: Verifikasi matematis ODE, Nested Logit, Hawkes, dan RecSys Funnel.
- **V3 (Security & OWASP)**: Audit sanitasi CaMeL, IDOR, SQL injection, dan enkripsi AES-256-GCM.
- **V4 (Standards via Web Search)**: Verifikasi standar terkini OpenAPI 3.1, MCP Specification, dan Vue 3.5.
- **V5 (Performance & Resources)**: Uji beban konkurensi BSP multi-ronde dan latensi read sub-100ms.
- **V6 (Regression Check)**: Memastikan tidak merusak endpoint dan alur simulasi yang sudah ada.
- **V7 (Code Quality)**: Standar Python PEP 8, tipe data statis, penanganan exception terpusat.
- **V8 (Handoff & Docs)**: Pembaruan OpenAPI docs, Wiki internal, dan persistensi state di `.state/boards/`.
