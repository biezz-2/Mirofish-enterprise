---
title: MiroFish - Swarm Intelligence & Predictive Social Simulation Engine
type: overview
tags: [mirofish, swarm-intelligence, social-simulation, graphrag, multi-platform, v3.1]
sources:
  - ./
  - backend/
  - frontend/
  - locales/
---

# MiroFish: Portal Utama Wikipedia MiroFish (v3.1 Enterprise)

Selamat datang di Dokumentasi Resmi dan Portal Wikipedia Arsitektur **MiroFish**. Dokumen ini merangkum seluruh fondasi teoritis, arsitektur teknis, implementasi kode sumber, spesifikasi multi-platform, riset terintegrasi, ketahanan operasional, serta panduan pengoperasian sistem simulasi kecerdasan kelompok (*swarm intelligence*) terdepan.

---

## 1. Ikhtisar Sistem (Executive Summary)

**MiroFish** adalah mesin simulasi dan prediksi sosial generasi baru berbasis agen otonom cerdas (*multi-agent systems*). Dengan mengekstraksi material informasi benih (*seed information*) dari dunia nyata—seperti berita terkini, draf kebijakan publik, dinamika pasar keuangan, hingga naskah literatur kompleks—MiroFish secara otomatis mengonstruksi sebuah dunia digital paralel berakurasi tinggi (*high-fidelity parallel digital sandbox*).

Di dalam ruang simulasi ini, ratusan hingga ribuan agen cerdas yang memiliki kepribadian independen, memori episodik & semantik jangka panjang (didukung oleh GraphRAG), serta logika tindakan individual, saling berinteraksi secara dinamis. Interaksi mikroskopis antar-agen ini memicu fenomena kemunculan kolektif (*collective emergence*), memungkinkan analis, pembuat kebijakan, dan peneliti untuk merekayasa skenario masa depan, menguji hipotesis "bagaimana jika" (*what-if analysis*), serta memitigasi risiko sosial sebelum terjadi di dunia nyata.

```
                          ┌────────────────────────┐
                          │   Material Benih       │
                          │ (Berita/Data/Kebijakan)│
                          └───────────┬────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │  Langkah 0: Riset Web SearXNG  │
                      │ (Validasi & Pengayaan Kredibel)│
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │   GraphRAG Knowledge Engine    │
                      │  (Zep Cloud / Standalone Graph)│
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ Ekosistem Simulasi 7 Platform  │
                      │ (Twitter, X, Reddit, TikTok,   │
                      │  Instagram, Facebook, Threads) │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │    ReportAgent ReACT Engine    │
                      │  (Wawancara, Analisis & Laporan)│
                      └────────────────────────────────┘
```

---

## 2. Visi dan Filosofi Desain

### 2.1 Menjembatani Makro dan Mikro
1. **Tingkat Makro (Laboratorium Keputusan Nir-Risiko)**: Organisasi pemerintah dan korporasi dapat menguji penerimaan regulasi, respons krisis kehumasan (*PR crisis*), dan volatilitas opini pasar modal di lingkungan pasir tanpa konsekuensi kerugian nyata.
2. **Tingkat Mikro (Ruang Kreasi & Eksplorasi Naratif)**: Peneliti dan kreator dapat melakukan deduksi plot sastra (seperti eksperimen rekonstruksi bagian akhir novel klasik *Dream of the Red Chamber*), pemetaan dinamika komunitas kampus (seperti studi kasus opini Universitas Wuhan), atau eksplorasi sosiologis interaktif.

### 2.2 Prinsip Arsitektur Utama (The Architecture Creed)
- **Data-Driven Parameterization**: Konfigurasi simulasi tidak dibangun atas dasar tebakan acak, melainkan diturunkan secara deterministik dari analisis graf entitas dan pengayaan data faktual.
- **Strict Isolation & Idempotency**: Setiap run simulasi memiliki ruang penyimpanan independen yang terisolasi, checkpoint per-ronde, dan kemampuan pemulihan pasca-kegagalan (*crash recovery*).
- **Anti-Hallucination & Content Shielding**: Seluruh data eksternal dari web metasearch disaring melalui lapisan sanitasi anti-prompt injection sebelum menyentuh memori agen atau basis graf.
- **Penuh Bahasa Indonesia (PUEBI Compliant)**: Antarmuka, instruksi kognitif agen, eksepsi sistem, hingga laporan akhir disesuaikan secara natif untuk ekosistem Bahasa Indonesia tanpa kehilangan kapabilitas multibahasa.

---

## 3. Garis Waktu Evolusi: Menuju Arsitektur v3.1 Enterprise

MiroFish berevolusi secara signifikan dari purwarupa eksperimental hingga platform simulasi siap-produksi kelas industri:

| Dimensi Arsitektur | MiroFish v1.0 / v2.0 (Warisan) | MiroFish v3.1 Enterprise (Arsitektur Terkini) |
| :--- | :--- | :--- |
| **Dukungan Platform** | Terbatas pada Twitter & Reddit (skrip OASIS dual-platform). | **Ekspansi 7 Platform**: Twitter, X, Reddit, TikTok, Instagram, Facebook, Threads dengan profil algoritma distingtif. |
| **Injeksi Fakta Awal** | Mengandalkan berkas dokumen unggahan pengguna statis. | **Riset Web Terintegrasi Langkah 0**: Metasearch privat via SearXNG self-hosted dengan penilaian kredibilitas & anti-injeksi. |
| **Penyimpanan State** | Berkas JSON lokal & in-memory dictionary volatile. | **SQLite WAL Transaksional / PostgreSQL**: Skema relasional ACID lengkap, checkpoint per-ronde, dan recovery scanner. |
| **Ketahanan Proses** | Rentan hilang progres jika proses latar mati mendadak. | **Crash Recovery Scanner Otomatis**: Melanjutkan simulasi dari checkpoint terakhir (\(R_{last}\)) tanpa kehilangan histori. |
| **Gateway LLM** | Pemanggilan langsung tunggal ke OpenAI API. | **9Router Intelligent Gateway**: Failover multi-provider (Anthropic, DeepSeek, vLLM), kuota dinamis, enkripsi rahasia AES-GCM. |
| **Ekosistem & Integrasi** | API REST terisolasi untuk dashboard web internal. | **Dukungan Protokol MCP (Model Context Protocol)**: MiroFish bertindak sebagai MCP Server terstandarisasi untuk ekosistem AI eksternal. |
| **Lokalisasi** | Dominan Bahasa Mandarin & Inggris. | **Lokalisasi Menyeluruh Bahasa Indonesia**: UI `vue-i18n`, panduan persona PUEBI baku, pesan error backend terstandardisasi. |
| **Orkes & Deployment** | Eksekusi manual skrip Python ad-hoc. | **PM2 Multi-Platform Process Manager & Docker Compose Multi-Service** (Neo4j, SearXNG, Backend, Frontend). |

---

## 4. Komponen Inti Sistem

1. **GraphRAG Builder & Zep Cloud Integration (`backend/app/services/graph_builder.py`)**:
   Mengekstraksi ontologi entitas dan relasi secara otomatis menggunakan LLM, lalu membangun Standalone Knowledge Graph berkinerja tinggi di Zep Cloud via Batch Ingestion API berorientasi episode.
2. **OASIS Profile & Config Generator (`backend/app/services/oasis_profile_generator.py` & `simulation_config_generator.py`)**:
   Mengonversi simpul entitas graf menjadi profil psikologis agen OASIS lengkap (nama, bio, kepribadian OCEAN, kecenderungan afektif, dan bobot aktivitas temporal).
3. **Multi-Platform Simulation Runner (`backend/scripts/run_parallel_simulation.py` & `simulation_runner.py`)**:
   Mengorkestrasi eksekusi simulasi paralel multi-ronde, memantau aksi posting/komentar/repost, memperbarui memori graf temporal secara langsung, dan mengekspor log aksi terstruktur (`actions.jsonl`).
4. **ReportAgent Engine (`backend/app/services/report_agent.py`)**:
   Agen analis otonom berbasis kerangka ReACT (*Reasoning + Acting*) yang membedah hasil simulasi menggunakan instrumen investigasi (InsightForge, Panorama, Search, dan Wawancara Langsung ke Agen) untuk menghasilkan laporan prediksi komprehensif.
5. **Interactive Interview Subsystem (`backend/app/services/simulation_ipc.py`)**:
   Mekanisme komunikasi antarmuka (*IPC*) berbasis berkas transaksional yang memungkinkan pengguna atau ReportAgent mewawancarai karakter agen mana pun di dalam dunia simulasi secara langsung.
6. **Frontend Web Modern (`frontend/`)**:
   Antarmuka berbasis Vue 3, Vite, TailwindCSS, dan Element Plus dengan visualisasi graf interaktif (GraphPanel), dashboard pemantauan aksi real-time, dan pengalih bahasa dinamis.

---

## 5. Indeks dan Panduan Navigasi Dokumentasi Wiki

Untuk menyelami detail teknis MiroFish v3.1, silakan merujuk pada bab-bab dokumentasi berikut:

* **[[arsitektur]] - Arsitektur Sistem Menyeluruh**:
  Membedah komparasi lapisan sistem eksisting vs target v3.1, diagram alur data hulu-ke-hilir, topologi layanan, dan strategi pemartisian data (*data partitioning*).
* **[[ekspansi-multi-platform]] - Spesifikasi 7 Platform Media Sosial**:
  Rincian karakteristik matematis, bobot algoritma (recency, popularity, echo chamber, threshold viralitas), ruang tindakan (*action space*), dan profil psikologis agen untuk Twitter, X, Reddit, TikTok, Instagram, Facebook, dan Threads.
* **[[riset-web-searxng]] - Riset Web Langkah 0 Berbasis SearXNG**:
  Arsitektur metasearch engine privat, integrasi Docker self-hosted, ekstraksi fakta & entitas dinamis, algoritma skor kredibilitas sumber, dan perisai anti-prompt injection.
* **[[kesiapan-operasional]] - Persistensi, Ketahanan, dan Infrastruktur**:
  Model data SQLAlchemy ACID, mekanisme state machine WAL, teknik checkpoint berkas ronde & recovery scanner, enkripsi kredensial AES-GCM, 9Router Gateway, dan Server MCP MiroFish.
* **[[codemap]] - Peta Kode Komprehensif (Comprehensive Codemap)**:
  Struktur pohon repositori berkas demi berkas, matriks dependensi antar-modul, alur data *end-to-end* mikro, dan peta kepemilikan berkas untuk 10 subagent tim pengembang.
* **[[panduan-operasional]] - Panduan Deployment, Eksekusi, dan Pengujian**:
  Langkah instalasi dan eksekusi produksi menggunakan PM2 (Linux/Windows/macOS), orkestrasi Docker Compose (SearXNG + Neo4j), referensi katalog REST API, dan pengujian gerbang pemulihan crash E1/E2.

---

## 6. Glosarium Istilah Teknis

* **Swarm Intelligence**: Kemunculan pola kecerdasan atau perilaku kolektif yang rumit dari interaksi agen-agen sederhana yang mengikuti seperangkat aturan lokal.
* **GraphRAG**: Pendekatan *Retrieval-Augmented Generation* yang memanfaatkan struktur graf pengetahuan (entitas dan keterhubungan semantik) untuk memperkaya konteks penalaran LLM.
* **Standalone Graph**: Graf pengetahuan independen dalam klaster Zep Cloud yang didedikasikan untuk satu sesi proyek simulasi tanpa interferensi memori global.
* **Episode Batch Ingestion**: Pola pengiriman data teks terfragmentasi ke Zep API dalam satu kelompok transaksi terverifikasi untuk membentuk simpul (*nodes*) dan sisi (*edges*).
* **OASIS Platform**: Mesin eksekusi simulasi agen sosial yang menyimulasikan umpan linimasa, aksi interaksi sosial, dan perputaran waktu virtual.
* **ReACT Pattern**: Paradigma penalaran LLM yang menggabungkan siklus *Thought* (Penalaran), *Action* (Pemanggilan Alat), dan *Observation* (Hasil Pengamatan) secara berulang.
* **Langkah 0 (Step 0)**: Tahap prapemrosesan opsional namun krusial di mana sistem melakukan penjelajahan fakta web eksternal untuk melengkapi data benih pengguna sebelum graf diinisialisasi.
* **IPC (Inter-Process Communication)**: Protokol pertukaran pesan berbasis berkas perintah (`commands/`) dan berkas respons (`responses/`) antara API Flask dan skrip lingkungan simulasi OASIS.
* **WAL (Write-Ahead Logging)**: Mode operasi basis data SQLite yang memungkinkan konkurensi pembacaan tinggi tanpa memblokir penulisan transaksional saat simulasi berlangsung cepat.
* **9Router**: Lapisan proksi pintar gateway LLM yang mengelola kegagalan koneksi (*failover*), kuota permintaan, dan pemerataan beban (*load balancing*) ke berbagai penyedia model AI.
