# Plan: Arsitektur Terpadu Auto System Prompt & Mitigasi Halusinasi MiroFish Enterprise

- **Project ID**: `mirofish-epistemic-mitigation`
- **Repositori Target**: `biezz-2/Mirofish-enterprise`
- **Referensi Teoretis**: arXiv:2509.04664 (*Why Language Models Hallucinate*), arXiv:2602.17671 (*AI Hallucination from Students Perspective*)
- **Status Evaluasi**: Sesuai dengan hasil evaluasi Jules session `12731709436002675240` (COCOK BERSYARAT).

---

## 1. Tujuan & Kriteria Keberhasilan (Objective & Success Criteria)

### Tujuan:
Menerapkan arsitektur 5-lapis mitigasi halusinasi dan auto system prompt ke dalam repositori MiroFish Enterprise untuk mengamankan meta-developer (Claude Code & Hermes) serta memperkuat validitas analitik data internal (Step 0, Step 1, Step 4) tanpa merusak kebebasan simulasi sosial di Step 3.

### Kriteria Keberhasilan (Testable):
1. **CLAUDE.md & Hooks**: Terpasang `CLAUDE.md` di root repo, serta script hooks deterministik di `.claude/hooks/` (`block-blind-installs.sh`, `verify-after-edit.sh`, `epistemic-audit.sh`) yang teregistrasi di `.claude/settings.json`.
2. **11 Agent Claude Code**: Seluruh file `.claude/agents/*.md` diperbarui dengan protokol safe abstention, premise check, dan kontrak status kembalian 3 tingkat (`VERIFIED_SUCCESS`, `UNVERIFIED_HYPOTHESIS`, `ABSTAIN_INSUFFICIENT_CONTEXT`).
3. **ReportAgent (Step 4)**: `backend/app/services/report_agent.py` dilengkapi klausul epistemic gate (safe abstention, sitasi simpul graf, graceful degradation saat data kosong) tanpa memicu crash/timeout.
4. **Web Research (Step 0)**: `backend/app/services/web_research_service.py` menyertakan pelabelan status epistemik (`[VERIFIED]`, `[UNVERIFIED]`, `[ASSUMED]`) pada ekstraksi fakta dan entitas.
5. **Non-interference Guarantee (Step 3)**: File simulasi swarm (`backend/app/services/multi_platform_simulator.py`, `simulation_runner.py`) tidak diubah dan tidak diinjeksi filter anti-halusinasi sehingga karakteristik perilaku simulasi sosial tetap utuh.

---

## 2. Cakupan (Scope & Non-Scope)

### Scope:
- Root repositori: `CLAUDE.md`.
- Direktori `.claude/`: `.claude/settings.json`, `.claude/hooks/*.sh`, update 11 file `.claude/agents/*.md`.
- Backend Step 4: `backend/app/services/report_agent.py`.
- Backend Step 0: `backend/app/services/web_research_service.py`.
- Unit test verifikasi backend: memastikan tidak ada syntax error / import error pada modul yang dimodifikasi.

### Non-Scope (Pengecualian Mutlak):
- **DILARANG KERAS MENGUBAH**: `MultiPlatformSimulator`, `OasisProfileGenerator`, `simulation_runner.py`, atau prompt aksi agen di Step 3. Agen simulasi media sosial harus tetap dapat berhalusinasi, bias, dan menyebarkan desas-desus demi realisme sosiologis.

---

## 3. Rincian Fase Implementasi

### Fase 1: Meta-Orchestration Guardrails & Deterministik Hooks
- Membuat `CLAUDE.md` di root repositori dengan protokol epistemik.
- Membuat direktori `.claude/hooks/`:
  - `block-blind-installs.sh` (PreToolUse, matcher Bash)
  - `verify-after-edit.sh` (PostToolUse, matcher Edit|Write)
  - `epistemic-audit.sh` (Stop hook)
- Membuat `.claude/settings.json` yang mendaftarkan hook di atas dengan parsing JSON via stdin.
- Memperbarui 11 file agen di `.claude/agents/*.md` dengan kontrak delegasi 3 tingkat.

### Fase 2: Epistemic Grounding & Safe Abstention pada ReportAgent (Step 4)
- Menambahkan aturan epistemic protocol pada `SECTION_SYSTEM_PROMPT_TEMPLATE` di `backend/app/services/report_agent.py`.
- Menambahkan penanganan graceful degradation jika `InsightForge` atau Zep tool tidak menemukan bukti: merespon dengan `ABSTAIN_INSUFFICIENT_CONTEXT` / pernyataan informatif alih-alih melempar exception atau memicu infinite loop ReACT.

### Fase 3: Pelabelan Ground-Truth Epistemik pada Web Research (Step 0)
- Menambahkan tagging status epistemik (`[VERIFIED]`, `[UNVERIFIED]`, `[ASSUMED]`) pada `ResearchReport` di `backend/app/services/web_research_service.py`.
- Memastikan fakta yang diekstrak mengaitkan domain sumber yang kredibel.

### Fase 4: Validasi & Pengujian
- Jalankan pemeriksaan lint/syntax pada file Python yang diubah (`python3 -m py_compile backend/app/services/report_agent.py`, dll.).
- Pastikan hak eksekusi `chmod +x` pada semua script hook di `.claude/hooks/`.
- Jalankan test suite backend yang relevan untuk memastikan tidak ada regresi.
