# Rencana Komprehensif: Migrasi Database MiroFish ke Supabase PostgreSQL

## 1. Executive Summary & Objective
MiroFish saat ini mengalami fragmentasi penyimpanan data:
- Database relasional SQLite (`mirofish.db`) hanya memuat tabel kosong untuk jobs/checkpoints/reports.
- Metadata proyek (`ProjectManager`) disimpan terpisah dalam file JSON di filesystem (`uploads/projects/{project_id}/project.json`).
- Status task antrean (`TaskManager`) disimpan dalam memori RAM (`dict`), sehingga hilang seketika saat service backend restart.
- Simulator OASIS menulis data interaksi sosial langsung ke SQLite per simulasi (`uploads/simulations/{id}/*.db`).

Tujuan migrasi ini adalah **mengkonsolidasikan seluruh resource database MiroFish ke dalam satu ruang lingkup terpadu di instance Supabase PostgreSQL lokal (`supabase-db`)**. Dengan ini, seluruh state proyek, task, job, konfigurasi, dan laporan tersimpan terpusat, ACID-compliant, persisten saat restart PM2, serta dapat diinspeksi secara langsung via Supabase Studio dan SQL Editor.

---

## 2. Success Criteria (Kriteria Keberhasilan)
1. **Konektivitas Database**: Engine SQLAlchemy MiroFish terhubung stabil ke instance Supabase PostgreSQL lokal (`postgresql+psycopg://...`) melalui port 5432.
2. **Integritas Skema Terpadu**: Tabel skema `projects`, `tasks`, `jobs`, `checkpoints`, `platforms_config`, `research_reports`, `settings`, `audit_log`, dan tabel pelengkap dibuat di Supabase dengan tipe data PostgreSQL modern (JSONB, TIMESTAMP WITH TIME ZONE, UUID/VARCHAR primary keys).
3. **Data Migrated & Intact**: Seluruh data proyek yang ada di direktori `uploads/projects/` berhasil di-ETL ke tabel `projects` di Supabase tanpa kehilangan metadata file, ontologi, atau status.
4. **Backend Resiliency**: `TaskManager` dan `ProjectManager` terintegrasi dengan database Supabase, mempertahankan state task secara persisten meskipun PM2 backend di-restart.
5. **Zero Regression**: Endpoint API frontend (`/api/graph/*`, `/api/simulation/*`, `/api/task/*`) tetap berfungsi 100% kompatibel tanpa error runtime.

---

## 3. Scope & Non-Scope
### In-Scope:
- Analisis dependensi dan skema SQLite vs PostgreSQL Supabase.
- Penyusunan DDL migration script (PostgreSQL-compatible) dan eksekusi pada database Supabase `postgres`.
- Penulisan script ETL (`migrate_sqlite_and_files_to_supabase.py`) untuk memindahkan data dari file JSON & SQLite ke Supabase.
- Instalasi driver `psycopg[binary]` di virtual environment backend MiroFish (`backend/.venv`).
- Refactoring `db_session.py`, `config.py`, `entities.py`, `project.py`, dan `task.py` agar sinkron dengan database Supabase.
- Pembaruan konfigurasi environment di `.env` dan `ecosystem.config.js`.
- Pengujian validasi gate (V1 - V8) dan verifikasi fungsionalitas API.

### Non-Scope:
- Mengubah internal core LLM workflow atau algoritma CAMEL OASIS simulator.
- Memindahkan file biner mentah (PDF/DOCX) dari disk lokal ke Supabase S3 Storage (disimpan sebagai referensi path di DB; dapat dijadikan fase perluasan mendatang).

---

## 4. Phase Breakdown (Tahapan Migrasi)

### Phase 1: Analisis Skema & Fragmentasi Data MiroFish
- **Status**: `IMPLEMENTED` (Awaiting Validation)
- **Goal**: Memetakan seluruh sumber data yang tersebar di backend MiroFish (SQLite `mirofish.db`, flat JSON files di `uploads/projects`, memory dict di `TaskManager`, serta simulation sqlite).
- **Deliverables**: Laporan audit arsitektur data MiroFish & pemetaan relasi entity.
- **Risk**: Rendah (Read-only analysis).

### Phase 2: Desain Skema Terpadu Supabase PostgreSQL & Extensions
- **Status**: `BACKLOG`
- **Goal**: Merancang skema DDL PostgreSQL terpadu di Supabase yang mencakup seluruh atribut proyek, riwayat task, dan jobs.
- **Deliverables**:
  - Script SQL DDL (`backend/scripts/supabase_schema.sql`).
  - Definisi tabel dengan dukungan JSONB untuk `ontology`, `analysis_summary`, `metadata`, dan `progress_detail`.
  - Eksekusi DDL ke container `supabase-db`.
- **Acceptance Criteria**: Seluruh tabel berhasil dibuat di database Supabase dengan skema yang tepat.
- **Risk**: Rendah.

### Phase 3: Migrasi Skema & ETL Data (SQLite + Files -> Supabase)
- **Status**: `BACKLOG`
- **Goal**: Mengimpor data historis proyek dari filesystem (`uploads/projects/proj_*/project.json`) dan SQLite ke Supabase.
- **Deliverables**:
  - Script ETL migrasi Python teruji (`backend/scripts/migrate_to_supabase.py`).
  - Log keberhasilan migrasi record proyek yang ada.
- **Acceptance Criteria**: Semua project yang terdaftar di filesystem terdaftar di tabel `projects` Supabase dengan status dan field yang identik.
- **Risk**: Sedang (Data parsing & integrity).

### Phase 4: Integrasi Backend MiroFish (Driver, ORM & Config)
- **Status**: `BACKLOG`
- **Goal**: Memasang driver database PostgreSQL dan mengonfigurasi backend MiroFish agar menggunakan Supabase PostgreSQL.
- **Deliverables**:
  - Driver `psycopg[binary]` terpasang di `.venv`.
  - Update `backend/app/config.py` dan `backend/app/models/db_session.py` untuk connection pooling PostgreSQL.
  - Update `ProjectManager` & `TaskManager` agar memanfaatkan database Supabase secara transparan dengan fallback cache.
  - Update `ecosystem.config.js` dan `.env` dengan `DATABASE_URI` mengarah ke Supabase `localhost:5432/postgres`.
- **Acceptance Criteria**: Backend MiroFish dapat start dengan `DATABASE_URI` PostgreSQL Supabase dan melakukan query CRUD tanpa exception.
- **Risk**: Sedang (ORM compatibility).

### Phase 5: Validasi Phase-Gate V1-V8, Testing Endpoint & Rollout PM2
- **Status**: `BACKLOG`
- **Goal**: Menjalankan checklist validasi independen (V1-V8), testing API endpoint, dan reload PM2.
- **Deliverables**:
  - Laporan validasi komprehensif (Appendix B format).
  - Verifikasi response endpoint MiroFish di PM2.
- **Acceptance Criteria**: PM2 service `mirofish-backend` restart bersih, health check OK, status task persisten.
- **Risk**: Sedang (Downtime saat restart).

---

## 5. Validation Plan per Phase (Checklist V1–V8)
- **V1 (Spec Completeness)**: Memastikan seluruh model data (`Project`, `Task`, `Job`, `Report`) terakomodasi di PostgreSQL.
- **V2 (Logic Correctness)**: Menjalankan test script untuk operasi create/read/update project dan task di Supabase.
- **V3 (Security & Permissions)**: Memastikan kredensial database disimpan di `.env`, tidak ada hardcoded credentials di kode, dan connection string diredaksi dalam log.
- **V4 (Standards & Compatibility)**: Memeriksa kompatibilitas SQLAlchemy 2.1.4 dengan dialek PostgreSQL `postgresql+psycopg://` via psycopg 3.
- **V5 (Performance & Resource)**: Memastikan connection pool dikonfigurasi (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`) untuk mencegah connection leak di Supabase/Supavisor.
- **V6 (Regression Check)**: Memastikan backward compatibility jika ada fungsi yang masih membaca file lokal (metode fallback aman).
- **V7 (Code Quality)**: Kode bersih, logging terstruktur, error handling transaksional.
- **V8 (Handoff & Docs)**: Dokumentasi connection string, schema migration, dan petunjuk operasional.

---

## 6. Board & Cron Automation Plan
- **Board Registry**:
  - Master Board: `project-mirofish-supabase-migration` (Status: ACTIVE).
  - Cards: `c-mig-01` s/d `c-mig-05`.
  - LangGraph Memory Board ID: `board-1792047362103`.
- **Audit Cron**:
  - `audit:project-daily`: Memeriksa kesehatan koneksi database Supabase dan status service backend di PM2.

---

## 7. Risk Register & Mitigasi
1. **Risiko Koneksi Pooler / PostgreSQL Timeout**:
   - *Mitigasi*: Gunakan direct port 5432 ke Supabase PostgreSQL dengan konfigurasi `pool_pre_ping=True` dan `pool_recycle=3600`.
2. **Risiko Ketidakcocokan Tipe Data JSON**:
   - *Mitigasi*: Manfaatkan kolom native `JSONB` PostgreSQL di SQLAlchemy (`from sqlalchemy.dialects.postgresql import JSONB`) dengan fallback ke `JSON` standar.
3. **Risiko Service Interruption**:
   - *Mitigasi*: Lakukan backup snapshot file `uploads/` dan database sebelum melakukan reload PM2.
