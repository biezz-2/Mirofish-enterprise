---
title: Panduan Deployment, Eksekusi, dan Pengujian Lapangan
type: guide
tags: [deployment, pm2, docker-compose, searxng, api-reference, recovery-testing, v3.1]
related:
  - "[[index]]"
  - "[[arsitektur]]"
  - "[[kesiapan-operasional]]"
  - "[[codemap]]"
sources:
  - docker-compose.yml
  - backend/run.py
  - backend/app/config.py
  - frontend/vite.config.js
---

> 🌐 **Bahasa / Language**: [Bahasa Indonesia](./panduan-operasional.md) | [English](./en/operational-guide.md)

# Panduan Deployment, Eksekusi, dan Pengujian Lapangan: MiroFish v3.1 Enterprise

Dokumen ini merupakan panduan operasional praktis (*runbook*) untuk menginstal, mengonfigurasi, menjalankan, dan menguji platform **MiroFish v3.1** di lingkungan pengembangan lokal maupun peladen produksi lintas sistem operasi (Linux, Windows, macOS).

---

## 1. Prasyarat Sistem & Dependensi Perangkat Lunak

Sebelum memulai instalasi, pastikan sistem operasi Anda telah memenuhi prasyarat berikut:

| Perangkat Lunak | Versi Minimal | Keterangan Verifikasi | Perintah Pengecekan |
| :--- | :--- | :--- | :--- |
| **Node.js** | v18.16.0+ LTS | Eksekusi build frontend & runtime PM2 | `node -v` |
| **npm** | v9.0.0+ | Manajemen paket JavaScript | `npm -v` |
| **Python** | 3.10.x - 3.12.x | Runtime backend Flask & simulasi OASIS | `python3 --version` |
| **UV (Direkomendasikan)**| Terkini | Paket manager Python ultra-cepat | `uv --version` |
| **Docker Engine** | 24.0.0+ | Kontainerisasi SearXNG & Neo4j | `docker --version` |
| **Docker Compose** | v2.20.0+ | Orkestrasi layanan kontainer | `docker compose version` |
| **PM2** | 5.3.0+ | Manajer proses produksi latar belakang | `pm2 -v` |

---

## 2. Manajemen Lingkungan & Konfigurasi (`.env`)

Salin templat konfigurasi dan sesuaikan variabel rahasia pada direktori root repositori:

```bash
cp .env.example .env
```

Isi berkas `.env` dengan kredensial yang valid:

```ini
# ========================================================
# MIROFISH v3.1 ENTERPRISE CONFIGURATION
# ========================================================

# Flask Server Config
SECRET_KEY=mirofish-super-deterministic-enterprise-key-2026
FLASK_DEBUG=False
PORT=5001

# LLM Gateway Config (Mendukung OpenAI / 9Router / vLLM)
LLM_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Zep Cloud Knowledge Graph Config
ZEP_API_KEY=z_cloud_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Step 0 Web Research (SearXNG Private Cluster)
SEARXNG_ENABLED=True
SEARXNG_ENDPOINT=http://127.0.0.1:8888

# OASIS Simulation Parameters
OASIS_DEFAULT_MAX_ROUNDS=10
REPORT_AGENT_MAX_TOOL_CALLS=8
REPORT_AGENT_MAX_REFLECTION_ROUNDS=3
REPORT_AGENT_TEMPERATURE=0.5

# Kriptografi Rahasia & Database
MASTER_APP_SECRET=bf38c71d6f5e4a8b9c2d1e0f3a5b7c9d
DATABASE_URL=sqlite:///backend/app/uploads/mirofish.db
```

---

## 3. Orkestrasi Kontainer: SearXNG & Neo4j (`docker-compose.yml`)

Jalankan klaster pendukung (metasearch SearXNG privat dan basis data graf Neo4j) menggunakan Docker Compose:

```bash
# Jalankan kontainer pendukung di latar belakang
docker compose -f docker-compose.yml up -d
```

Verifikasi bahwa seluruh kontainer telah berstatus *healthy*:
```bash
docker compose ps
```

Hasil verifikasi yang diharapkan:
```
NAME                    IMAGE                   COMMAND                  SERVICE             STATUS
mirofish-searxng        searxng/searxng:latest  "/sbin/tini -- /usr/…"   searxng             Up (healthy) (127.0.0.1:8888->8080/tcp)
mirofish-searxng-redis  redis:7-alpine          "docker-entrypoint.s…"   searxng-redis       Up (healthy)
mirofish-neo4j          neo4j:5.15-community    "tini -g -- /startup…"   neo4j               Up (healthy) (7474/tcp, 7687/tcp)
```

---

## 4. Konfigurasi dan Manajemen Proses Produksi dengan PM2

PM2 digunakan untuk menjamin peladen tetap aktif (*always-on*), melakukan *auto-restart* jika terjadi crash tak terduga, dan menyajikan log terpusat.

### 4.1 Berkas Konfigurasi PM2 (`ecosystem.config.js`)

Buat berkas `ecosystem.config.js` di root repositori:

```javascript
module.exports = {
  apps: [
    {
      name: 'mirofish-backend',
      cwd: './backend',
      script: 'run.py',
      interpreter: 'python3', // Pada Windows, ganti dengan path python.exe virtualenv
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        PYTHONUNBUFFERED: '1',
        FLASK_ENV: 'production',
        PORT: 5001
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      merge_logs: true
    },
    {
      name: 'mirofish-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run preview -- --port 3000 --host 0.0.0.0',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      merge_logs: true
    }
  ]
};
```

### 4.2 Prosedur Eksekusi Lintas Sistem Operasi

#### A. Linux (Ubuntu / Debian / WSL2)
```bash
# 1. Buat direktori logs
mkdir -p logs

# 2. Setup virtual environment Python
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Setup Frontend
cd frontend
npm install
npm run build
cd ..

# 4. Jalankan aplikasi via PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### B. Windows (PowerShell / CMD)
```powershell
# 1. Setup direktori dan venv
mkdir logs
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# 2. Build Frontend
cd frontend
npm install
npm run build
cd ..

# 3. Jalankan PM2 (Pastikan interpreter menunjuk ke python venv)
pm2 start ecosystem.config.js
```

#### C. macOS (Apple Silicon M1/M2/M3 & Intel)
```bash
# Setup sama dengan Linux, pastikan Xcode command line tools terinstal
xcode-select --install
pm2 start ecosystem.config.js
```

Perintah kontrol operasional PM2:
- `pm2 status` : Menampilkan ringkasan status proses.
- `pm2 logs mirofish-backend` : Menampilkan log real-time backend.
- `pm2 restart all` : Merestart seluruh klaster.
- `pm2 stop all` : Menghentikan layanan secara anggun (*graceful stop*).

---

## 5. Katalog Referensi REST API Lengkap

### 5.1 Grup Endpoint Graf Pengetahuan (`/api/graph/*`)
- **`POST /api/graph/upload`**:
  Mengunggah satu atau beberapa dokumen benih (`multipart/form-data`). Mengembalikan `project_id` dan statistik teks.
- **`POST /api/graph/ontology`**:
  Memicu analisis ontologi entitas dan relasi menggunakan LLM berdasarkan teks dokumen.
- **`POST /api/graph/build`**:
  Memulai pengiriman batch dokumen ke Zep Cloud / Neo4j dan mengonstruksi graf secara asinkron. Mengembalikan `task_id`.
- **`GET /api/graph/task/<task_id>`**:
  Memantau persentase kemajuan (*progress percentage*) pembangunan graf pengetahuan.
- **`GET /api/graph/data/<graph_id>`**:
  Mengambil data struktur simpul dan sisi graf lengkap untuk dirender pada komponen `GraphPanel.vue`.

### 5.2 Grup Endpoint Simulasi (`/api/simulation/*`)
- **`GET /api/simulation/entities/<graph_id>`**:
  Membaca dan memfilter entitas dari graf pengetahuan yang layak dijadikan agen sosial.
- **`POST /api/simulation/prepare`**:
  Menghasilkan profil psikologis agen (OCEAN traits) dan konfigurasi parameter 7 platform.
- **`POST /api/simulation/start`**:
  Memulai eksekusi subproses simulasi multi-platform.
- **`GET /api/simulation/status/<simulation_id>`**:
  Mengambil status aktif, nomor ronde terkini, dan metrik interaksi.
- **`POST /api/simulation/pause` & `POST /api/simulation/resume`**:
  Menjeda atau melanjutkan jalannya simulasi sosial.
- **`POST /api/simulation/stop`**:
  Menghentikan simulasi secara anggun dan memindahkan lingkungan ke mode siap wawancara (*interview-ready*).
- **`POST /api/simulation/interview`**:
  Mengirimkan pertanyaan ke agen tertentu via IPC file system dan mengambil jawabannya.

### 5.3 Grup Endpoint Laporan Analisis (`/api/report/*`)
- **`POST /api/report/generate`**:
  Memicu ReportAgent untuk menyusun outline dan mengeksekusi siklus ReACT. Mengembalikan `report_id`.
- **`GET /api/report/status/<report_id>`**:
  Memeriksa kemajuan penulisan per bab dan status penyelesaian laporan.
- **`GET /api/report/get/<report_id>`**:
  Mengambil naskah laporan Markdown final yang lengkap.
- **`GET /api/report/logs/<report_id>`**:
  Mengambil atau melakukan streaming jejak audit penalaran agen (*Thought, Action, Observation*) dari berkas `agent_log.jsonl`.
- **`POST /api/report/chat`**:
  Melakukan percakapan interaktif tanya-jawab dengan ReportAgent mengenai isi laporan.

### 5.4 Grup Endpoint Riset Web Langkah 0 (`/api/research/*`)
- **`POST /api/research/search`**:
  Mengeksekusi pencarian web privat via SearXNG, melakukan sanitasi anti-injeksi, dan mengembalikan fakta berbobot kredibel.

---

## 6. Prosedur Pengujian Gerbang Pemulihan Bukti (*Recovery Proof Gates*)

Untuk memvalidasi kesiapan operasional tingkat enterprise, sistem harus lolos dua gerbang pengujian ketahanan (*reliability gates*):

```
                   GERBANG PENGUJIAN KETAHANAN RESILIENSI
                   
       [ Gerbang E1: Uji Crash Pasca Terminasi Paksa (SIGKILL) ]
       ─────────────────────────────────────────────────────────
       Ronde t Berjalan ──► kill -9 PID ──► Boot Ulang Backend
                                                  │
                                                  ▼
       Verifikasi: Scanner pulihkan Job ke Ronde t via Checkpoint SHA-256
       Lanjutkan ke Ronde t+1 tanpa duplikasi rekaman tindakan!
       
       
       [ Gerbang E2: Uji Partisi Jaringan & Pemadaman Provider ]
       ─────────────────────────────────────────────────────────
       Simulasi Aktif ──► Blokir API LLM ──► 9Router Circuit Breaker
                                                  │
                                                  ▼
       Verifikasi: Rute otomatis dialihkan ke Secondary / Local vLLM
       Batch Zep Retry Drain sukses tanpa menggagalkan simulasi!
```

### 6.1 Gerbang E1: Pengujian Terminasi Paksa Subproses (`kill -9`)
**Tujuan**: Membuktikan bahwa pemadaman mendadak di tengah ronde tidak merusak integritas basis data dan simulasi dapat dilanjutkan dari checkpoint valid terakhir.

**Langkah Pengujian**:
1. Jalankan simulasi dengan 10 ronde:
   ```bash
   curl -X POST http://127.0.0.1:5001/api/simulation/start -H "Content-Type: application/json" \
     -d '{"simulation_id": "sim-test-e1", "project_id": "proj-test"}'
   ```
2. Pantau log hingga simulasi mencapai ronde ke-4:
   ```bash
   tail -f backend/app/uploads/simulations/sim-test-e1/simulation.log
   ```
3. Cari PID proses dan hentikan secara paksa menggunakan sinyal terminasi mutlak:
   ```bash
   kill -9 <PID_SIMULASI>
   ```
4. Restart peladen backend via PM2:
   ```bash
   pm2 restart mirofish-backend
   ```
5. **Kriteria Kelulusan E1**:
   - `CrashRecoveryScanner` mendeteksi bahwa PID telah tiada.
   - Status pekerjaan pada basis data berubah menjadi `paused`.
   - File checkpoint `round_004.snap` diverifikasi cocok dengan `round_004.sha256`.
   - Panggilan API `/api/simulation/resume` berhasil melanjutkan simulasi langsung ke ronde 5 tanpa mengulang ronde 1-4 dan tanpa duplikasi entri di `actions.jsonl`.

### 6.2 Gerbang E2: Pengujian Gangguan Jaringan & Failover Gateway 9Router
**Tujuan**: Membuktikan bahwa fluktuasi jaringan atau pemblokiran kuota LLM dapat ditangani secara transparan tanpa menggagalkan tugas.

**Langkah Pengujian**:
1. Saat simulasi berlangsung, putuskan rute ke endpoint penyedia utama (misal memblokir akses IP OpenAI via `iptables` lokal atau menyetel API Key palsu sementara).
2. Amati respons internal pada log gateway `9router.log`.
3. **Kriteria Kelulusan E2**:
   - Sistem mencatat kegagalan koneksi awal dan mengaktifkan mekanisme *jittered exponential backoff* (3 kali percobaan).
   - Setelah ambang batas kegagalan terlampaui, *Circuit Breaker* membuka sirkuit dan mengalihkan permintaan ke provider cadangan (Anthropic Claude atau model lokal Ollama/vLLM).
   - Seluruh panggilan agen menerima respons valid dan simulasi terus berlanjut hingga selesai tanpa memicu status `FAILED`.
