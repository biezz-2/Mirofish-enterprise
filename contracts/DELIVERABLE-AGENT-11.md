# Deliverable: Agent 11 — 3-Stage RecSys Funnel Engineer

**Task ID**: `t_459ee3c9`  
**Slice**: Slice 11 (Subagent 11: 3-Stage RecSys Funnel Engineer)  
**Divisi**: Swarm Simulation & Predictive Sandbox (SIM)  
**Status**: Ready for Human Gate Approval & Downstream Handoff (Agent 12: 7-Platform Calibration Matrix & Agent 13: Hawkes Viral Cascade Modeler)  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 7; Kontrak Step 2 Agents (`contracts/03-step2-agents.json`), Kontrak Step 3 RecSys (`contracts/04-step3-recsys.json`)  

---

## 1. Ringkasan Eksekutif & Blueprint Arsitektur

Sebagai komponen corong rekomendasi feed sentral dalam **Step 3: RecSys Funnel & Viral Dynamics (Divisi D)**, Agent 11 bertugas mengimplementasikan corong rekomendasi feed 3-tahap tingkat enterprise untuk memastikan populasi agen swarm menerima distribusi paparan konten yang seimbang, tidak monoton, dan tahan terhadap fenomena *filter bubble* atau *echo chamber*.

Modul ini mengintegrasikan:
1. **Tahap 1 — Candidate Generation (High-Throughput Retrieval)**:
   - Pengambilan kandidat berskala tinggi dari ribuan item korpus mentah menuju batas kandidat terkontrol ($K = 50 - 60$ kandidat, terkalibrasi dengan rekomendasi Agent 10: `recommended_candidate_limit = 60`).
   - Retrieval berbasis gabungan multi-sinyal:
     - **Graf Homofili Jaringan**: Deteksi kedekatan graf relasi (author in network / following network).
     - **Kemiripan Kosinus Embedding Semantik**: Evaluasi dot product ternormalisasi antara vektor preferensi agen dan vektor embedding konten.
     - **Stance Alignment**: Kedekatan afinitas ideologis $1.0 - \min(1.0, |s_{\text{item}} - s_{\text{user}}| / 2.0)$.
     - **Base & Quality Composite**: Bobot kredibilitas dan kualitas intrinsik konten.
2. **Tahap 2 — Heavy Ranking (Multi-task Scoring 7 Platform)**:
   - Prediksi keterlibatan granular melalui model multi-task logistik:
     - $P(\text{like})$: Dipicu oleh afinitas stance, kualitas konten, dan otoritas kreator.
     - $P(\text{share})$ / Retweet: Dipicu oleh gairah emosional (*arousal*), kontroversi, dan keselarasan ideologis.
     - $P(\text{reply})$: Dipicu oleh kontroversi dan friksi stance (*cognitive dissonance / debate stimulation*).
     - $\widehat{T}_{\text{dwell}}$: Estimasi durasi konsumsi kognitif terkalibrasi dengan model DDM Agent 10.
   - Pembobotan spesifik untuk 7 platform target (X, Reddit, TikTok, Instagram, YouTube, LinkedIn, Threads).
3. **Tahap 3 — Re-Ranking & Diversity (Peredaman Ruang Gema & Serendipitas)**:
   - **Exponential Time Decay**: Penalti keusangan konten $\exp(-\lambda_{\text{decay}} \cdot \Delta t_{\text{hours}})$.
   - **Echo Chamber Damping**: Redam konten terlalu homogen ($|s_{\text{item}} - s_{\text{user}}| < 0.20$) dengan faktor redaman adaptif $\delta \in [0.40, 0.80]$ (default 0.75 dari Agent 10), serta memberikan bonus eksplorasi untuk konten sudut pandang moderat / kontras seimbang.
   - **Sequential MMR Topic Diversity**: Penalti penumpukan topik yang berulang secara berurutan dalam feed atas.
   - **$\epsilon$-Greedy Serendipity Exploration**: Injeksi item eksploratif dari luar kluster dominan dengan probabilitas $\epsilon = 0.05 - 0.10$.
4. **Metrik Keanekaragaman Informasi**:
   - Kalkulasi Shannon Entropy $H = -\sum p_i \log_2 p_i$ untuk distribusi topik.
   - Dispersi stance (varians & polar spread).
   - Indeks kerentanan ruang gema (*echo chamber index*).
5. **Swarm Predictive Sandbox Simulation**:
   - Simulasi 50 agen heterogen x 15 ronde (500 item korpus) memvalidasi penurunan polarisasi feed, kestabilan konvergensi tanpa deadlock (`deadlock_detected = False`), dan performa komputasi tinggi (< 2 detik untuk 15 ronde simulasi swarm).
6. **Kalibrasi Downstream untuk Agent 12 & Agent 13**:
   - Menerbitkan rekomendasi terkalibrasi untuk matriks platform Agent 12 (`recommended_virality_decay_rate`, `calibrated_echo_damping`) dan pemodel cascade Hawkes Agent 13 (`cascade_damping_factor`, `recommended_hawkes_alpha`, `recommended_rescorla_alpha`).

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │         Agent 10: Decision Engine (Nested Logit, DDM, Prospect)        │
  │     (recommended_candidate_limit=60, damping=0.75, epsilon=0.10)       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │            Agent 11: 3-Stage RecSys Funnel Engineer                    │
  │                                                                        │
  │  Stage 1: Candidate Generation ──▶ Homophily + Cosine Sim + Stance     │
  │  Stage 2: Heavy Ranking        ──▶ Multi-Task (Like, Share, Reply,     │
  │                                    Dwell) terbobot 7 Platform          │
  │  Stage 3: Re-Ranking           ──▶ Echo Chamber Damping (0.40 - 0.80), │
  │                                    Time Decay, MMR & eps-Serendipity   │
  │  Swarm Sandbox Validation      ──▶ 50 Agents x 15 Rounds, Zero Deadlock│
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
  ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
  │ Agent 12: 7-Platform Calibration  │   │ Agent 13: Hawkes & Rescorla-      │
  │ Matrix Specialist                 │   │ Wagner Viral Cascade Modeler      │
  │ (calibrated_echo_damping: 0.75,   │   │ (cascade_damping_factor: 0.75,    │
  │  virality_decay_rate: 0.85)       │   │  recommended_hawkes_alpha: 0.637) │
  └───────────────────────────────────┘   └───────────────────────────────────┘
```

---

## 2. Formulasi Matematis & Algoritma Corong 3-Tahap

### 2.1 Tahap 1: Candidate Generation (Retrieval)
Menyaring korpus besar $M \approx 500 - 1000+$ item menjadi $K \approx 50 - 60$ kandidat relevan:
$$\text{Score}_{\text{stage1}} = 0.35 \cdot H_{\text{stance}} + 0.25 \cdot A_{\text{net}} + 0.25 \cdot S_{\text{semantic}} + 0.15 \cdot Q_{\text{base}}$$
di mana:
- $H_{\text{stance}} = 1.0 - \min(1.0, |s_{\text{item}} - s_{\text{user}}| / 2.0)$
- $A_{\text{net}} \in \{1.0 \text{ (direct network)}, 0.8 \text{ (in-network author)}, 0.25 \text{ (out-network)}\}$
- $S_{\text{semantic}} = 0.5 + 0.5 \cdot \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2 + 10^{-12}}$
- $Q_{\text{base}} = 0.6 \cdot \text{base\_score} + 0.4 \cdot \text{quality\_score}$

### 2.2 Tahap 2: Heavy Ranking (Multi-task Scoring)
Memprediksi ekspektasi keterlibatan multi-task terbobot platform:
$$\text{Score}_{\text{stage2}} = w_{\text{like}} P(\text{like}) + w_{\text{share}} P(\text{share}) + w_{\text{reply}} P(\text{reply}) + w_{\text{dwell}} \frac{\widehat{T}_{\text{dwell}}}{3000}$$
dengan logistik multi-task:
- $P(\text{like}) = \sigma(-0.6 + 1.5 H_{\text{stance}} + 1.2 Q + 0.8 \text{base} + 0.4 \text{auth})$
- $P(\text{share}) = \sigma(-1.1 + 1.3 C + 1.1 A + 0.8 \text{auth} + 0.9 H_{\text{stance}})$
- $P(\text{reply}) = \sigma(-1.0 + 1.4 C + 1.2 F_{\text{stance}} + 0.6 Q)$
- $\widehat{T}_{\text{dwell}} = 300 + 1100 Q + 750 V_{\text{rich}} + 450 H_{\text{stance}} \text{ (ms)}$

Matriks Bobot 7 Platform:
- **X**: `w_like: 0.25, w_share: 0.35, w_reply: 0.25, w_dwell: 0.15`
- **Reddit**: `w_like: 0.15, w_share: 0.10, w_reply: 0.55, w_dwell: 0.20`
- **TikTok**: `w_like: 0.20, w_share: 0.20, w_reply: 0.10, w_dwell: 0.50`
- **Instagram**: `w_like: 0.40, w_share: 0.25, w_reply: 0.15, w_dwell: 0.20`
- **YouTube**: `w_like: 0.20, w_share: 0.15, w_reply: 0.15, w_dwell: 0.50`
- **LinkedIn**: `w_like: 0.30, w_share: 0.30, w_reply: 0.25, w_dwell: 0.15`
- **Threads**: `w_like: 0.30, w_share: 0.20, w_reply: 0.35, w_dwell: 0.15`

### 2.3 Tahap 3: Re-Ranking & Regulasi Ruang Gema
1. **Exponential Time Decay**:
   $$\text{Decay} = \exp(-\lambda_{\text{time}} \cdot \Delta t_{\text{hours}})$$
2. **Echo Chamber Damping**:
   Untuk $\Delta s = |s_{\text{item}} - s_{\text{user}}|$:
   - Jika $\Delta s < 0.20$ (konten echo chamber homogen):
     $$\text{Damping} = 1.0 - (\delta \times 0.5), \quad \delta \in [0.40, 0.80]$$
   - Jika $\Delta s \ge 0.20$ (konten berimbang / moderat kontras):
     $$\text{Damping} = 1.15 \text{ (bonus eksplorasi moderat)}$$
3. **Sequential MMR Topic Diversity**:
   $$\text{Penalty}_{\text{topic}} = 1.0 - \min(0.40, k \times 0.08)$$
   di mana $k$ adalah frekuensi topik tersebut telah muncul di feed atas.
4. **$\epsilon$-Greedy Serendipity Injection**:
   Dengan probabilitas $\epsilon \in [0.05, 0.10]$, item serendipitas dari luar kluster teratas diinjeksi ke posisi teratas feed untuk memecah jebakan gelembung filter.

---

## 3. Hasil Pengujian & Verifikasi Sandbox

Seluruh 15 unit/integrasi test untuk Agent 11 dan 64 enterprise test suite gabungan (Agent 08, 09, 10, 11, dsb.) lulus dengan **100% kelulusan** dan **0 regresi**:

```bash
backend/.venv/bin/pytest tests/test_recsys_funnel.py
============================== 15 passed in 2.51s ==============================

backend/.venv/bin/pytest tests/test_v32_enterprise.py tests/test_humanoid_needs.py tests/test_psychometrics.py tests/test_decision_engine.py tests/test_recsys_funnel.py
============================== 64 passed in 3.67s ==============================
```

### 3.1 Metrik Simulasi Swarm 50 Agen x 15 Ronde (750 Keputusan Feed)
- **Eksekusi Komputasi**: 1.856 detik (jauh di bawah batas toleransi 10 detik).
- **Rata-rata Shannon Topic Entropy**: **2.506** (menunjukkan keanekaragaman topik yang kaya dan stabil).
- **Indeks Ruang Gema (Echo Chamber Index)**:
  - Baseline tanpa damping: **0.405** (40.5% konten terjebak di echo zone).
  - Dengan peredaman adaptif ($\delta = 0.75, \epsilon = 0.10$): **0.299** (29.9%).
  - **Reduksi Ruang Gema**: **26.17%** penurunan polarisasi feed.
- **Deteksi Deadlock**: `deadlock_detected = False`.
- **Rata-rata Varians Stance Feed**: **0.1296**.

### 3.2 Parameter Handoff ke Downstream Agent 12 & 13
1. **Ke Agent 12 (7-Platform Calibration Matrix Specialist)**:
   - `recommended_virality_decay_rate`: `0.85`
   - `calibrated_echo_damping`: `0.75`
   - `recommended_epsilon`: `0.10`
   - `target_platform`: `"x"`
   - `status`: `"CALIBRATED"`
2. **Ke Agent 13 (Hawkes Process & Rescorla-Wagner Viral Cascade Modeler)**:
   - `cascade_damping_factor`: `0.75`
   - `recommended_hawkes_alpha`: `0.637`
   - `recommended_rescorla_alpha`: `0.25`
   - `granovetter_activation_barrier`: `0.30`

---

## 4. Kepatuhan Kontrak & Kompatibilitas Mundur

1. **Kompatibilitas API V3.2**:
   - `POST /api/enterprise/recsys/rank`: Tetap mendukung payload legacy dan mengembalikan status sukses, shannon entropy, serta items terurut.
2. **REST API Endpoints Baru (`backend/app/api/enterprise.py`)**:
   - `POST /api/enterprise/recsys/funnel`: Full 3-stage funnel dengan `user_profile`, `platform`, `damping_factor`, `epsilon`.
   - `POST /api/enterprise/recsys/simulate-swarm`: Simulasi sandbox multi-agen heterogen.
   - `POST /api/enterprise/recsys/diversity-metrics`: Evaluasi komprehensif metrik diversitas & Shannon entropy.
   - `GET /api/enterprise/recsys/weights`: Bobot multi-task platform rekomendasi 7 platform.
3. **Ekspor Modul Layanan (`backend/app/services/__init__.py`)**:
   - `FeedItem`, `UserProfile`, `FunnelResult`, `SwarmRecSysSimulationResult`, `RecSysFunnel`, `PLATFORM_RECSYS_WEIGHTS`.
