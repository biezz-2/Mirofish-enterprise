# Deliverable: Agent 18 — OpenAPI 3.1 RESTful API & Distributed Webhook Engine

**Task ID**: `t_a0bb3682`  
**Slice**: Slice 18 (Subagent 18: OpenAPI 3.1 RESTful API & Distributed Webhook Engine)  
**Divisi**: Core Engineering & Platform Development (Divisi DEV / Ekstensibilitas Universal)  
**Status**: Ready for Human Gate Approval & Downstream Handoff (Agent 19: Vue 3 Control Dashboard `t_c5459b36`, Agent 20: DevOps & QA Gate Guard `t_e84830cd`)  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 7 & 8; Kontrak Step 5 Extensibility (`contracts/06-step4-report.md`), Kontrak Deliverable Agent 17 (`contracts/DELIVERABLE-AGENT-17.md`), Deliverable Agent 16 (`contracts/DELIVERABLE-AGENT-16.md`)  

---

## 1. Ringkasan Eksekutif & Arsitektur Sistem

Sebagai bagian krusial dalam **Step 5: Universal Extensibility & Dashboard**, Agent 18 mengimplementasikan spesifikasi resmi **OpenAPI 3.1.0** yang terikat langsung dengan dialek **JSON Schema Draft 2020-12**, serta mesin pengiriman **Distributed Webhooks** berkemampuan tinggi dengan otentikasi kriptografis **HMAC-SHA256**, pencegahan serangan pemutaran ulang (*anti-replay timestamp verification*), kebijakan *exponential backoff retry* dengan *full jitter*, dan antrean pesan gagal (*Dead-Letter Queue / DLQ*) yang dilengkapi kapabilitas inspeksi serta *re-drive* (pengiriman ulang) terdistribusi.

Arsitektur OpenAPI 3.1.0 & Webhook Engine MiroFish Enterprise mencakup:
1. **OpenAPI 3.1.0 Specification & Dialek JSON Schema Draft 2020-12**:
   - Mematuhi standar formal `openapi: 3.1.0` dengan deklarasi meta-schema `jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema`.
   - Menggunakan validator kanonikal `jsonschema.Draft202012Validator` untuk validasi muatan (*request payload validation*) secara deterministik pada titik masuk API.
   - Menyediakan objek tingkat atas `webhooks` sesuai spesifikasi OpenAPI 3.1.0 untuk mendokumentasikan katalog peristiwa webhook yang dipublikasikan platform.
   - Endpoint Swagger UI interaktif (`/docs`, `/api/docs`, `/api/v1/enterprise/docs`) dan ekspor spesifikasi format JSON (`/openapi.json`) serta YAML (`/openapi.yaml`, `docs/openapi.yaml`).
2. **Mesin Webhook Terdistribusi & Kriptografi HMAC-SHA256**:
   - Pembangkitan tanda tangan kriptografis `X-Mirofish-Signature` berformat `sha256=<hex_digest>` menggunakan kunci rahasia (*pre-shared secret*) dengan payload pesan yang distandarisasi (`canonical JSON`).
   - Header verifikasi stempel waktu `X-Mirofish-Timestamp` dengan toleransi pergeseran jam (*clock skew tolerance*) maksimum 300 detik (5 menit) untuk memblokir serangan pemutaran ulang (*replay attacks*).
   - Pengiriman paralel asinkron melalui thread pool aman (*daemon threads*) tanpa memblokir thread eksekusi utama simulasi atau API.
3. **Kebijakan Retry Exponential Backoff dengan Jitter & Latensi P95 < 250ms**:
   - Algoritma Full Jitter:
     $$\Delta t = \min(t_{\max}, t_0 \cdot 2^{\text{attempt}-1}) \times \text{Uniform}(0, 1)$$
   - Mengeliminasi fenomena *thundering herd* pada sistem penerima webhook downstream.
   - Pengujian benchmark beban menghasilkan latensi terkirim P95 konsisten di bawah 250 ms (rata-rata 10-25 ms pada mode simulasi cepat).
4. **Dead-Letter Queue (DLQ) & Manajemen Re-Drive**:
   - Setiap webhook yang gagal dikirim setelah seluruh kuota percobaan (*retries*) habis secara otomatis dialihkan ke antrean DLQ berstempel waktu kegagalan dan riwayat kode status respons HTTP.
   - Dilengkapi antarmuka inspeksi (`GET /api/v1/enterprise/webhooks/dlq`), mekanisme re-drive selektif per event atau massal (`POST /api/v1/enterprise/webhooks/dlq/redrive` / `POST /api/v1/enterprise/webhooks/dlq/replay`), dan pembersihan antrean (`DELETE /api/v1/enterprise/webhooks/dlq`).
5. **Integrasi Dua-Arah dengan Layanan Eksekutif & Risiko BettaFish**:
   - Peristiwa pembuatan laporan eksekutif C-Level (`/api/v1/enterprise/bettafish/executive-report`) memicu penyiaran webhook `BETTAFISH_EXECUTIVE_REPORT_GENERATED`.
   - Analisis risiko korporat berkategori `HIGH` atau `CRITICAL` (`/api/v1/enterprise/bettafish/risk-assessment`) memicu peringatan darurat seketika melalui webhook `BETTAFISH_CRITICAL_RISK_ALERT`.
   - Pemanggilan alat kanonikal MCP (`/api/v1/enterprise/mcp/invoke`) menyiarkan peristiwa `MCP_TOOL_INVOKED`.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 17: Canonical FastMCP Server Architect                           │
  │   (FastMCP Streamable HTTP, OAuth 2.1 RFC 7636, 11 Canonical Tools)    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Upstream Tools & Event Registry
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 18: OpenAPI 3.1 RESTful API & Distributed Webhook Engine         │
  │                                                                        │
  │  [OpenAPI 3.1.0]     ──▶ JSON Schema Draft 2020-12, Top-Level Webhooks │
  │  [Swagger UI Docs]   ──▶ /docs, /openapi.json, /openapi.yaml           │
  │  [Request Validator] ──▶ @validate_request_schema(Draft202012)         │
  │  [HMAC-SHA256 Sign]  ──▶ X-Mirofish-Signature, X-Mirofish-Timestamp    │
  │  [Jittered Backoff]  ──▶ Exponential Backoff + Full Jitter (P95<250ms) │
  │  [DLQ Engine]        ──▶ Dead-Letter Queue Inspection & Re-drive API   │
  │  [BettaFish Alerts]  ──▶ CRITICAL_RISK_ALERT & REPORT_GENERATED Events │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Downstream Extensibility Handoff
                     ┌────────────────┼────────────────┐
                     ▼                                 ▼
  ┌──────────────────────────────────────┐ ┌──────────────────────────────────────┐
  │ Agent 19: Vue 3 Control Dashboard    │ │ Agent 20: DevOps & QA Gate Guard     │
  │ Task: t_c5459b36 (7 Enterprise Panels│ │ Task: t_e84830cd (AES-256 Vault/QA)  │
  └──────────────────────────────────────┘ └──────────────────────────────────────┘
```

---

## 2. Landasan Teori & Spesifikasi Teknis

### 2.1 JSON Schema Dialect 2020-12 & OpenAPI 3.1.0 Compliance
Spesifikasi OpenAPI 3.1.0 mengadopsi JSON Schema Draft 2020-12 secara penuh sebagai model schema bawaan.
- **Dialect URI**: `https://json-schema.org/draft/2020-12/schema`
- Seluruh definisi schema pada `components/schemas` mematuhi meta-schema draft 2020-12, meliputi:
  - `SimulationProject`: Validasi atribut judul (minLength: 3), parameter agen, dan konfigurasi multi-platform.
  - `SimulationStepRequest`: Validasi langkah tick simulasi sinkron.
  - `WebhookSubscription`: Validasi pendaftaran URL penerima webhook dan daftar peristiwa.
  - `PolarSentimentAnalysis`: Validasi skor polaritas kontinu $[-1.0, +1.0]$ dan 8 vektor emosi.
  - `CorporateRiskAssessment`: Validasi level risiko korporat (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) dan skor komposit.
- Validasi masukan didekorasikan dengan `@validate_request_schema(schema_dict)` pada endpoint RESTful Flask, yang secara ketat menolak request payload yang menyimpang dengan HTTP 422 Unprocessable Entity.

### 2.2 Top-Level Webhooks Object Catalog
OpenAPI 3.1.0 memaparkan objek tingkat atas `webhooks` yang mendokumentasikan katalog pesan asinkron yang dikirimkan MiroFish:
1. `BETTAFISH_EXECUTIVE_REPORT_GENERATED`: Laporan naratif ringkasan C-Level telah selesai disintesis berstempel SHA-256.
2. `BETTAFISH_CRITICAL_RISK_ALERT`: Peringatan dini eskalasi risiko korporat kritis (polaritas negatif ekstrim atau potensi kaskade viral Hawkes tinggi).
3. `MCP_TOOL_INVOKED`: Pemanggilan alat eksekusi simulasi atau analitik graf melalui MCP.
4. `MCP_SIMULATION_STATE_CHANGED`: Perubahan status mesin siklus hidup simulasi.
5. `SIMULATION_ROUND_COMPLETED`: Penyelesaian satu putaran interaksi agen swarm BSP.
6. `SIMULATION_COMPLETED`: Penyelesaian komputasi seluruh siklus simulasi swarm.
7. `SYSTEM_ALERT`: Anomali operasional atau peringatan performa sistem.

### 2.3 Protokol Otentikasi Webhook (HMAC-SHA256 & Anti-Replay)
Pengiriman payload webhook diamankan menggunakan tanda tangan kriptografis:
1. **Pembangkitan Tanda Tangan**:
   $$\text{Signature} = \text{HMAC-SHA256}(K, T \mathbin{\Vert} \text{Payload})$$
   Di mana $K$ adalah pre-shared secret key dan $T$ adalah stempel waktu Unix (detik).
   Header HTTP yang dikirimkan:
   - `X-Mirofish-Signature: sha256=<hex_digest>`
   - `X-Mirofish-Timestamp: <timestamp>`
   - `X-Mirofish-Delivery-Id: <uuid>`
   - `X-Mirofish-Event: <event_type>`
2. **Pencegahan Serangan Replay**:
   Sistem penerima atau penguji memverifikasi stempel waktu terhadap batas ambang $\delta = 300\text{ s}$:
   $$|T_{\text{current}} - T_{\text{header}}| \le 300$$
   Jika stempel waktu berada di luar ambang batas (kedaluwarsa atau terjadi deviasi jam maju/mundur melebihi toleransi), pesan ditolak seketika (*stale or future timestamp rejected*).

### 2.4 Kebijakan Retry Exponential Backoff dengan Jitter & Latensi P95
Algoritma retry menerapkan Full Jitter untuk mendistribusikan beban jaringan secara acak dan mencegah tabrakan serentak:
$$\Delta t_i = \text{Uniform}\left(0, \min(t_{\max}, t_0 \cdot 2^{i-1})\right)$$
- Nilai awal $t_0 = 0.05\text{ s}$, pengganda basis $2.0$, batas atas $t_{\max} = 2.0\text{ s}$.
- Kesalahan sisi klien (HTTP 4xx seperti 400, 401, 403, 404, 422) tidak diulang karena menunjukkan kesalahan payload atau otentikasi permanen.
- Kesalahan jaringan atau HTTP 5xx diulang hingga kuota `max_retries` terpenuhi.
- Pada benchmark pengiriman cepat, P95 tercatat stabil di bawah 250 ms.

### 2.5 Dead-Letter Queue (DLQ) & Endpoint Re-Drive
Setiap peristiwa yang gagal setelah kuota percobaan terpenuhi dipindahkan ke DLQ:
- Kapasitas buffer DLQ terisolasi di memori dengan batasan aman 500 entri terakhir.
- Endpoint terkelola:
  - `GET /api/v1/enterprise/webhooks/dlq`: Menampilkan daftar item dalam DLQ dengan pagination (`limit`, `offset`) dan filter tipe peristiwa.
  - `POST /api/v1/enterprise/webhooks/dlq/redrive` (alias: `/replay`): Memicu pengiriman ulang instan per `event_id` atau re-drive massal seluruh item yang gagal.
  - `DELETE /api/v1/enterprise/webhooks/dlq`: Membersihkan antrean DLQ secara manual.

---

## 3. Struktur File & Modifikasi Komponen

| File Path | Operasi | Deskripsi Komponen |
| :--- | :--- | :--- |
| `backend/app/services/openapi_engine.py` | **Created** | Mesin spesifikasi OpenAPI 3.1.0, dialek JSON Schema Draft 2020-12, schema component registry, katalog webhooks, dan decorator validasi request. |
| `backend/app/services/webhook_service.py` | **Modified** | Engine Webhook terdistribusi: HMAC-SHA256, verifikasi anti-replay, exponential backoff dengan jitter, DLQ store, dan in-memory benchmark test harness. |
| `backend/app/services/__init__.py` | **Modified** | Ekspor modul dan simbol OpenAPI 3.1.0 serta Webhook Dispatcher ke dalam package services. |
| `backend/app/services/bettafish_adapter.py` | **Modified** | Normalisasi klaim risiko korporat untuk menyelaraskan polaritas negatif terhadap pemicu peringatan dini BettaFish. |
| `backend/app/api/enterprise.py` | **Modified** | Pemasangan endpoint OpenAPI (`/openapi.json`, `/openapi.yaml`, `/docs`), manajemen langganan webhook (`/webhooks/subscriptions`), dispatch manual, DLQ redrive/inspection, dan trigger webhook risiko BettaFish. |
| `backend/app/__init__.py` | **Modified** | Pemasangan route OpenAPI 3.1.0 dan Swagger UI pada tingkat root application factory (`/openapi.json`, `/docs`). |
| `docs/openapi.yaml` | **Updated** | Spesifikasi lengkap OpenAPI 3.1.0 dalam format YAML yang tersinkronisasi. |
| `docs/openapi.json` | **Created** | Spesifikasi lengkap OpenAPI 3.1.0 dalam format JSON untuk tooling otomatis dan frontend dashboard. |
| `backend/tests/test_agent18_webhooks_and_openapi.py` | **Created** | Suite pengujian otomatis mencakup 18 skenario pengujian komprehensif (100% lulus). |

---

## 4. Hasil Verifikasi & Test Suite (100% Pass)

### 4.1 Eksekusi Test Suite Agent 18
Perintah eksekusi:
```bash
PYTHONPATH=/home/biezz/Documents/Project/coding/Mirofish-enterprise:/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend \
/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend/.venv/bin/pytest \
backend/tests/test_agent18_webhooks_and_openapi.py -v
```
Hasil Aktual: **18 passed in 3.05s** (100% Lulus).

Daftar 18 Skenario Pengujian:
1. `test_openapi_version_and_dialect`: Verifikasi `openapi: 3.1.0` dan meta-schema dialek JSON Schema Draft 2020-12.
2. `test_openapi_top_level_webhooks_catalog`: Validasi katalog objek tingkat atas `webhooks`.
3. `test_json_schema_2020_12_validation_utility`: Pengujian validasi schema valid dan invalid via `Draft202012Validator`.
4. `test_webhook_hmac_signature_generation_and_verification`: Pembangkitan tanda tangan HMAC-SHA256, deteksi tamper payload, dan penolakan kunci rahasia salah.
5. `test_webhook_anti_replay_timestamp_protection`: Penolakan stempel waktu kedaluwarsa (>300s) dan stempel waktu masa depan yang melampaui toleransi.
6. `test_exponential_backoff_jitter_distribution`: Verifikasi keterikatan delay pada interval batas atas dan keacakan variansi jitter.
7. `test_webhook_delivery_p95_latency_benchmark`: Uji beban 50 request beruntun dengan target P95 latency < 250ms (lulus dengan hasil < 25ms).
8. `test_webhook_dlq_capture_and_redrive`: Pengalihan pengiriman gagal ke antrean DLQ dan eksekusi re-drive saat endpoint pulih.
9. `test_dlq_api_endpoints`: Verifikasi endpoint RESTful inspeksi (`GET /dlq`), re-drive (`POST /dlq/replay`), dan pembersihan (`DELETE /dlq`).
10. `test_webhook_subscriptions_crud_lifecycle`: Siklus hidup lengkap pendaftaran, pemanggilan, dan penghapusan langganan webhook.
11. `test_mock_webhook_receiver_end_to_end`: Pengujian end-to-end pengiriman webhook ke mock receiver lokal dengan validasi tanda tangan HMAC dan timestamp.
12. `test_request_schema_validation_decorator`: Pengujian penolakan request payload yang melanggar kontrak JSON Schema 2020-12 dengan kode HTTP 422.
13. `test_mcp_invoke_dispatches_webhook`: Verifikasi bahwa pemanggilan alat kanonikal MCP menyiarkan webhook `MCP_TOOL_INVOKED`.
14. `test_bettafish_executive_report_webhook_broadcast`: Verifikasi otomatisasi broadcast webhook saat laporan C-Level dibuat.
15. `test_bettafish_critical_risk_alert_webhook`: Verifikasi deteksi risiko korporat tingkat `HIGH`/`CRITICAL` yang memicu seketika webhook peringatan darurat.
16. `test_openapi_json_endpoint_and_swagger_docs`: Verifikasi ketersediaan dan struktur endpoint `/openapi.json` serta `/docs`.
17. `test_openapi_yaml_endpoint`: Verifikasi ketersediaan dan validitas parsing dokumen spesifikasi `/openapi.yaml`.
18. `test_root_level_openapi_and_docs`: Verifikasi route root level `/openapi.json` dan `/docs`.

### 4.2 Uji Regresi Enterprise Penuh (Full Regression Suite)
Perintah eksekusi gabungan (Agent 17 + Agent 18 + Legacy Enterprise):
```bash
PYTHONPATH=/home/biezz/Documents/Project/coding/Mirofish-enterprise:/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend \
/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend/.venv/bin/pytest \
backend/tests/test_agent18_webhooks_and_openapi.py \
backend/tests/test_v32_enterprise.py \
backend/tests/test_fastmcp_server.py
```
Hasil Aktual: **43 passed in 4.89s** (0 gagal, 0 regresi).

---

## 5. Matriks Handoff ke Downstream Agents

### 5.1 Handoff ke Agent 19: Vue 3 Control Dashboard (`t_c5459b36`)
1. **Endpoint OpenAPI & Dokumentasi Interaktif**:
   - URL Spesifikasi JSON: `/api/v1/enterprise/openapi.json` dan `/openapi.json`.
   - URL Dokumentasi Swagger UI: `/api/v1/enterprise/docs` dan `/docs`.
   - Schema Pydantic & JSON Schema 2020-12 dapat digunakan langsung oleh pustaka klien frontend (misal: `openapi-fetch` atau generator tipe TypeScript).
2. **Endpoint Manajemen Webhook & Monitoring**:
   - `GET /api/v1/enterprise/webhooks/subscriptions`: Menampilkan daftar URL penerima event untuk panel *Webhook Management*.
   - `POST /api/v1/enterprise/webhooks/subscriptions`: Pendaftaran subscriber baru dari UI.
   - `GET /api/v1/enterprise/webhooks/deliveries`: Riwayat pengiriman webhook terkini untuk tabel monitoring.
   - `GET /api/v1/enterprise/webhooks/dlq`: Pemantauan antrean Dead-Letter Queue secara visual di dasbor.
   - `POST /api/v1/enterprise/webhooks/dlq/redrive`: Tombol aksi re-drive manual dari antarmuka dasbor.

### 5.2 Handoff ke Agent 20: DevOps, AES-256-GCM Vault & QA Phase-Gate Guard (`t_e84830cd`)
1. **Parameter Lingkungan & Keamanan**:
   - Webhook signing secrets dikelola melalui modul `VaultManager` dan variabel lingkungan `WEBHOOK_DEFAULT_SECRET`.
   - Tidak ada kredensial atau rahasia yang di-hardcode (semua rahasia bertopeng `[REDACTED]` dalam payload konfigurasi).
   - Validasi schema Draft 2020-12 menjamin isolasi input pada boundary API sebelum mencapai logic engine atau database.
2. **Kesiapan Cluster & Health Check**:
   - Endpoint kesehatan `/api/v1/enterprise/health` dan `/health` mencatat ketersediaan OpenAPI generator dan Webhook Dispatcher.
   - Seluruh artefak pengujian (43 test cases) siap diaudit dalam automated CI pipeline PM2 cluster.

---

## 6. Pernyataan Kepatuhan Protokol & R3 Gate
Seluruh deliverable Agent 18 telah diuji secara nyata dengan runtime Python lokal pada lingkungan virtual `.venv`, menghasilkan artefak spesifikasi OpenAPI 3.1.0 yang valid, mesin webhook terdistribusi dengan proteksi kriptografis HMAC-SHA256, anti-replay, exponential backoff full-jitter, dan DLQ re-drive. Pekerjaan siap ditinjau dan diserahkan ke human architect serta divisi downstream.
