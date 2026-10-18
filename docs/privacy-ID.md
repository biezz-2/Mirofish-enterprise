# Dokumentasi Kepatuhan Pelindungan Data Pribadi (UU PDP No. 27/2022)
## MiroFish Enterprise - Autonomous Multi-Agent Social Simulation Platform

---

## 1. Landasan Hukum dan Ruang Lingkup

Dokumen ini menetapkan kerangka kerja tata kelola data dan kepatuhan sistem **MiroFish Enterprise** terhadap **Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)**.

MiroFish Enterprise beroperasi sebagai platform simulasi dinamika opini publik, analitik multi-agen sosial, dan penalar graf pengetahuan (GraphRAG) skala makro. MiroFish memposisikan diri sebagai **Pengendali Data Pribadi (Data Controller)** dan **Prosesor Data Pribadi (Data Processor)** yang taat hukum dalam seluruh siklus pemrosesan data: mulai dari pencarian web otonom (Langkah 0), ekstraksi graf pengetahuan (Langkah 1), hingga simulasi agen persona sintetis (Langkah 2–5).

### 1.1 Klasifikasi Data Sesuai Pasal 4 UU PDP
Sistem MiroFish mengklasifikasikan data yang ditemui ke dalam kategori berikut:
1. **Data Pribadi yang Bersifat Spesifik (Pasal 4 ayat 2)**:
   - Data kesehatan/rekam medis, biometrik, genetika, catatan kejahatan, data anak, dan data keuangan pribadi.
   - *Kebijakan*: **Dilarang keras diproses atau disimpan**. Setiap kemunculan data finansial (nomor rekening bank, nomor kartu kredit) atau data spesifik lainnya seketika diamputasi melalui modul `PIIScrubber` menjadi token anonim `[REDACTED_FINANCIAL]`.
2. **Data Pribadi yang Bersifat Umum (Pasal 4 ayat 3)**:
   - Nama lengkap, jenis kelamin, kewarganegaraan, agama, status perkawinan, dan/atau data pribadi yang dikombinasikan untuk mengidentifikasi seseorang (NIK, nomor telepon, alamat email).
   - *Kebijakan*: **Wajib disamarkan (scrubbed)** menjadi token anonim:
     - NIK (16 digit) -> `[REDACTED_NIK]`
     - Nomor HP Indonesia (+62 / 08xx) -> `[REDACTED_PHONE]`
     - Alamat Email -> `[REDACTED_EMAIL]`
     - Nama individu nyata -> `[REDACTED_NAME]`
3. **Data Agregat dan Opini Publik Sintetis**:
   - Tren makro, klaster wacana, distribusi sentimen statistik, dan persona simulasi abstrak (bukan representasi orang perseorangan nyata). Data ini bukan data pribadi karena tidak dapat dihubungkan kembali kepada individu tertentu.

---

## 2. Dasar Hukum Pemrosesan Data Publik (Pasal 20 UU PDP)

Dalam mengoperasikan riset web Langkah 0 (SearXNG self-hosted metasearch), MiroFish memproses data terbuka di ranah publik dengan berpijak pada:
1. **Pasal 20 ayat (2) huruf b**: Pemrosesan data pribadi untuk pemenuhan kewajiban hukum pengendali data.
2. **Pasal 20 ayat (2) huruf d**: Pemrosesan data yang dilakukan terhadap data pribadi yang telah **dipublikasikan secara umum oleh subjek data pribadi itu sendiri**.
3. **Pasal 20 ayat (2) huruf f**: Pemenuhan **kepentingan yang sah (legitimate interest)** pengendali data untuk keperluan riset ilmiah, pemodelan sosial makro, mitigasi krisis komunikasi, dan peningkatan ketahanan informasi nasional, dengan tetap memperhatikan keseimbangan antara kepentingan pengendali dan hak-hak subjek data.

---

## 3. Implementasi 6 Prinsip Utama Pelindungan Data (Pasal 16 UU PDP)

| No | Prinsip UU PDP | Implementasi Teknis pada MiroFish Enterprise | Instrumen Verifikasi |
|---|---|---|---|
| 1 | **Tujuan Terbatas & Spesifik** (Pasal 16 huruf a & b) | Pemrosesan data murni dibatasi untuk ekstraksi tren wacana sosial dan struktur relasi ontologis. Dilarang digunakan untuk profiling individu, penargetan iklan mikro, atau pengawasan perseorangan. | *Service Boundary Locks & API Scope Guard* |
| 2 | **Minimisasi Data (Data Minimization)** (Pasal 16 huruf c) | Data publik mentah yang ditarik via SearXNG disaring secara *in-memory* sebelum persistensi. Modul `backend/app/services/pii_scrubber.py` mengamputasi NIK, telepon, email, akun bank, dan nama pribadi seketika. | *PII Sanitization Hook pada Step 0 & Step 1* |
| 3 | **Akurasi & Integritas Data** (Pasal 16 huruf d) | Verifikasi sumber berbasis Domain Credibility Scorer ($S_{domain} \ge 0.70$) dan penandaan status epistemik (`[VERIFIED]`, `[UNVERIFIED]`, `[ASSUMED]`). | *EpistemicGroundingValidator (Agent 04)* |
| 4 | **Keamanan Pemrosesan** (Pasal 16 huruf e) | Enkripsi simetris AES-256-GCM pada data tersimpan (*at-rest*), TLS 1.3 pada data transmisi (*in-transit*), dan isolasi 3-lapis CaMeL Prompt Shield (L1 Sanitasi, L2 XML Spotlighting, L3 Passive Capability Gate). | *CaMeL Prompt Shield & Vault Security* |
| 5 | **Transparansi Pemrosesan** (Pasal 16 huruf f) | Seluruh aktivitas ekstraksi dan inferensi tercatat dalam audit log kekal (*append-only logs*) dengan stempel waktu ISO 8601 UTC. | *Auditable Event Logger & OpenAPI 3.1 Trace* |
| 6 | **Pembatasan Penyimpanan / Retensi** (Pasal 16 huruf g) | Data mentah cuplikan web dihapus setelah graf pengetahuan terbentuk. Entitas graf yang usang dimusnahkan secara berkala. | *Automated Retention Policy & Crypto-Shredding* |

---

## 4. Arsitektur Teknis Sanitasi PII (Step 0 & Step 1)

Untuk mencegah data sensitif masuk ke basis data graf (Neo4j, Graphiti, FalkorDB) dan Vector DB (Embedding Models), MiroFish menerapkan sanitasi deterministik ganda:

```
[Sumber Web Mentah / Dokumen Pengguna]
                  │
                  ▼
   ┌──────────────────────────────┐
   │  backend/app/services/       │
   │  pii_scrubber.py             │
   ├──────────────────────────────┤
   │ 1. Contextual NIK Scrubbing  │ ──► [REDACTED_NIK]
   │ 2. Financial & Card Scrubbing│ ──► [REDACTED_FINANCIAL]
   │ 3. 16-Digit Standalone NIK   │ ──► [REDACTED_NIK]
   │ 4. Phone (+62 / 08xx) Scrub  │ ──► [REDACTED_PHONE]
   │ 5. Email RFC 5322 Scrub      │ ──► [REDACTED_EMAIL]
   │ 6. Personal Name Scrubbing   │ ──► [REDACTED_NAME]
   └──────────────────────────────┘
                  │
                  ▼ (100% PII-Free Text Stream)
   ┌────────────────────────────────────────────────────────┐
   │  Step 0: Web Research (SearXNG + CaMeL Shield)         │
   │  Step 1: Graph Builder (Adaptive Chunking & Ontology)  │
   │  Storage: FalkorDB / Graphiti / Neo4j / Local Vector DB│
   └────────────────────────────────────────────────────────┘
```

### 4.1 Jaminan Idempotensi
Fungsi sanitasi bersifat idempoten:
$$\text{scrub\_pii}(\text{scrub\_pii}(T)) = \text{scrub\_pii}(T)$$
Token pengganti (`[REDACTED_*]`) kebal terhadap pemindaian ulang, mencegah mutasi rekursif atau kerusakan teks sintaksis.

---

## 5. Hak-Hak Subjek Data (Pasal 5 s/d Pasal 15 UU PDP)

MiroFish Enterprise memfasilitasi pemenuhan hak-hak asasi subjek data sesuai mandat Bab IV UU PDP:

1. **Hak Memperoleh Informasi (Pasal 5)**:
   Subjek data berhak mengetahui kejelasan identitas, dasar kepentingan hukum, dan tujuan pemrosesan data. Dokumentasi ini dan endpoint `/api/research/health` menyediakan transparansi penuh atas penggunaan mesin metasearch privat tanpa pelacakan (*zero tracking*).
2. **Hak Mengakses dan Memperoleh Salinan (Pasal 7)**:
   Subjek data dapat meminta konfirmasi apakah data pribadi mereka terdapat dalam korpus graf MiroFish.
3. **Hak Pembaruan dan Rektifikasi (Pasal 6)**:
   Jika ditemukan kekeliruan data pada ekstraksi entitas faktual, subjek data berhak mengajukan koreksi melalui mekanisme re-grounding ontologi.
4. **Hak Penghentian Pemrosesan dan Penghapusan / Hak untuk Dilupakan (Pasal 8)**:
   Subjek data berhak menuntut penghapusan (*erasure/purge*) data pribadi mereka dari graf memori. MiroFish menyediakan perintah *Graph Purge API* untuk menghapus simpul (*nodes*) dan relasi (*edges*) terkait subjek data dalam waktu paling lambat $3 \times 24$ jam sejak permohonan diverifikasi.
5. **Hak Menarik Persetujuan (Pasal 9)**:
   Penarikan persetujuan berakibat pada penghentian seketika pemrosesan data terkait subjek bersangkutan.
6. **Hak Menolak Otomatisasi Profiling Individu (Pasal 10)**:
   **MiroFish melarang keras segala bentuk profiling otomatis terhadap orang perseorangan**. Subjek data berhak menolak keputusan yang didasarkan pada pemrosesan otomatis yang berdampak hukum.

### Saluran Kontak Hak Subjek Data:
Permohonan pemenuhan hak subjek data dapat diajukan secara resmi melalui koordinator kepatuhan data:
- **Email Kepatuhan**: `privacy@mirofish.enterprise.local` / `dpo@mirofish.org`
- **Waktu Respons Maksimal**: $3 \times 24$ jam kerja untuk konfirmasi awal, maksimal 30 hari kalender untuk eksekusi penghapusan/rektifikasi penuh.

---

## 6. Retensi Data Simulasi dan Kebijakan Pemusnahan

1. **Data Kueri dan Cuplikan Mentah (Step 0)**:
   - Masa simpan: **Ephemeral (In-Memory)**.
   - Dibuang seketika setelah laporan ekstraksi fakta (`ResearchReport`) diekspor menjadi kontrak JSON.
2. **Teks Masukan Dokumen (Step 1)**:
   - Masa simpan: Maksimal selama masa aktif proyek simulasi pengguna, atau paling lama 90 hari kalender jika proyek tidak aktif.
   - Format: Seluruh berkas wajib melalui sanitasi `TextProcessor.preprocess_text` sebelum disimpan di media lokal (`backend/uploads/projects/`).
3. **Graf Memori Temporal (FalkorDB / Graphiti / Zep Cloud)**:
   - Masa simpan: Terikat pada daur hidup proyek (`project_id`).
   - Apabila sebuah proyek dihapus melalui antarmuka atau API (`DELETE /api/graph/project/<id>`), sistem secara otomatis mengeksekusi cascading delete pada simpul graf lokal dan Cloud.
4. **Pemusnahan Data (*Crypto-Shredding*)**:
   - Pemusnahan data menggunakan penimpaan biner (*zeroing/shred*) pada disk lokal dan pembatalan kunci enkripsi terkait, memastikan data tidak dapat direkonstruksi kembali.

---

## 7. Pernyataan Penutup

Implementasi kepatuhan UU PDP No. 27/2022 pada MiroFish Enterprise bukan sekadar kewajiban administratif, melainkan pilar desain arsitektur (*Privacy by Design and by Default*). Platform berkomitmen menjaga kedaulatan data dan privasi setiap warga negara Indonesia dalam setiap lini inovasi kecerdasan buatan.
