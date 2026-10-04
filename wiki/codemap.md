---
title: Codemap Komprehensif dan Peta Arsitektur Berkas MiroFish
type: reference
tags: [codemap, directory-tree, module-dependencies, e2e-dataflow, subagent-ownership, v3.1]
related:
  - "[[index]]"
  - "[[arsitektur]]"
  - "[[kesiapan-operasional]]"
  - "[[panduan-operasional]]"
sources:
  - backend/
  - frontend/
  - locales/
  - scripts/
  - tests/
---

> 🌐 **Bahasa / Language**: [Bahasa Indonesia](./codemap.md) | [English](./en/codemap.md)

# Codemap Komprehensif: Struktur Kode, Dependensi, dan Kepemilikan Subagent (v3.1)

Dokumen ini adalah rujukan teknis definitif (*canonical code map*) dari repositori **MiroFish**. Bab ini menguraikan seluruh hierarki berkas, matriks dependensi antar-modul, alur data mikro *end-to-end*, dan pembagian kepemilikan kode untuk 10 subagent pengembang.

---

## 1. Pohon Direktori Lengkap & Deskripsi Peran Berkas

```
/home/biezz/Project/apps/MiroFish/
├── .env.example                       # Templat konfigurasi lingkungan (LLM, Zep, Port)
├── .gitignore                         # Pengecualian pelacakan Git (cache, uploads, venv)
├── .dockerignore                      # Pengecualian build image Docker
├── Dockerfile                         # Definisi container image monolitik MiroFish
├── docker-compose.yml                 # Orkestrasi container layanan (Backend, Frontend)
├── LICENSE                            # Lisensi perangkat lunak (Apache 2.0 / MIT)
├── package.json                       # Konfigurasi dependensi Node.js tingkat root
├── package-lock.json                  # Lockfile dependensi Node.js root
├── README.md                          # Dokumentasi pengantar repositori (Bahasa Inggris)
├── README-ZH.md                       # Dokumentasi pengantar repositori (Bahasa Mandarin)
│
├── backend/                           # LUMBUNG LOGIKA SERVER & SISTEM MULTI-AGEN
│   ├── pyproject.toml                 # Konfigurasi proyek Python, metadata, & linter
│   ├── requirements.txt               # Daftar pustaka pip (Flask, OpenAI, Zep, SQLAlchemy)
│   ├── uv.lock                        # Lockfile manajer paket ultra-cepat UV
│   ├── run.py                         # Titik masuk eksekusi Flask Backend (Entrypoint)
│   │
│   ├── app/                           # Paket inti aplikasi Flask
│   │   ├── __init__.py                # Application Factory, CORS, dan inisialisasi Blueprint
│   │   ├── config.py                  # Pemuat konfigurasi terpadu .env & validasi env vars
│   │   │
│   │   ├── api/                       # Lapisan antarmuka HTTP REST Controller
│   │   │   ├── __init__.py            # Deklarasi Blueprint: graph_bp, sim_bp, report_bp
│   │   │   ├── graph.py               # Endpoint upload, ekstraksi teks, ontologi, Zep build
│   │   │   ├── simulation.py          # Endpoint entitas, profil agen, prepare, run, IPC
│   │   │   └── report.py              # Endpoint pembuatan laporan ReACT, SSE log, chat
│   │   │
│   │   ├── models/                    # Lapisan persistensi data & model status
│   │   │   ├── __init__.py            # Ekspor modul TaskManager, ProjectManager, Models
│   │   │   ├── project.py             # Model Project transaksional berbasis berkas/memori
│   │   │   ├── task.py                # TaskManager thread-safe untuk tracking pekerjaan async
│   │   │   └── entities.py            # Model SQLAlchemy relasional v3.1 (SQLite/Postgres)
│   │   │
│   │   ├── services/                  # Lapisan logika bisnis & pemrosesan domain
│   │   │   ├── __init__.py            # Pendaftaran layanan inti MiroFish
│   │   │   ├── text_processor.py      # Ekstraksi berkas teks & normalisasi segmentasi chunk
│   │   │   ├── ontology_generator.py  # Ekstraksi ontologi entitas/relasi berbasis LLM
│   │   │   ├── graph_builder.py       # Pembangun graf Zep Cloud via Batch Ingestion API
│   │   │   ├── zep_entity_reader.py   # Pembaca & filter simpul/sisi dari Zep Graph
│   │   │   ├── oasis_profile_generator.py # Generator profil kepribadian agen OASIS (OCEAN)
│   │   │   ├── simulation_config_generator.py # Generator parameter aktivitas & platform
│   │   │   ├── simulation_manager.py  # Orkestrator siklus hidup simulasi tingkat tinggi
│   │   │   ├── simulation_runner.py   # Pengendali eksekusi subproses & pemantau runner
│   │   │   ├── simulation_ipc.py      # Kanal komunikasi IPC file-based (Command/Response)
│   │   │   ├── zep_graph_memory_updater.py # Injeksi memori aksi baru secara dinamis ke Zep
│   │   │   ├── zep_tools.py           # Toolkit analis ReACT (Search, InsightForge, Panorama)
│   │   │   └── report_agent.py        # Agen cerdas ReACT perencana & penulis laporan akhir
│   │   │
│   │   └── utils/                     # Pustaka utilitas lintas modul
│   │       ├── __init__.py            # Inisialisasi modul utilitas
│   │       ├── file_parser.py         # Parsing multi-format dokumen (PDF, MD, TXT)
│   │       ├── llm_client.py          # Klien abstraksi pemanggilan OpenAI & model kompatibel
│   │       ├── openai_chat_compat.py  # Normalisasi kompatibilitas skema payload chat LLM
│   │       ├── ontology.py            # Validasi aturan penamaan PascalCase & SCREAMING_SNAKE
│   │       ├── retry.py               # Algoritma retry eksponensial ber-jitter untuk jaringan
│   │       ├── zep.py                 # Klien Zep Cloud SDK & penanganan error transien
│   │       ├── zep_lifecycle.py       # Pengunci konkurensi siklus hidup graf (Readers/Locks)
│   │       ├── zep_paging.py          # Pengambil simpul dan sisi graf dengan cursor aman
│   │       ├── locale.py              # Sistem translasi lokal backend & injeksi instruksi PUEBI
│   │       └── logger.py              # Konfigurasi logging terstandarisasi konsol & berkas
│   │
│   ├── scripts/                       # Skrip eksekusi otonom & batch runner
│   │   ├── run_parallel_simulation.py # Mesin eksekusi simulasi paralel multi-platform OASIS
│   │   ├── run_twitter_simulation.py  # Skrip simulasi khusus platform Twitter tunggal
│   │   ├── run_reddit_simulation.py   # Skrip simulasi khusus platform Reddit tunggal
│   │   ├── action_logger.py           # Pencatat streaming aksi agen berkinerja tinggi
│   │   ├── test_profile_format.py     # Pengujian validasi skema format profil agen
│   │   └── validate_zep_cloud_integration.py # Skrip verifikasi kontrak API Zep Cloud
│   │
│   └── tests/                         # Rangkaian pengujian unit & integrasi backend
│       ├── test_zep_cloud_contracts.py       # Verifikasi kesesuaian payload SDK Zep Cloud
│       ├── test_zep_cloud_validation_script.py # Pengujian skrip validator Zep
│       ├── test_zep_edge_paging.py           # Pengujian pagination traversal sisi graf
│       ├── test_zep_entity_reader_edges.py   # Pengujian parsing relasi graf entitas
│       ├── test_zep_graph_lifecycle.py       # Pengujian lock siklus pembaca/penulis graf
│       ├── test_zep_graph_memory_updater.py  # Pengujian injeksi aksi ke memori graf
│       ├── test_zep_report_barrier.py        # Pengujian barrier sinkronisasi laporan
│       ├── test_zep_retry_and_client.py      # Pengujian ketahanan retry klien Zep
│       ├── test_zep_simulation_barrier.py    # Pengujian barrier simulasi vs updater
│       ├── test_profile_field_normalization.py# Pengujian konversi tipe data profil agen
│       ├── test_simulation_prepare_failure.py # Pengujian mitigasi error saat persiapan
│       └── test_report_tool_result_sanitizer.py # Pengujian pembersihan hasil alat laporan
│
├── frontend/                          # APLIKASI WEB KLIEN (VUE 3 SPA)
│   ├── index.html                     # Dokumen HTML utama aplikasi
│   ├── package.json                   # Dependensi frontend (Vue, Element Plus, Vis.js, Tailwind)
│   ├── package-lock.json              # Lockfile dependensi frontend
│   ├── vite.config.js                 # Konfigurasi bundler Vite & proksi dev backend
│   │
│   └── src/                           # Kode sumber antarmuka pengguna
│       ├── main.js                    # Titik masuk Vue 3, pemasangan router, i18n, & CSS
│       ├── App.vue                    # Komponen induk tata letak (Root Layout)
│       │
│       ├── api/                       # Klien HTTP Axios pembungkus backend REST
│       │   ├── index.js               # Konfigurasi dasar Axios & penanganan error global
│       │   ├── graph.js               # Pemanggilan API graf (upload, status, ontology)
│       │   ├── simulation.js          # Pemanggilan API simulasi (prepare, start, IPC)
│       │   └── report.js              # Pemanggilan API laporan (generate, chat, streaming)
│       │
│       ├── components/                # Komponen antarmuka per langkah alur kerja
│       │   ├── Step1GraphBuild.vue    # UI Langkah 1: Unggah benih & visualisasi ontologi
│       │   ├── Step2EnvSetup.vue      # UI Langkah 2: Parameterisasi 7-platform & profil
│       │   ├── Step3Simulation.vue    # UI Langkah 3: Pengendalian simulasi & pemantau ronde
│       │   ├── Step4Report.vue        # UI Langkah 4: Tinjauan draf laporan ReACT & ekspor
│       │   ├── Step5Interaction.vue   # UI Langkah 5: Wawancara interaktif agen & ReportAgent
│       │   ├── GraphPanel.vue         # Penampil visual interaktif jejaring simpul-sisi graf
│       │   ├── HistoryDatabase.vue    # Tabel riwayat proyek & tugas simulasi terdahulu
│       │   └── LanguageSwitcher.vue   # Komponen pengalih bahasa (ID / ZH / EN)
│       │
│       ├── i18n/                      # Konfigurasi vue-i18n
│       │   └── index.js               # Pemuat berkas bahasa dinamis dari folder locales/
│       │
│       ├── router/                    # Konfigurasi rute halaman Vue Router
│       │   └── index.js               # Pemetaan path URL ke View Components
│       │
│       ├── store/                     # Manajemen status reaktif Vuex / Pinia-lite
│       │   └── pendingUpload.js       # Buffer status sementara saat unggah berkas
│       │
│       └── views/                     # Halaman tampilan utama aplikasi
│           ├── Home.vue               # Halaman beranda pengantar & peluncuran proyek baru
│           ├── Process.vue            # Halaman panduan wizard langkah 1 sampai 5 terpadu
│           ├── MainView.vue           # Tampilan navigasi kerja utama
│           ├── SimulationView.vue     # Dasbor pemantauan graf dan konfigurasi agen
│           ├── SimulationRunView.vue  # Dasbor visualisasi linimasa interaksi agen real-time
│           ├── ReportView.vue         # Penampil laporan prediksi komprehensif
│           └── InteractionView.vue    # Ruang wawancara mendalam dengan agen digital
│
├── locales/                           # SUMBER DAYA INTERNASIONALISASI BILINGUAL/MULTILINGUAL
│   ├── languages.json                 # Daftar kode bahasa, label UI, & instruksi prompt LLM
│   ├── zh.json                        # Glosarium terjemahan Bahasa Mandarin
│   └── en.json                        # Glosarium terjemahan Bahasa Inggris
│
├── wiki/                              # PUSAT DOKUMENTASI WIKIPEDIA MIROFISH
│   ├── index.md                       # Portal Utama Wikipedia MiroFish
│   ├── arsitektur.md                  # Arsitektur Sistem Menyeluruh & Topologi
│   ├── ekspansi-multi-platform.md     # Spesifikasi 7 Platform Media Sosial
│   ├── riset-web-searxng.md           # Riset Web Terintegrasi Langkah 0 SearXNG
│   ├── kesiapan-operasional.md        # Persistensi, Ketahanan, Checkpoint & 9Router
│   ├── codemap.md                     # Codemap Komprehensif & Matriks Dependensi
│   └── panduan-operasional.md         # Panduan Deployment, Eksekusi, & Pengujian
│
├── scripts/                           # Skrip pemeliharaan repositori tingkat root
│   ├── star_history.py                # Skrip visualisasi riwayat bintang GitHub
│   └── fetch_star_count.py            # Pengambil metrik popularitas repositori
│
└── tests/                             # Pengujian otomasi end-to-end tingkat root
    ├── test_local_star_history.py     # Uji visualisasi bintang lokal
    └── test_local_star_count_fetch.py # Uji pengambilan bintang lokal
```

---

## 2. Matriks Dependensi Antar-Modul Backend

Tabel di bawah ini menggambarkan relasi ketergantungan (siapa memanggil siapa) pada lapisan backend MiroFish:

| Modul Pemanggil (*Caller*) | Modul yang Dipanggil (*Callee / Dependency*) | Tujuan & Peran Fungsional |
| :--- | :--- | :--- |
| `api/graph.py` | `services/ontology_generator.py` | Meminta analisis teks dan perancangan skema ontologi. |
| `api/graph.py` | `services/graph_builder.py` | Menyerahkan episode batch ke Zep Cloud dan polling status. |
| `api/graph.py` | `utils/zep_lifecycle.py` | Mengunci graf saat proses pembangunan/penghapusan berlangsung. |
| `api/simulation.py` | `services/zep_entity_reader.py` | Membaca simpul entitas graf dari Zep untuk bahan persona. |
| `api/simulation.py` | `services/oasis_profile_generator.py`| Menghasilkan profil kepribadian lengkap (OCEAN + bio). |
| `api/simulation.py` | `services/simulation_config_generator.py`| Merumuskan parameter aktivitas agen dan bobot platform. |
| `api/simulation.py` | `services/simulation_runner.py` | Menjalankan subproses simulasi dan memantau status aktif. |
| `api/simulation.py` | `services/simulation_ipc.py` | Mengirim perintah wawancara (*interview*) ke lingkungan agen. |
| `api/report.py` | `services/report_agent.py` | Menginisialisasi siklus ReACT pembuat laporan prediksi. |
| `services/report_agent.py` | `services/zep_tools.py` | Memanggil perkakas investigasi graf (InsightForge, Panorama). |
| `services/report_agent.py` | `services/simulation_ipc.py` | Mewawancarai agen di dalam dunia simulasi saat penulisan draf. |
| `services/simulation_runner.py`| `scripts/run_parallel_simulation.py`| Menjalankan subproses Python mandiri di sistem operasi. |
| `scripts/run_parallel_simulation.py`| `services/zep_graph_memory_updater.py`| Menyuntikkan aksi ronde terbaru ke graf Zep secara langsung. |
| `services/graph_builder.py` | `utils/zep_paging.py` & `utils/zep.py` | Memanggil Zep SDK dengan paginasi aman dan mekanisme retry. |

---

## 3. Alur Data End-to-End Mikro

```
[Materi Benih / Kebutuhan]
          │
          ▼
┌─────────────────────────────────┐
│ 1. Ingesti & Riset Langkah 0    │ ──► Simpan `parsed_text.txt` & `research_summary.md`
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 2. Rekayasa Ontologi & Graf     │ ──► Ekstraksi skema via LLM ──► Batch Ingestion Zep Cloud
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 3. Profiling & Konfigurasi      │ ──► Filter Entitas ──► Ekspor `agent_profiles.json` &
└────────────────┬────────────────┘     `simulation_config.json`
                 │
                 ▼
┌─────────────────────────────────┐
│ 4. Eksekusi Simulasi Paralel    │ ──► Subproses 7-Platform ──► `actions.jsonl`
└────────────────┬────────────────┘     ├── Update Memori Graf (`zep_graph_memory_updater.py`)
                 │                      └── Simpan Checkpoint SHA-256 (`round_X.snap`)
                 ▼
┌─────────────────────────────────┐
│ 5. Analisis ReACT ReportAgent   │ ──► Thought -> Tool Calls -> Outline -> Final Markdown
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 6. Eksplorasi Human-in-the-Loop │ ──► UI Interaksi ──► IPC Command ──► Respon Agen
└─────────────────────────────────┘
```

---

## 4. Peta Kepemilikan Berkas untuk 10 Subagent Pengembang

Untuk memfasilitasi pengembangan terdistribusi berskala besar oleh tim multi-agen AI (*swarm engineering*), kepemilikan kode dibagi secara tegas ke dalam 10 subagent spesialis:

```
+-----------------------------------------------------------------------------------------+
|                    PETA TANGGUNG JAWAB & KEPEMILIKAN 10 SUBAGENT                        |
+---+----------------------+---------------------------------+----------------------------+
| # | KODE & PERAN SUBAGENT| DOMAIN TANGGUNG JAWAB UTAMA     | BERKAS DI BAWAH KONTROL    |
+---+----------------------+---------------------------------+----------------------------+
| 1 | Subagent A: Core API | Routing REST, App Factory, CORS | backend/app/api/, run.py   |
| 2 | Subagent B: Database | Skema ORM, SQLite WAL, Postgres | backend/app/models/        |
| 3 | Subagent C: GraphRAG | Zep Cloud SDK, Ontologi, Paging | services/graph_builder.py  |
| 4 | Subagent D: SimEngine| OASIS 7-Platform, Action Engine | scripts/run_*.py, runner.py|
| 5 | Subagent E: Step0Web | SearXNG, Anti-Injeksi, Skorer   | services/step0_*, parser.py|
| 6 | Subagent F: Analyst  | ReACT ReportAgent, ZepTools     | services/report_agent.py   |
| 7 | Subagent G: Gateway  | 9Router, Failover, Enkripsi AES | utils/crypto.py, llm_*.py  |
| 8 | Subagent H: MCP Eng  | Model Context Protocol Server   | backend/mcp_server.py      |
| 9 | Subagent I: Frontend | Vue 3 SPA, vue-i18n, Visual Vis | frontend/src/, locales/    |
| 10| Subagent J: DevOps   | PM2, Docker, Crash Recovery     | docker-compose*, tests/    |
+---+----------------------+---------------------------------+----------------------------+
```

### 4.1 Rincian Kontrak Tiap Subagent

1. **Subagent A (Core API & Application Framework)**:
   - *Tanggung Jawab*: Menjaga kestabilan *Application Factory* Flask (`backend/app/__init__.py`), konfigurasi environment (`config.py`), dan Blueprint modular (`backend/app/api/`).
   - *Batasan*: Tidak boleh mengubah skema basis data secara langsung tanpa koordinasi dengan Subagent B.
2. **Subagent B (Persistence & Database Architect)**:
   - *Tanggung Jawab*: Mengembangkan dan memelihara model relasional SQLAlchemy (`backend/app/models/entities.py`), mode SQLite WAL, skrip migrasi Alembic, dan integritas transaksi ACID.
3. **Subagent C (GraphRAG & Knowledge Engineer)**:
   - *Tanggung Jawab*: Optimalisasi `graph_builder.py`, `ontology_generator.py`, `zep_entity_reader.py`, serta penanganan konkurensi siklus hidup graf di `utils/zep_lifecycle.py`.
4. **Subagent D (Multi-Platform Simulation Architect)**:
   - *Tanggung Jawab*: Memperluas mesin eksekusi simulasi 7-platform (`backend/scripts/run_parallel_simulation.py`), penanganan sinkronisasi barrier antar-pekerja, serta kalkulasi bobot algoritma umpan.
5. **Subagent E (Step 0 Web Research & Content Shield Specialist)**:
   - *Tanggung Jawab*: Klaster Docker SearXNG, ekstraksi fakta otomatis, perisai anti-prompt injection, dan kalkulator kredibilitas sumber.
6. **Subagent F (ReportAgent & Analytic Reasoning Engineer)**:
   - *Tanggung Jawab*: Mengembangkan kemampuan penalaran ReACT di `backend/app/services/report_agent.py`, toolkit investigasi di `zep_tools.py`, dan kualitas narasi prediktif.
7. **Subagent G (LLM Gateway & Secrets Security Specialist)**:
   - *Tanggung Jawab*: Membangun proxy pintar 9Router, penanganan failover multi-penyedia, pemerataan kuota, dan enkripsi rahasia simetris AES-256-GCM.
8. **Subagent H (MCP Protocol Integration Specialist)**:
   - *Tanggung Jawab*: Mengimplementasikan server terstandarisasi Model Context Protocol agar ekosistem MiroFish dapat dipanggil oleh alat eksternal.
9. **Subagent I (Frontend & Internationalization Engineer)**:
   - *Tanggung Jawab*: Seluruh direktori `frontend/`, implementasi `vue-i18n` Bahasa Indonesia penuh, dan panel visualisasi jejaring simpul graf (`GraphPanel.vue`).
10. **Subagent J (DevOps, Reliability & QA Specialist)**:
    - *Tanggung Jawab*: Konfigurasi PM2 lintas sistem operasi (`ecosystem.config.js`), orkestrasi Docker multi-container, pengujian gerbang pemulihan crash (E1/E2), dan pipeline CI/CD.
