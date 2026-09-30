---
title: Kesiapan Operasional, Persistensi, dan Ketahanan Sistem
type: concept
tags: [operational-readiness, sqlite-wal, postgresql, crash-recovery, aes-gcm, 9router, mcp-server, v3.1]
related:
  - "[[index]]"
  - "[[arsitektur]]"
  - "[[panduan-operasional]]"
  - "[[codemap]]"
sources:
  - backend/app/models/entities.py
  - backend/app/models/task.py
  - backend/app/models/project.py
  - backend/app/config.py
---

# Kesiapan Operasional, Persistensi, dan Ketahanan Sistem: MiroFish v3.1 Enterprise

Dokumen ini mendokumentasikan spesifikasi ketahanan operasional (*operational readiness and enterprise resilience*) MiroFish v3.1. Lingkungan simulasi sosial berskala besar membutuhkan jaminan integritas data yang kokoh, arsitektur pemulihan kegagalan nir-kehilangan (*zero-loss recovery*), perlindungan rahasia terenkripsi, serta gerbang integrasi protokol terbuka.

---

## 1. Skema Relasional Transaksional (SQLite WAL & PostgreSQL)

Pada versi sebelumnya, status proyek dan tugas disimpan dalam berkas JSON terpisah (`project_state.json`, `run_state.json`) yang rentan terhadap kerusakan data (*file corruption*) apabila sistem mengalami kegagalan daya atau terminasi mendadak. 

MiroFish v3.1 mengimplementasikan lapisan persistensi berbasis **SQLAlchemy ORM** (`backend/app/models/entities.py`) yang mendukung konfigurasi ganda:
- **SQLite dengan Mode Write-Ahead Logging (WAL)**: Standar *out-of-the-box* untuk instalasi mandiri, single-node, dan lingkungan pengembangan. WAL memungkinkan pembacaan berkecepatan tinggi tanpa memblokir penulisan data aksi simulasi yang sangat cepat.
- **PostgreSQL**: Untuk lingkungan produksi berskala klaster (*enterprise multi-instance*).

```
                      +-----------------------------+
                      |        ProjectModel         |
                      | (id, name, desc, created_at)|
                      +--------------+--------------+
                                     │ 1:N
                                     ▼
                      +-----------------------------+
                      |          TaskModel          |
                      | (id, project_id, type, stat)|
                      +--------------+--------------+
                                     │ 1:N
                                     ▼
                      +-----------------------------+
                      |          JobModel           |
                      | (id, task_id, state, pid,   |
                      |  current_round, total_round)|
                      +--------------+--------------+
                                     │ 1:N
                                     ▼
                      +-----------------------------+
                      |       CheckpointModel       |
                      | (id, job_id, round, path,   |
                      |  sha256_hash, created_at)   |
                      +-----------------------------+
```

### 1.1 Tabel Inti Skema Relasional (`backend/app/models/entities.py`)

1. **`projects` (`ProjectModel`)**:
   Menyimpan identitas proyek simulasi, deskripsi naratif, stempel waktu, dan relasi berjenjang (*cascade*) ke seluruh tugas.
2. **`tasks` (`TaskModel`)**:
   Mencatat pekerjaan tingkat tinggi (`graph_build`, `profile_generation`, `simulation_run`, `report_generation`), status terkini, dan parameter JSON.
3. **`jobs` (`JobModel`)**:
   Mencatat unit eksekusi proses sistem operasi aktual. Menyimpan PID proses sub-sistem, nomor ronde aktif (`current_round`), persentase kemajuan (`progress_pct`), dan pesan galat.
4. **`checkpoints` (`CheckpointModel`)**:
   Menyimpan riwayat snapshot kondisi simulasi per ronde virtual lengkap dengan path berkas biner dan hash integritas `sha256_hash`.
5. **`platforms_config` (`PlatformConfigModel`)**:
   Konfigurasi terparameterisasi untuk 7 platform media sosial yang terikat pada sebuah proyek.
6. **`research_reports` (`ResearchReportModel`)**:
   Hasil riset web Langkah 0 SearXNG: ringkasan fakta, entitas terverifikasi, tren, dan skor kredibilitas.
7. **`settings` (`SettingsModel`)**:
   Penyimpanan pasangan kunci-nilai rahasia sistem yang terenkripsi (`value_encrypted`).
8. **`audit_log` (`AuditLogModel`)**:
   Pencatatan jejak audit tak-terhapuskan (*immutable append-only log*) untuk setiap aksi operasional penting yang dilakukan oleh aktor sistem atau pengguna.

---

## 2. Siklus Hidup Mesin Status & State Machine Job WAL

Status eksekusi pada `JobModel` diatur oleh mesin status transaksional:

```
  [QUEUED] ──► [INITIALIZING] ──► [RUNNING] ──► [CHECKPOINTING] ──► [COMPLETED]
                                     │   ▲              │
                            (Pause)  │   │ (Resume)     │
                                     ▼   │              │
                                  [PAUSED]              │
                                     │                  │
                          (Crash / SIGKILL)             │
                                     │                  ▼
                                     ▼          [INTEGRITY_CHECK]
                              [ABNORMAL_EXIT]           │
                                     │                  ▼
                                     ▼          [ROUND_COMMITTED]
                              [RECOVERING] ─────────────┘
```

Setiap transisi status diapit oleh transaksi basis data atomik. Pada SQLite, konfigurasi pragma diaktifkan saat inisialisasi:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

---

## 3. Mekanisme Checkpoint Per-Ronde & Scanner Pemulihan Crash (*Crash Recovery*)

Salah satu ancaman terbesar dalam simulasi sosial multi-ronde berdurasi panjang adalah kegagalan sistem mendadak (*Out Of Memory / OOM*, crash kernel, atau terminasi sinyal OS `SIGKILL`).

### 3.1 Algoritma Checkpointing Per-Ronde
Pada setiap akhir ronde virtual \(R\):
1. **Flushing & Barrier**: Koordinator menunggu seluruh pekerja 7-platform menyelesaikan aksi ronde \(R\).
2. **Serialisasi State**: Keadaan memori internal agen, indeks umpan linimasa, dan antrean pesan diekspor ke berkas snapshot:
   `uploads/simulations/<sim_id>/checkpoints/round_<R>.snap`
3. **Kalkulasi Checksum**: Sistem menghitung hash kriptografi SHA-256 dari berkas snapshot:
   \[
   H = \text{SHA256}(\text{FileBytes})
   \]
4. **Komit Transaksional**: Baris baru dimasukkan ke dalam tabel `checkpoints` dengan atribut `round_number`, `snapshot_path`, dan `sha256_hash`.
5. **Pembaruan Job**: Nilai `current_round` pada tabel `jobs` dinaikkan ke \(R\).

### 3.2 Crash Recovery Scanner Saat Booting Server
Ketika backend MiroFish dinyalakan kembali, sebuah modul pemindai latar belakang (`CrashRecoveryScanner`) dieksekusi secara otomatis:

```python
# backend/app/services/recovery_scanner.py (Logika Algoritma)
import os
import hashlib
from datetime import datetime

def scan_and_recover_orphaned_jobs(db_session):
    orphaned_jobs = db_session.query(JobModel).filter(
        JobModel.state.in_(["running", "checkpointing"])
    ).all()

    for job in orphaned_jobs:
        # Periksa apakah PID OS masih hidup
        pid_alive = is_process_alive(job.pid)
        if not pid_alive:
            logger.warning(f"Terdeteksi job mati mendadak: {job.id} (PID {job.pid})")
            
            # Cari checkpoint valid terakhir
            latest_cp = db_session.query(CheckpointModel).filter_by(job_id=job.id)\
                .order_by(CheckpointModel.round_number.desc()).first()

            if latest_cp and verify_sha256(latest_cp.snapshot_path, latest_cp.sha256_hash):
                job.state = "paused"
                job.current_round = latest_cp.round_number
                job.error_message = f"Crash pulih otomatis pada ronde {latest_cp.round_number} saat booting"
                logger.info(f"Job {job.id} berhasil dipulihkan ke ronde {latest_cp.round_number}")
            else:
                job.state = "failed"
                job.error_message = "Crash tidak dapat dipulihkan: Checkpoint rusak atau tidak ditemukan"
            
            job.updated_at = datetime.utcnow()
            db_session.commit()
```

---

## 4. Manajemen Rahasia & Enkripsi Kredensial AES-GCM

Untuk mematuhi standar keamanan enterprise, kredensial sensitif (kunci API model LLM, token Zep Cloud, kata sandi basis data) tidak disimpan dalam teks polos (*plaintext*).

### 4.1 Mekanisme Kriptografis
- **Algoritma**: AES-256-GCM (*Galois/Counter Mode*) yang menyediakan kerahasiaan (*confidentiality*) dan integritas (*authenticity*) sekaligus.
- **Key Derivation Function**: Master key diturunkan dari variabel lingkungan `MASTER_APP_SECRET` menggunakan PBKDF2-HMAC-SHA256 dengan 100.000 iterasi dan *salt* unik.
- **Penyimpanan**: Nilai terenkripsi disimpan dalam format gabungan Base64:
  `[IV 12-byte] + [Ciphertext] + [Auth Tag 16-byte]` pada tabel `settings`.

```python
# backend/app/utils/crypto.py (Spesifikasi Enkripsi)
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecretVault:
    def __init__(self, master_key_bytes: bytes):
        self.aesgcm = AESGCM(master_key_bytes)

    def encrypt_secret(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt_secret(self, payload_b64: str) -> str:
        raw = base64.b64decode(payload_b64.encode('utf-8'))
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext_bytes.decode('utf-8')
```

---

## 5. Arsitektur Gateway 9Router

Simulasi multi-agen memicu ribuan panggilan LLM dalam rentang waktu singkat. Ketergantungan pada satu penyedia (*single provider*) rentan terhadap *rate-limiting (HTTP 429)* atau gangguan jaringan.

**9Router** bertindak sebagai lapisan proksi cerdas (*intelligent gateway*) di depan lapisan model AI:

```
                  ┌────────────────────────────────────────┐
                  │          Panggilan Agen / LLM          │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │            9Router Gateway             │
                  │  - Circuit Breaker Status Tracker      │
                  │  - Dynamic Quota Load Balancer         │
                  │  - Semantic Response Cache             │
                  └──────┬────────────┬────────────┬───────┘
                         │            │            │
            (Utama)      │    (Fail)  │    (Fail)  │
            ┌────────────┘            │            └────────────┐
            ▼                         ▼                         ▼
  ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
  │  OpenAI Endpoint  │     │ Anthropic / Claude│     │ DeepSeek / Local  │
  │  (gpt-4o / mini)  │     │ (claude-3-5-sonnet│     │ (vLLM / Ollama)   │
  └───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 5.1 Fitur Unggulan 9Router
1. **Automatic Exponential Retry**: Penanganan otomatis terhadap error transien jaringan (status 500, 502, 503, 504, 429) dengan algoritma *jittered exponential backoff*.
2. **Multi-Provider Failover**: Jika kuota provider utama habis atau *circuit breaker* terbuka, rute dialihkan secara transparan ke provider cadangan tanpa menggagalkan simulasi.
3. **Semantic Caching**: Respons aksi deterministik (misalnya format persona atau pengecekan tata bahasa) disimpan dalam cache memori guna memangkas latensi dan biaya token.

---

## 6. Server Model Context Protocol (MCP) Terintegrasi

MiroFish v3.1 menyediakan server berbasis standar **Model Context Protocol (MCP)** terintegrasi, memungkinkan agen AI eksternal (seperti Claude Desktop, Cursor IDE, atau sistem orkestrasi internal perusahaan) berinteraksi dengan ekosistem simulasi secara terstruktur.

### 6.1 Daftar Alat MCP yang Disediakan (`mcp_server.py`)

| Nama Alat MCP | Parameter Masukan | Deskripsi Fungsional |
| :--- | :--- | :--- |
| `run_simulation` | `project_id`, `platforms`, `rounds`, `requirement` | Memicu eksekusi simulasi prediktif baru dan mengembalikan ID pekerjaan. |
| `query_social_graph` | `graph_id`, `query_text`, `limit` | Mengekstrak simpul, keterhubungan entitas, dan memori kolektif dari Zep/Neo4j. |
| `interview_agent` | `simulation_id`, `agent_id`, `question` | Mengirimkan pertanyaan wawancara via IPC langsung ke agen tertentu di dalam dunia simulasi. |
| `get_prediction_report`| `report_id` | Mengambil draf atau naskah lengkap laporan analitik hasil simulasi. |
| `search_step0` | `query`, `categories` | Menjalankan riset web privat SearXNG untuk memverifikasi topik terkini. |
