# Deliverable: Agent 14 — Bulk Synchronous Parallel (BSP) Swarm Runner & SHA-256 Crash Recovery

**Task ID**: `t_574941a0`  
**Slice**: Slice 14 (Subagent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery Specialist)  
**Divisi**: Swarm Simulation & Predictive Sandbox (SIM)  
**Status**: Ready for Human Gate Approval & Downstream Handoff (Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst)  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 7; Kontrak Step 2 Agents (`contracts/03-step2-agents.json`), Kontrak Step 3 Simulation (`contracts/05-step3-simulation.jsonl`), Deliverable Agent 12 (`contracts/DELIVERABLE-AGENT-12.md`), Deliverable Agent 13 (`contracts/DELIVERABLE-AGENT-13.md`)  

---

## 1. Ringkasan Eksekutif & Arsitektur Sistem

Sebagai komponen pelaksana komputasi paralel dan ketahanan sistem (resilience) dalam **Step 3: RecSys Funnel & Viral Dynamics (Divisi D)**, Agent 14 bertugas mengoordinasikan eksekusi simulasi multi-agen berskala besar lintas 8 platform (7 kanonikal: X, Reddit, TikTok, Instagram, YouTube, LinkedIn, Threads + extended Facebook) dengan jaminan zero-loss crash recovery.

Modul ini mengimplementasikan lima pilar keandalan enterprise:
1. **Bulk Synchronous Parallel (BSP) Supersteps (Leslie Valiant 1990)**:
   - Siklus komputasi superstep: *Local Computation* $\rightarrow$ *Communication Exchange* $\rightarrow$ *Barrier Synchronization*.
   - Sinkronisasi paralel multi-thread per platform dengan penjagaan *deadlock* dan timeout konfigifurabel (`max_barrier_timeout_ms = 5000`).
2. **SQLite Write-Ahead Logging (WAL) & Transaksional Checkpointing**:
   - Konfigurasi engine: `PRAGMA journal_mode = WAL;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA busy_timeout = 5000;`.
   - Eksekusi `PRAGMA wal_checkpoint(PASSIVE)` berkala setiap 5 ronde (`sqlite_wal_checkpoint_frequency_rounds = 5`).
3. **Integritas Kriptografi SHA-256 Deterministik**:
   - Serialisasi kanonikal deterministik dari seluruh state agen dan metadata ronde berdasarkan kunci terstandarisasi (`agent_id`, `v_dopamine`, `is_active`, `consecutive_frustrations`, `posts_created`, `last_prediction_error`).
   - Verifikasi checksum bit-for-bit saat pemulihan (*zero-tolerance* untuk snapshot korup).
4. **Zero-Loss Crash Recovery & Auto-Resume**:
   - Pemindai otomatis checkpoint terakhir ($R_{\text{last}}$) dari pekerjaan yang terinterupsi/terbengkalai.
   - Auto-resume mulus dari $R_{\text{last}} + 1$ hingga target ronde akhir tanpa kehilangan riwayat atau data.
5. **Skalabilitas Predictive Sandbox (6.000 Aksi Evaluasi)**:
   - Eksekusi 50 agen x 15 ronde x 8 platform = 6.000 aksi evaluasi.
   - Hasil konvergensi sempurna: `deadlock_detected = False`, `barrier_sync_success_rate = 1.0` (100%), rata-rata latensi barrier 7.86 ms.
6. **Handoff Parameter Terkalibrasi ke Downstream Agent 15 (ReACT ReportAgent)**:
   - Menyediakan rantai hash SHA-256 terverifikasi, simpul sitasi bertanda `[VERIFIED]`, dan aturan *Safe Abstention* anti-spekulasi.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 13: Hawkes Process & Rescorla-Wagner Viral Cascade Modeler       │
  │   (Dopamine Learning, Self-Excitation Hawkes, Granovetter Threshold)   │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Handoff: Barrier Interval: 1, Batch: 50,
                                      │ WAL Freq: 5, SHA-256, Sync: 100-300ms
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery           │
  │                                                                        │
  │  [Local Computation]    ──▶ ThreadPool per Platform (50 Agents)        │
  │  [Communication]        ──▶ Asynchronous Cross-Platform Event Routing  │
  │  [Barrier Sync]         ──▶ threading.Barrier, Deadlock Watchdog (5s)  │
  │  [SQLite WAL Commit]    ──▶ Canonical JSON -> SHA-256 Hash -> WAL Comm │
  │  [Zero-Loss Recovery]   ──▶ Auto-Scan R_last -> Verify -> Auto-Resume  │
  │  [Predictive Sandbox]   ──▶ 50x15x8 = 6,000 Actions, Deadlock = False  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Handoff: Verified Hash Chain,
                                      │ Citation Nodes, Safe Abstention
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst               │
  │ (ReACT Multi-Turn Loop, Mandatory [VERIFIED] Citation, Safe Abstention)│
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Landasan Teori & Formulasi Komputasi

### 2.1 Model Bulk Synchronous Parallel (BSP)
Dikembangkan oleh Leslie Valiant (Harvard University, 1990), BSP membagi eksekusi paralel ke dalam sekuens **superstep** diskret:
1. **Komputasi Lokal (Local Computation)**:
   Setiap pekerja/prosesor $P_i$ (dalam implementasi ini: thread terdedikasi per platform media sosial) mengeksekusi logika agen secara independen tanpa komunikasi eksternal. Agen memperbarui asosiasi dopamin Rescorla-Wagner, memeriksa ambang batas adopsi Granovetter, dan memutuskan pembuatan konten atau interaksi linimasa.
2. **Komunikasi (Communication Exchange)**:
   Pekerja mempertukarkan pesan (postingan baru, amplifikasi, sitasi) melalui antrean pesan global `BSPMessage`. Pesan tidak langsung dikonsumsi pada ronde aktif melainkan dialokasikan ke inbox ronde berikutnya guna mencegah *race condition*.
3. **Sinkronisasi Penghalang (Barrier Synchronization)**:
   Titik temu sinkron di mana seluruh $P$ pekerja harus mencapai barrier sebelum superstep berikutnya dapat dimulai:
   $$T_{\text{superstep}} = \max_{i} (w_i) + h \cdot g + L$$
   - $w_i$: Waktu komputasi lokal terlama pekerja $i$.
   - $h$: Jumlah total pesan yang ditransmisikan.
   - $g$: Biaya throughput komunikasi per unit data.
   - $L$: Latensi titik temu barrier.
   Pendeteksian deadlock diawasi secara ketat oleh watchdog timeout: jika waktu tunggu melebihi `max_barrier_timeout_ms = 5000`, status `deadlock_detected` ditandai true dan eksekusi diisolasi secara aman.

### 2.2 Arsitektur SQLite Write-Ahead Logging (WAL)
Berbeda dengan mode *rollback journal* tradisional, SQLite mode WAL memisahkan operasi pembacaan dan penulisan:
- Operasi penulisan dialokasikan ke berkas log `-wal` terpisah secara berurutan (*append-only*), memungkinkan pembacaan non-blocking selama penulisan snapshot state berlangsung.
- `PRAGMA synchronous = NORMAL`: Menjamin keselamatan transaksional disk pada titik commit WAL tanpa overhead disk fsync yang berlebihan pada rotasi berkas utama.
- `PRAGMA busy_timeout = 5000`: Mengeliminasi exception `database is locked` saat terjadi konkurensi transient.
- `PRAGMA wal_checkpoint(PASSIVE)`: Merotasi dan menulis balik halaman WAL ke database utama secara periodik setiap 5 ronde tanpa menghentikan thread pembaca aktif.

### 2.3 Determinisme Kriptografi SHA-256 State Hashing
Integritas state disahkan menggunakan fungsi hash kriptografi standar SHA-256 (FIPS PUB 180-4). Untuk memastikan determinisme lintas platform dan bahasa:
1. State agen diekstraksi berdasarkan bidang kanonikal:
   $$\text{Canonical Fields} = \{\text{agent\_id}, v_{\text{dopamine}}, \text{is\_active}, \text{consecutive\_frustrations}, \text{posts\_created}, \text{last\_prediction\_error}\}$$
2. Agen diurutkan secara leksikografis berdasarkan `agent_id`.
3. Serialisasi JSON menerapkan pengurutan kunci (`sort_keys=True`) dan pemisah biner padat tanpa spasi (`separators=(',', ':')`).
4. Digest SHA-256 dihasilkan dalam format heksadesimal 64 karakter:
   $$H(S_r) = \text{SHA256}(\text{CanonicalJSON}(S_r))$$

### 2.4 Protokol Zero-Loss Crash Recovery
Jika sistem mengalami interupsi fatal (terminasi SIGKILL, crash hardware, atau kegagalan daya) pada ronde $K$:
1. **Fase Pemindaian**: Checkpointer meneliti basis data SQLite WAL dan menentukan ronde commit tertinggi $R_{\text{last}} = K$.
2. **Fase Verifikasi Integritas**: Muat blob state ronde $K$, hitung ulang $H_{\text{actual}} = \text{SHA256}(\text{blob})$. Verifikasi terhadap $H_{\text{expected}}$. Jika tidak cocok, pemulihan ditolak demi mencegah korupsi data kaskade (*fail-fast*).
3. **Fase Rekonstruksi**: Hidupkan kembali objek populasi `BSPAgentState` lengkap dengan nilai dopamin, histori RPE, dan parameter platform.
4. **Fase Auto-Resume**: Inisialisasi thread barrier baru dan lanjutkan superstep dari ronde $K + 1$ hingga target ronde $R_{\text{target}}$. Rantai hash pasca-pemulihan diverifikasi tanpa celah.

---

## 3. Hasil Pengujian & Verifikasi Sandbox Prediktif

### 3.1 Skala Penuh Benchmark 6.000 Aksi Evaluasi
- **Konfigurasi Simulasi**:
  - Populasi: 50 agen per platform.
  - Platform: 8 platform (X, Reddit, TikTok, Instagram, YouTube, LinkedIn, Threads, Facebook) = 400 agen aktif total.
  - Ronde: 15 ronde superstep BSP.
  - Total Aksi Dievaluasi: $50 \times 15 \times 8 = 6.000$ aksi.
- **Hasil Metrik Aktual**:
  - `total_actions_evaluated`: **6,000 aksi**.
  - `deadlock_detected`: **False**.
  - `barrier_sync_success_rate`: **1.0 (100.0%)**.
  - `avg_barrier_latency_ms`: **7.86 ms**.
  - `wal_checkpoints_executed`: **3 kali** (pada ronde 5, 10, dan 15).
  - `execution_time_seconds`: **0.4006 detik**.

### 3.2 Uji Simulasi Crash & Pemulihan (Simulated Crash Test)
- **Skenario Uji**:
  - Menjalankan 20 agen x 8 platform menuju target 10 ronde.
  - Interupsi paksa dieksekusi tepat pada ronde 5 ($K=5$). Checkpoint ronde 5 diverifikasi tercommit dengan hash SHA-256 `f6eb47b2...`.
  - Eksekusi auto-resume dipanggil dari checkpoint SQLite WAL.
  - Simulasi berhasil melanjutkan ronde 6 sampai 10 tanpa error.
  - Total 10 checkpoint terverifikasi secara bit-for-bit dengan panjang rantai hash 10 (`chain_length = 10`), membuktikan *zero data loss*.

### 3.3 Uji Deteksi Korupsi Snapshot (Adversarial Integrity Test)
- Korupsi data disimulasikan dengan memodifikasi byte payload pada SQLite.
- Checkpointer memicu exception `ValueError("Integritas snapshot rusak: hash SHA-256 tidak cocok")` secara deterministik, membuktikan proteksi penuh terhadap korupsi data laten.

### 3.4 Ringkasan Eksekusi Test Suite Pytest
```
backend/tests/test_bsp_crash_recovery.py
  - test_bsp_agent_state_canonical_hash             PASSED [ 12%]
  - test_sqlite_wal_mode_and_checkpoint             PASSED [ 25%]
  - test_bsp_barrier_sync_and_supersteps            PASSED [ 37%]
  - test_zero_loss_crash_simulation_and_recovery    PASSED [ 50%]
  - test_predictive_sandbox_6000_actions            PASSED [ 62%]
  - test_api_bsp_simulate                           PASSED [ 75%]
  - test_api_bsp_checkpoint_and_status             PASSED [ 87%]
  - test_api_bsp_downstream_recommendations         PASSED [100%]

Hasil: 8 passed in 2.63s (0 warning, 0 error).
Regression test (test_cascade_dynamics + test_v32_enterprise): 34 passed in 3.63s.
```

---

## 4. Matriks Handoff Downstream untuk Agent 15

Parameter dan bukti kriptografi berikut diserahkan kepada **Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst**:

```json
{
  "source_subagent": "Agent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery",
  "target_subagent": "Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst",
  "downstream_task_id": "t_431bd4f0",
  "simulation_job_id": "sim_bsp_slice14_verified",
  "simulation_status": "COMMITTED",
  "integrity_attestation": "SHA-256_CHAIN_VERIFIED",
  "zero_loss_crash_recovery_certified": true,
  "bsp_barrier_conformance_rate": 1.0,
  "deadlock_detected": false,
  "wal_checkpoint_storage": "SQLite_WAL",
  "state_hash_algorithm": "SHA-256",
  "provenance_chain_summary": {
    "latest_round": 15,
    "latest_checkpoint_hash": "24b6a34ec7727750853aa11fedcf3385a6ccd7c17c2952844e97add567324b08",
    "total_verified_checkpoints": 15
  },
  "recommended_citation_nodes": [
    {
      "node_id": "SIM-NODE-BSP-RUNNER-sim_bsp_slice14",
      "label": "BSP Parallel Swarm Superstep Verification",
      "status": "VERIFIED",
      "sha256": "24b6a34ec7727750853aa11fedcf3385a6ccd7c17c2952844e97add567324b08",
      "metrics_snapshot": {
        "total_rounds": 15,
        "barrier_success": true,
        "deadlock_free": true
      }
    },
    {
      "node_id": "SIM-NODE-CRASH-RECOVERY-sim_bsp_crash",
      "label": "SQLite WAL Zero-Loss State Recovery",
      "status": "VERIFIED",
      "sha256": "fe078e3a38a30ae2a2ca0ec445b644de5764aacd3d54ac1b29548058c7835935",
      "recovery_mechanism": "Automated Checkpoint Scanner"
    }
  ],
  "safe_abstention_rules": {
    "mandatory_verification_clause": "Sitasi wajib menyertakan simpul graf bertanda [VERIFIED].",
    "anti_speculation_barrier": "Semua klaim dinamika swarm yang tidak memiliki bukti hash SHA-256 terkomit wajib ditolak (Safe Abstention).",
    "minimum_nli_confidence_threshold": 0.85
  }
}
```

---

## 5. Kepatuhan Kontrak & Kompatibilitas Mundur

1. **REST API Endpoints Baru (`backend/app/api/enterprise.py`)**:
   - `POST /api/enterprise/bsp/simulate`: Menjalankan simulasi paralel BSP multi-platform dengan opsi ukuran swarm dan jumlah ronde.
   - `POST /api/enterprise/bsp/checkpoint`: Menyimpan snapshot manual ke SQLite WAL dengan verifikasi SHA-256.
   - `POST /api/enterprise/bsp/recover`: Memulihkan simulasi dari titik crash terakhir dan melakukan auto-resume.
   - `GET /api/enterprise/bsp/status/<job_id>`: Menampilkan metadata checkpoint dan riwayat status job.
   - `GET /api/enterprise/bsp/downstream-recommendations`: Mengembalikan paket handoff terkalibrasi untuk Agent 15.
2. **Kontrak Payload Simulasi (`contracts/05-step3-simulation.jsonl`)**:
   - Memperluas catatan superstep hingga 15 ronde lengkap dengan atribut `active_agents: 400`, `events_generated`, `status: "COMMITTED"`, dan integritas kriptografi `sha256`.
3. **Ekspor Modul Layanan (`backend/app/services/__init__.py`)**:
   - `BSPAgentState`, `BSPMessage`, `BSPBarrierMetrics`, `BSPCheckpointRecord`, `BSPSimulationMetrics`, `BSPSimulationResult`, `SQLiteWALCheckpointer`, `BSPSwarmRunner`, `RECOMMENDED_STATE_HASH_FIELDS`, `DEFAULT_PLATFORM_SYNC_INTERVALS_MS`.
4. **Artefak Human Gate Pipeline**:
   - `/home/biezz/contracts/pipeline/artifacts/slice-14-bsp-crash-recovery.json`
   - `/home/biezz/contracts/pipeline/artifacts/slice-14-human-gate-checklist.md`
