# Evaluasi: Plan Arsitektur Terpadu Auto System Prompt & Mitigasi Halusinasi untuk MiroFish Enterprise

## 1. Pendahuluan
Dokumen ini merupakan analisis mendalam dan evaluasi kritis mengenai kecocokan "Plan Arsitektur Terpadu Auto System Prompt dan Mitigasi Halusinasi (berbasis arXiv:2509.04664 dan arXiv:2602.17671)" jika diterapkan pada ekosistem **MiroFish Enterprise (v3.1)**.

MiroFish adalah *Autonomous Swarm Intelligence & Multi-Agent Predictive Simulation Sandbox*. Sistem ini memiliki arsitektur yang kompleks, mencakup:
- **Backend/Frontend**: Flask/Python backend, SQLite/PostgreSQL, Vue 3.
- **Ekosistem Agent Pengembang**: Terdapat direktori `.claude/agents/` yang mengindikasikan penggunaan agent eksternal (seperti Claude Code) yang sangat terstruktur dalam pemeliharaan repositori.
- **Pipeline Internal Simulasi (5 Langkah)**: Step 0 (Web Research via SearXNG), Step 1 (GraphRAG Zep/Neo4j), Step 2 (OCEAN Profiles), Step 3 (Parallel Swarm Simulation di 7 platform sosmed), Step 4 (ReACT Report Agent).

---

## 2. Evaluasi pada Dimensi A: Meta-Orchestration (Agen Pengembang)
Dimensi ini berfokus pada penggunaan Claude Code dan Hermes Agent sebagai asisten *developer* untuk memelihara dan mengembangkan repositori MiroFish.

**Kesesuaian: SANGAT COCOK (Highly Suitable)**

Repositori ini membagi tugas developer ke dalam subagent spesifik (misal `mirofish-web-researcher.md`, `mirofish-graphrag-engineer.md`). Arsitektur 5-Lapis pada rencana ini sangat sesuai untuk ranah meta-orchestration:
- **Lapis 1 & Lapis 2 (Prompt Compiler & Guardrail di CLAUDE.md)**: Agent yang mengembangkan backend Flask sering kali terjebak dalam halusinasi path impor, fabrikasi metode SQLAlchemy, atau modifikasi file yang salah. Guardrail anti-sycophancy memastikan agent tidak sekadar mengiyakan premis pengguna yang mungkin keliru terkait arsitektur MiroFish yang ketat.
- **Lapis 3 & 4 (Hooks & Kontrak Delegasi)**: PreToolUse yang memblokir instalasi buta sangat penting karena MiroFish memiliki `requirements.txt` yang spesifik untuk versi Python 3.10-3.13 dan Zep. PostToolUse memastikan agen memverifikasi hasil sebelum menyimpan ke memori. Kontrak 3 tingkat (terutama `ABSTAIN_INSUFFICIENT_CONTEXT`) akan menekan risiko agen mengarang solusi saat log error tidak lengkap.
- **Lapis 5 (Cron Audit)**: Secara rutin membersihkan memori agen agar tidak terjebak dalam *persistence failure* mengingat ekosistem MCP server dan backend MiroFish terus berkembang.

---

## 3. Evaluasi pada Dimensi B: Domain Internal MiroFish
Dimensi ini mengevaluasi apakah prinsip epistemik dari plan tersebut dapat diadaptasi menjadi sistem prompt internal bagi agen-agen *di dalam* MiroFish (Step 0 s.d. Step 4).

**Kesesuaian: COCOK BERSYARAT (Conditionally Suitable)**

Penerapan prinsip anti-halusinasi tidak dapat dipukul rata pada seluruh sistem internal MiroFish. Hal ini disebabkan oleh tujuan utama MiroFish sebagai *sandbox* simulasi perilaku manusia di media sosial.

### ✅ Cocok untuk Step 0, Step 1, dan Step 4 (Analitik & Ekstraksi Data)
- **Step 0 (Web Research) & Step 1 (GraphRAG)**: Di sini, halusinasi berakibat fatal karena *Knowledge Graph* harus berdasarkan fakta empiris (`verified`). Menerapkan label epistemik (`[VERIFIED]`, `[UNVERIFIED]`) dan menghargai "Abstention" (tidak tahu) sangat selaras dengan fitur *3-Layer Anti-Prompt Injection Shield* yang sudah ada. Ini mencegah masuknya relasi palsu ke Zep Cloud.
- **Step 4 (ReACT ReportAgent)**: Agen analitik ini bertugas menghasilkan laporan *predictive intelligence*. ReACT *loop* sangat rentan terhadap overconfidence dan fabrikasi wawasan. Memaksa ReportAgent untuk menggunakan klausa abstensi saat `InsightForge` tidak menemukan data akan sangat meningkatkan validitas ilmiah laporan yang dihasilkan.

### ❌ TIDAK COCOK untuk Step 3 (Parallel Swarm Simulation)
- **Konflik Fundamental**: Step 3 menjalankan ribuan agen yang dimodelkan dengan profil psikologi OCEAN untuk berinteraksi di 7 platform media sosial (Twitter, Reddit, Facebook, dll.).
- Jika agen simulasi diberi sanksi fatal untuk "tebakan percaya diri" atau dilarang melakukan "sycophancy" (mengiyakan premis yang salah), maka **efek Echo Chamber (ruang gema) dan penyebaran misinformasi tidak akan pernah terjadi**.
- Manusia di media sosial *sering kali* berhalusinasi, overconfident, dan menyetujui premis yang salah. Memaksakan *epistemic guardrails* pada agen di Step 3 akan menghancurkan realisme sosiologis simulasi MiroFish.

---

## 4. Keuntungan, Risiko, dan Penyesuaian

### Keuntungan (Pros)
1. **Integritas Repositori (Meta-level)**: Modifikasi file dan integrasi MCP akan jauh lebih stabil karena agen pengembang dilarang berasumsi.
2. **Kualitas Data Ekstraksi (Internal)**: Menghasilkan GraphRAG yang 100% didasarkan pada data faktual, mengurangi *noise* di dalam database `SQLite/PostgreSQL`.
3. **Auditabilitas Laporan**: ReportAgent di Step 4 dapat menghasilkan laporan dengan tingkat keyakinan yang akurat, dengan menyatakan ketidaktahuan jika data simulasi tidak cukup.

### Risiko / Bottleneck (Cons)
1. **Resiko Kehancuran Simulasi**: Jika filter *epistemic* bocor ke sistem *prompt* agen simulasi di Step 3, perilaku platform menjadi kaku dan artifisial.
2. **Infinite Abstention Loop di ReACT**: Jika penalti halusinasi terlalu kuat, Step 4 ReACT ReportAgent mungkin terjebak dalam *loop* "Saya tidak tahu", menyebabkan laporan gagal di-generate (timeout pada siklus Tool Call).
3. **Overhead Latensi**: Memverifikasi *ground-truth* pada Step 0 & 1 menambah latensi proses LLM.

### Penyesuaian Spesifik (Required Adjustments)
- **Isolasi Prompt**: Terapkan *whitelist/blacklist* untuk Arsitektur 5 Lapis. Guardrail epistemik **wajib** digunakan pada prompt untuk *ReportAgent*, namun **dilarang keras** disisipkan pada `OasisProfileGenerator` dan *Agent Actions* di Step 3.
- **Fallback Abstensi untuk ReACT**: Pada Step 4, map respon `ABSTAIN_INSUFFICIENT_CONTEXT` menjadi *graceful degradation* (misal: "Berdasarkan simulasi, tren ini tidak teramati secara signifikan") alih-alih melempar *error exception* ke sistem backend.

---

## 5. Kesimpulan dan Rekomendasi Akhir

**Rekomendasi Akhir: COCOK BERSYARAT (Conditionally Suitable)**

Plan arsitektur terpadu anti-halusinasi ini sangat brilian dan sangat dibutuhkan untuk **pengembangan kode (Meta-Orchestration)** dan **modul analitik data** di MiroFish Enterprise. Namun, ia menjadi anti-pola (anti-pattern) jika diterapkan pada agen simulasi sosial yang desainnya memang membutuhkan cacat kognitif manusia (bias, overconfidence, echo-chambers).

**Prioritas Implementasi:**
1. **Prioritas 1 (Tinggi)**: Implementasikan Arsitektur Lapis 2, 3, dan 4 pada Claude Code dan Hermes sebagai meta-orchestrator repositori (tambahkan ke `.claude/agents/` dan `CLAUDE.md`).
2. **Prioritas 2 (Sedang)**: Integrasikan Gerbang Epistemik (Lapis 1) ke dalam `ReportAgent` (Step 4) untuk memastikan klaim laporan didukung oleh kutipan entitas graf yang nyata.
3. **Prioritas 3 (Selektif)**: Tambahkan label `[VERIFIED]` / `[UNVERIFIED]` pada output `SearXNG Web Research` (Step 0) sebelum masuk ke *Knowledge Graph*.
4. **Pengecualian Mutlak**: Jangan sentuh algoritma dan *prompt* yang berjalan di dalam `MultiPlatformSimulator` (Step 3). Biarkan agen simulasi tetap "berhalusinasi" demi validitas eksperimen sosial.
