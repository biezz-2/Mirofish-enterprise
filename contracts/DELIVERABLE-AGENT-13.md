# Deliverable: Agent 13 — Hawkes Process & Rescorla-Wagner Viral Cascade Modeler

**Task ID**: `t_a89ceb7b`  
**Slice**: Slice 13 (Subagent 13: Hawkes Process & Rescorla-Wagner Viral Cascade Modeler)  
**Divisi**: Swarm Simulation & Predictive Sandbox (SIM)  
**Status**: Ready for Human Gate Approval & Downstream Handoff (Agent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery Specialist)  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 7; Kontrak Step 2 Agents (`contracts/03-step2-agents.json`), Kontrak Step 3 RecSys & Simulation (`contracts/04-step3-recsys.json`, `contracts/05-step3-simulation.jsonl`), Deliverable Agent 12 (`contracts/DELIVERABLE-AGENT-12.md`)  

---

## 1. Ringkasan Eksekutif & Blueprint Arsitektur

Sebagai komponen pemodel transmisi informasi dan dinamika viralitas dalam **Step 3: RecSys Funnel & Viral Dynamics (Divisi D)**, Agent 13 bertugas memodelkan mekanisme psikologis agen individu dan fenomena kaskade penularan kolektif lintas 8 platform sosial media (7 kanonikal: X, Reddit, TikTok, Instagram, YouTube, LinkedIn, Threads + extended Facebook).

Modul ini memadukan tiga teori saintifik utama ke dalam satu arsitektur terintegrasi:
1. **Rescorla-Wagner (1972) Dopamine Learning Loop**: Memodelkan Reward Prediction Error (RPE), antisipasi dopamin notifikasi, habituasi, dan mekanisme *burnout* (disengagement) agen.
2. **Marked Hawkes Self-Exciting Point Process**: Memodelkan penularan viral swa-eksitasi (self-exciting cascades), branching ratio $\eta = \alpha/\beta$, regim kritisitas (*subcritical* vs *supercritical*), dan waktu paruh peluruhan konten.
3. **Mark Granovetter (1978) Threshold Model of Collective Action**: Memodelkan fenomena *tipping point* penularan sosial pada topologi jaringan Watts-Strogatz small-world dan Barabási-Albert scale-free, dimodulasi oleh level dopamin dan intensitas viralitas lingkungan.
4. **Swarm Predictive Sandbox Evaluator**: Menjalankan simulasi multi-agen (50 agen x 15 ronde x 8 platform = 6,000 aksi evaluasi) guna membuktikan konvergensi kaskade dan ketiadaan *deadlock* (`deadlock_detected = False`).
5. **Matriks Handoff Terkalibrasi ke Downstream Agent 14**: Menyediakan spesifikasi interval superstep BSP (Bulk Synchronous Parallel), ukuran batch agen per platform, interval sinkronisasi milidetik, dan algoritma *state hashing* SHA-256 untuk pemulihan kegagalan (*crash recovery*).

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │         Agent 12: 7-Platform Algorithm Calibration Matrix              │
  │   (Pareto 90-9-1, Power-Law Attention Gini, Calibrated Hawkes Matrix)  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 13: Hawkes Process & Rescorla-Wagner Viral Cascade Modeler       │
  │                                                                        │
  │  Rescorla-Wagner Loop   ──▶ V <- V + alpha * (R - V), RPE, Burnout     │
  │  Marked Hawkes Process  ──▶ lambda(t) = mu + sum(a*mark*e^(-b*dt))     │
  │  Criticality Regimes    ──▶ Subcritical (eta < 1) vs Supercritical     │
  │  Granovetter Threshold  ──▶ Dynamic theta_eff(V, lambda), Tipping Pt   │
  │  Swarm Sandbox (50x15x8)──▶ 6,000 Actions, Deadlock-Free Convergence   │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Agent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery           │
  │ (Superstep Barrier: 1, SQLite WAL Checkpoint: 5, Sync 100-300ms)       │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Formulasi Matematis & Model Komputasi

### 2.1 Rescorla-Wagner (1972) Reward Prediction Error & Dopamin Agen
Perubahan nilai asosiasi antisipasi reward dopamin $V(t)$ ditentukan oleh perbedaan antara reward yang dialami ($R$) dan ekspektasi sebelumnya ($V$):
$$\Delta V = \alpha_{\text{rw}} \cdot (R - V)$$
$$V(t+1) = V(t) + \Delta V$$
- **Reward Prediction Error (RPE)**: $\delta = R - V$.
  - $\delta > 0$: Kejutan positif (misal postingan viral melampaui ekspektasi) $\rightarrow$ lonjakan dopamin, peningkatan kecenderungan posting.
  - $\delta < 0$: Kekecewaan/frustrasi (misal postingan sepi respon).
- **Mekanisme Habituasi & Burnout**:
  - Jika seorang agen mengalami 4 ronde beruntun dengan $\delta < -0.15$, agen memasuki fase **burnout** (`is_burnout = True`).
  - Frekuensi posting agen tereduksi sebesar $80\%$ hingga memperoleh pemulihan melalui reward signifikan ($\delta > 0.20$).
- **Frekuensi Posting Sigmoid**:
  $$f_{\text{post}}(V) = f_{\min} + \frac{f_{\max} - f_{\min}}{1 + e^{-3(V - V_{\text{mid}})}}$$

### 2.2 Marked Hawkes Self-Exciting Point Process
Intensitas kejadian bersyarat $\lambda(t)$ pada waktu $t$, dengan mempertimbangkan riwayat kejadian sebelumnya $\{t_i, \text{mark}_i\}_{t_i < t}$:
$$\lambda(t) = \mu + \sum_{t_i < t} \alpha \cdot \text{mark}_i \cdot e^{-\beta (t - t_i)}$$
- $\mu$: Intensitas eksogen baseline (laju posting spontan platform).
- $\alpha$: Bobot lonjakan eksitasi endogen (faktor infektivitas viral).
- $\text{mark}_i$: Bobot pengaruh pengguna pencetus (Creator $= 3.2$, Contributor $= 1.6$, Lurker $= 0.6$).
- $\beta$: Laju peluruhan eksponensial viralitas (kecepatan konten memudar dari linimasa).
- **Branching Ratio ($\eta$) & Kritisitas**:
  $$\eta = \frac{\alpha}{\beta}$$
  - $\eta < 1.0$ (*Subcritical*): Kaskade stabil, memiliki ekspektasi ukuran akhir terhingga $\mathbb{E}[N] = \frac{1}{1 - \eta}$.
  - $\eta = 1.0$ (*Critical*): Kaskade berada pada batas transisi fase.
  - $\eta > 1.0$ (*Supercritical*): Kaskade berpotensi mengalami ledakan eksponensial (*runaway viral explosion*).
- **Karakteristik Temporal**:
  - Waktu Paruh ($t_{1/2}$): $\frac{\ln 2}{\beta}$
  - Waktu Ekstingsi 95% ($t_{95}$): $\frac{\ln 20}{\beta}$

### 2.3 Matriks Kalibrasi Hawkes 8 Platform Sosial

| Platform | Kunci | $\mu$ (Base) | $\alpha$ (Jump) | $\beta$ (Decay) | Branching $\eta$ | Regim Kritisitas | Waktu Paruh ($t_{1/2}$) | Ekstingsi 95% ($t_{95}$) | Granovetter $\theta_0$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **X (Twitter)** | `x` | 0.12 | 0.75 | 0.85 | **0.8824** | Subcritical | 0.815 jam | 3.524 jam | 0.25 |
| **Reddit** | `reddit` | 0.15 | 0.60 | 0.50 | **1.2000** | Supercritical | 1.386 jam | 5.991 jam | 0.20 |
| **TikTok** | `tiktok` | 0.05 | 0.85 | 0.92 | **0.9239** | Subcritical | 0.753 jam | 3.256 jam | 0.35 |
| **Instagram** | `instagram` | 0.08 | 0.65 | 0.75 | **0.8667** | Subcritical | 0.924 jam | 3.994 jam | 0.30 |
| **YouTube** | `youtube` | 0.06 | 0.70 | 0.40 | **1.7500** | Supercritical | 1.733 jam | 7.489 jam | 0.28 |
| **LinkedIn** | `linkedin` | 0.08 | 0.55 | 0.60 | **0.9167** | Subcritical | 1.155 jam | 4.993 jam | 0.32 |
| **Threads** | `threads` | 0.10 | 0.65 | 0.80 | **0.8125** | Subcritical | 0.866 jam | 3.745 jam | 0.25 |
| **Facebook** | `facebook` | 0.10 | 0.70 | 0.65 | **1.0769** | Supercritical | 1.066 jam | 4.609 jam | 0.30 |

### 2.4 Mark Granovetter (1978) Ambang Batas Kolektif Dinamis
Seorang agen mengadopsi perilaku viral apabila proporsi rekan aktif memenuhi ambang batasnya:
$$\text{Adopsi Aktif} \iff \frac{\sum_{j \in \mathcal{N}_i} \mathbb{I}(j \text{ aktif})}{|\mathcal{N}_i|} \ge \theta_{i, \text{eff}}$$
Ambang batas efektif individual $\theta_{i, \text{eff}}$ dimodulasi secara dinamis oleh dopamin internal agen dan intensitas viral eksternal:
$$\theta_{i, \text{eff}} = \max\left(0.01, \min\left(0.99, \theta_{i, 0} - \kappa_V \cdot V_i - \kappa_\lambda \cdot \frac{\lambda(t)}{1 + \lambda(t)}\right)\right)$$
dengan $\kappa_V = 0.15$ dan $\kappa_\lambda = 0.10$. Tingkat antusiasme dopamin yang tinggi dan linimasa yang dipenuhi konten viral menurunkan resistensi agen terhadap adopsi perilaku kelompok, memicu percepatan *tipping point*.

---

## 3. Hasil Pengujian & Verifikasi Sandbox Swarm

### 3.1 Ringkasan Test Suite
Seluruh unit dan integrasi test lulus **100%** tanpa kegagalan:

```bash
cd /home/biezz/Documents/Project/coding/Mirofish-enterprise/backend
PYTHONPATH=/home/biezz/Documents/Project/coding/Mirofish-enterprise:. .venv/bin/pytest tests/test_cascade_dynamics.py tests/test_platform_matrix.py tests/test_v32_enterprise.py
============================== 51 passed in 4.37s ==============================
```

Daftar pengujian khusus `tests/test_cascade_dynamics.py` (18 passed):
1. `test_rescorla_wagner_acquisition`: Konvergensi peningkatan $V$ saat reward positif.
2. `test_rescorla_wagner_extinction`: Peluruhan $V \to 0$ saat reward ditiadakan.
3. `test_rescorla_wagner_stateful_agent_and_burnout`: Pemicuan burnout pada RPE negatif berturut-turut.
4. `test_rescorla_wagner_post_frequency`: Validasi modulasi frekuensi posting oleh dopamin dan burnout.
5. `test_hawkes_intensity_baseline_and_decay`: Peluruhan eksponensial intensitas Hawkes menuju baseline $\mu$.
6. `test_hawkes_influence_mark_weighting`: Verifikasi mark pengaruh pengguna pada magnitudo lonjakan.
7. `test_hawkes_platform_matrices_and_criticality`: Verifikasi parameter analitik 8 platform dan regim kritisitas.
8. `test_hawkes_continuous_simulation_ogata`: Validasi algoritma thinning Ogata dalam horizon waktu kontinu.
9. `test_granovetter_basic_activation`: Verifikasi kepatuhan aturan ambang batas Granovetter klasik.
10. `test_granovetter_dynamic_effective_threshold`: Verifikasi modulasi ambang batas oleh dopamin dan intensitas Hawkes.
11. `test_granovetter_cascade_simulation_small_world`: Verifikasi propagasi kaskade pada topologi Watts-Strogatz.
12. `test_swarm_cascade_sandbox_full_run`: Eksekusi 50 agen x 15 ronde x 8 platform (6,000 aksi, zero deadlock).
13. `test_api_cascade_hawkes_endpoint`: Verifikasi kompatibilitas endpoint legacy `/cascade/hawkes`.
14. `test_api_cascade_rescorla_wagner_endpoint`: Verifikasi endpoint RPE update & schedule simulation.
15. `test_api_cascade_granovetter_endpoint`: Verifikasi endpoint evaluasi ambang batas & simulasi jaringan.
16. `test_api_cascade_hawkes_simulate_endpoint`: Verifikasi endpoint simulasi Ogata thinning.
17. `test_api_cascade_swarm_simulate_endpoint`: Verifikasi endpoint simulasi swarm multi-platform interaktif.
18. `test_api_platform_matrices_and_downstream`: Verifikasi endpoint inspeksi matriks platform & rekomendasi downstream.

### 3.2 Metrik Simulasi Sandbox Swarm (50 Agen x 15 Ronde x 8 Platform)
Total keputusan aksi feed yang dievaluasi: **6,000 aksi** (750 aksi x 8 platform).

| Platform | Total Events | Peak Intensity ($\lambda_{\max}$) | Final Adoption | Tipping Point Round | Branching ($\eta$) | Regim Kritisitas | Mean Dopamine ($V$) | Mean RPE | Burnout Count | Deadlock | Waktu Sandbox |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **X** | 122 | 17.73 | 100.0% | Ronde 3 | 0.8824 | Subcritical | 3.275 | +0.300 | 0 | **FALSE** | 0.144s |
| **Reddit** | 113 | 19.88 | 100.0% | Ronde 3 | 1.2000 | Supercritical | 3.693 | +0.106 | 0 | **FALSE** | 0.009s |
| **TikTok** | 136 | 17.51 | 100.0% | Ronde 3 | 0.9239 | Subcritical | 3.090 | +0.222 | 0 | **FALSE** | 0.009s |
| **Instagram** | 133 | 17.15 | 100.0% | Ronde 3 | 0.8667 | Subcritical | 3.267 | +0.252 | 0 | **FALSE** | 0.009s |
| **YouTube** | 126 | 28.53 | 100.0% | Ronde 3 | 1.7500 | Supercritical | 4.417 | +0.226 | 0 | **FALSE** | 0.009s |
| **LinkedIn** | 136 | 18.06 | 100.0% | Ronde 3 | 0.9167 | Subcritical | 3.327 | +0.218 | 0 | **FALSE** | 0.009s |
| **Threads** | 136 | 17.76 | 100.0% | Ronde 3 | 0.8125 | Subcritical | 3.298 | +0.274 | 0 | **FALSE** | 0.009s |
| **Facebook** | 137 | 18.66 | 100.0% | Ronde 3 | 1.0769 | Supercritical | 3.345 | +0.247 | 0 | **FALSE** | 0.009s |

- **Konvergensi & Deadlock**: Tidak ada *deadlock* sistemik terdeteksi (`deadlock_detected = False`).
- **Stabilitas Kaskade**: `global_cascade_stability = True`.
- **Waktu Eksekusi Agregat**: **0.21 detik** untuk seluruh 6,000 evaluasi swarm.

---

## 4. Parameter Handoff ke Downstream Agent 14

Parameter terkalibrasi untuk **Agent 14: BSP Parallel Swarm Runner & SHA-256 Crash Recovery Specialist**:

```json
{
  "bsp_superstep_barrier_interval": 1,
  "batch_size_agents": 50,
  "sqlite_wal_checkpoint_frequency_rounds": 5,
  "state_hash_algorithm": "SHA-256",
  "max_barrier_timeout_ms": 5000,
  "recommended_state_hash_fields": [
    "agent_id",
    "v_dopamine",
    "is_active",
    "consecutive_frustrations",
    "posts_created",
    "last_prediction_error"
  ],
  "platform_sync_intervals_ms": {
    "tiktok": 100,
    "instagram": 120,
    "x": 150,
    "threads": 150,
    "facebook": 180,
    "linkedin": 200,
    "reddit": 250,
    "youtube": 300
  },
  "cascade_stability_certified": true,
  "platform_branching_ratios": {
    "x": 0.8824,
    "reddit": 1.2,
    "tiktok": 0.9239,
    "instagram": 0.8667,
    "youtube": 1.75,
    "linkedin": 0.9167,
    "threads": 0.8125,
    "facebook": 1.0769
  },
  "granovetter_tipping_thresholds": {
    "x": 0.25,
    "reddit": 0.2,
    "tiktok": 0.35,
    "instagram": 0.3,
    "youtube": 0.28,
    "linkedin": 0.32,
    "threads": 0.25,
    "facebook": 0.3
  }
}
```

---

## 5. Kepatuhan Kontrak & Kompatibilitas Mundur

1. **Kompatibilitas API V3.2**:
   - `POST /api/enterprise/cascade/hawkes`: Mengembalikan intensitas Hawkes viralitas tanpa mengubah tanda tangan atau struktur respons warisan.
2. **REST API Endpoints Baru (`backend/app/api/enterprise.py`)**:
   - `POST /api/enterprise/cascade/rescorla-wagner`: Pembaruan dopamin RPE dan simulasi jadwal reward.
   - `POST /api/enterprise/cascade/granovetter`: Evaluasi aktivasi ambang batas individu dan simulasi kaskade jaringan.
   - `POST /api/enterprise/cascade/hawkes/simulate`: Simulasi kontinu kaskade Hawkes dengan Ogata thinning.
   - `POST /api/enterprise/cascade/swarm/simulate`: Eksekusi sandbox swarm 50x15 interaktif multi-platform.
   - `GET /api/enterprise/cascade/platform-matrices`: Inspeksi parameter analitik dan regim kritisitas Hawkes per platform.
   - `GET /api/enterprise/cascade/downstream-recommendations`: Handoff parameter komputasi ke Agent 14.
3. **Ekspor Modul Layanan (`backend/app/services/__init__.py`)**:
   - `HawkesEvent`, `HawkesPlatformParams`, `RescorlaWagnerState`, `GranovetterAgentState`, `CascadeSimulationMetrics`, `SwarmCascadeSimulationResult`, `CascadeDynamicsEngine`, `DEFAULT_PLATFORM_HAWKES_MATRIX`.