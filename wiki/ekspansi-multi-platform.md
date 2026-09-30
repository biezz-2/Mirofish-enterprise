---
title: Spesifikasi 7 Platform Media Sosial MiroFish
type: concept
tags: [multi-platform, social-simulation, algorithms, agent-behavior, ocean-psychology, v3.1]
related:
  - "[[index]]"
  - "[[arsitektur]]"
  - "[[kesiapan-operasional]]"
  - "[[codemap]]"
sources:
  - backend/app/services/oasis_profile_generator.py
  - backend/app/services/simulation_config_generator.py
  - backend/scripts/run_parallel_simulation.py
---

# Spesifikasi 7 Platform Media Sosial: MiroFish v3.1 Enterprise

Dokumen ini menyajikan rancangan teknis mendalam dan spesifikasi kuantitatif untuk ekspansi ekosistem simulasi MiroFish dari dual-platform (Twitter dan Reddit) menjadi **7 Platform Media Sosial Terpadu**: **Twitter**, **X**, **Reddit**, **TikTok**, **Instagram**, **Facebook**, dan **Threads**. 

Setiap platform memiliki arsitektur algoritma rekomendasi distingtif, dinamika ruang tindakan (*action space*), parameterisasi peluruhan informasi, serta profil perilaku psikologis agen.

---

## 1. Analisis Karakteristik Per Platform

```
+-------------------------------------------------------------------------------------------------------+
|                                    LANSKAP 7 PLATFORM MIROFISH v3.1                                   |
+-------------------+--------------------+--------------------+--------------------+--------------------+
| PLATFORM          | TIPOLOGI KONTEN    | FOKUS ALGORITMA    | DINAMIKA SOSIAL    | POLA INTERAKSI     |
+-------------------+--------------------+--------------------+--------------------+--------------------+
| 1. Twitter        | Mikro-teks cepat   | Kronologis & Viral | Cascades Cepat     | Retweet, Quote     |
| 2. X              | Teks panjang/Media | Pembagian Cuan/ForU| Polarisasi Ekstrem | Opini berbayar     |
| 3. Reddit         | Thread bertingkat  | Karma & Komunitas  | Diskusi Mendalam   | Upvote, Subreddit  |
| 4. TikTok         | Video mikro/Skrip  | Minat Murni & Loop | Replikasi Viral    | Duet, Sound Contag |
| 5. Instagram      | Visual & Estetika  | Jaringan Afinitas  | Citra Diri Positif | Like, Save, DM     |
| 6. Facebook       | Multi-format/Grup  | Ikatan Keluarga/Kl | Echo Chamber Kuat  | Reaction Emosi     |
| 7. Threads        | Diskusi teks santai| Terkoneksi IG/Fedi | Percakapan Ringan  | Repost, Mentions   |
+-------------------+--------------------+--------------------+--------------------+--------------------+
```

### 1.1 Twitter (Legacy Short-Form Microblogging)
- **Fokus**: Distribusi berita kilat, breaking news, dan pergolakan tagar (*hashtag trending*).
- **Karakteristik**: Batas teks ketat (280 karakter), laju aliran linimasa sangat cepat, dependensi kuat pada graf pengikut (*follower-graph*).
- **Mekanisme Kaskade**: Satu cuitan dari simpul bereputasi tinggi (*influencer*) dapat memicu ledakan penyebaran informasi (*information cascade*) eksponensial dalam hitungan ronde awal.

### 1.2 X (Algorithmic "For You" & Creator Ecosystem)
- **Fokus**: Monetisasi perhatian, opini bertaji, teks panjang (*long-form articles*), dan polarisasi tinggi.
- **Karakteristik**: Tab "For You" memprioritaskan akun terverifikasi (Blue tick) dan memicu interaksi kontroversial (*rage-baiting*) guna memaksimalkan waktu tonton.
- **Dinamika Khusus**: Fitur *Quote Post* sering kali digunakan sebagai alat counter-argumentasi publik yang membelah jejaring opini menjadi dua faksi tajam.

### 1.3 Reddit (Hierarchical Community & Karma Economy)
- **Fokus**: Diskusi tematik berbasis sub-komunitas (*subreddits*) dengan struktur komentar pohon bersarang (*threaded discussions*).
- **Karakteristik**: Anonimitas tinggi, moderasi berbasis aturan komunitas lokal, serta sistem nilai sosial terukur melalui mekanisme *Upvote* dan *Downvote*.
- **Sensitivitas Bobot**: Postingan dengan sentimen bertentangan dengan konsensus subreddit akan mengalami penalti karma dan tenggelam secara otomatis (*shadow suppression*).

### 1.4 TikTok (Interest-Graph & Short-Video Script Engine)
- **Fokus**: Penyebaran tren berbasis minat murni (*interest-graph*) bukan hubungan sosial pertemanan.
- **Karakteristik**: Agen menyimulasikan pembuatan narasi/skrip konten mikro (15-60 detik) dengan *hook* dramatis pada 3 detik pertama.
- **Daya Tular (*Virality Contagion*)**: Algoritma FYP (*For You Page*) memberikan peluang viralitas tinggi bagi akun kecil sekalipun apabila *engagement completion rate* tinggi.

### 1.5 Instagram (Visual Narrative & Social Curation)
- **Fokus**: Kurasi citra visual, narasi gaya hidup, foto/infografis berseri (*carousel*), dan komentar terkelola.
- **Karakteristik**: Interaksi dominan berupa *Likes*, *Saves*, dan *Shares* via pesan langsung. Bahasa cenderung estetis, positif, atau semi-formal.
- **Dinamika Komentar**: Menghindari perdebatan vulgar terbuka; perdebatan sengit umumnya terjadi di akun portal berita atau akun gosip.

### 1.6 Facebook (Intergenerational Social Graph & High Homophily)
- **Fokus**: Jaringan pertemanan dunia nyata, ikatan keluarga, alumni, dan grup tertutup (*closed communities*).
- **Karakteristik**: Rata-rata usia pengguna lebih variatif; sangat rentan terhadap penyebaran narasi konspirasi, hoaks emosional, dan bias konfirmasi.
- **Ruang Reaksi Afektif**: Menyediakan spektrum emosi lengkap: *Like*, *Love*, *Care*, *Haha*, *Wow*, *Sad*, dan *Angry*, yang mempengaruhi bobot bobot kurasi algoritma umpan (*feed*).

### 1.7 Threads (Conversational Decentralized Microblogging)
- **Fokus**: Percakapan teks berbasis komunitas santai tanpa tekanan matriks metrik agresif seperti X.
- **Karakteristik**: Terhubung secara terpadu dengan graf pertemanan Instagram; algoritma mengutamakan dialog konstruktif dan meminimalisir berita politik keras.

---

## 2. Tabel Karakteristik Kuantitatif 7 Platform

Parameter matematis di bawah ini dimasukkan ke dalam mesin simulasi untuk mengatur kurasi umpan dan evaluasi probabilitas tindakan agen:

| Parameter Simbolik | Twitter | X | Reddit | TikTok | Instagram | Facebook | Threads |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Bobot Kebaruan (\(\lambda_{rec}\))** | 0.45 | 0.35 | 0.20 | 0.50 | 0.25 | 0.15 | 0.40 |
| **Bobot Popularitas (\(\beta_{pop}\))** | 0.30 | 0.40 | 0.35 | 0.35 | 0.45 | 0.30 | 0.25 |
| **Koefisien Ruang Gema (\(\gamma_{echo}\))** | 0.15 | 0.30 | 0.40 | 0.10 | 0.25 | 0.45 | 0.15 |
| **Ambang Batas Viralitas (\(\theta_{viral}\))** | 0.70 | 0.60 | 0.75 | 0.45 | 0.65 | 0.80 | 0.70 |
| **Waktu Paruh Informasi (\(t_{half}\) dlm Ronde)**| 2.5 | 3.5 | 6.0 | 1.8 | 4.5 | 8.0 | 3.0 |
| **Tingkat Kebocoran Silang (\(\sigma_{spill}\))** | 0.35 | 0.40 | 0.25 | 0.50 | 0.30 | 0.20 | 0.30 |
| **Maksimum Karakter Konten** | 280 | 4.000 | 40.000 | 500 (skrip)| 2.200 | 10.000 | 500 |

### 2.1 Ruang Tindakan Legal (*Action Space Enum*) Tiap Platform

Dalam berkas konfigurasi `simulation_config.json`, setiap platform mendefinisikan himpunan aksi yang valid:

```python
PLATFORM_ACTION_SPACES = {
    "twitter": [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST", "FOLLOW", "DO_NOTHING"
    ],
    "x": [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST", "BOOKMARK", 
        "REPLY_LONG", "FOLLOW", "BLOCK", "DO_NOTHING"
    ],
    "reddit": [
        "CREATE_POST", "CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST",
        "LIKE_COMMENT", "DISLIKE_COMMENT", "SEARCH_POSTS", "SEARCH_USER",
        "TREND", "REFRESH", "FOLLOW", "MUTE", "DO_NOTHING"
    ],
    "tiktok": [
        "CREATE_SCRIPT", "LIKE_VIDEO", "COMMENT", "SHARE_TO_FRIENDS",
        "DUET_REACT", "FOLLOW_CREATOR", "SKIP", "DO_NOTHING"
    ],
    "instagram": [
        "CREATE_POST", "LIKE_POST", "CREATE_COMMENT", "SAVE_POST",
        "SHARE_STORY", "FOLLOW", "DO_NOTHING"
    ],
    "facebook": [
        "CREATE_POST", "REACT_LIKE", "REACT_LOVE", "REACT_HAHA", 
        "REACT_WOW", "REACT_SAD", "REACT_ANGRY", "SHARE_FEED", 
        "CREATE_COMMENT", "JOIN_GROUP", "DO_NOTHING"
    ],
    "threads": [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST", 
        "REPLY", "FOLLOW", "DO_NOTHING"
    ]
}
```

---

## 3. Model Matematika Perilaku & Formulasi Probabilitas Aksi

### 3.1 Skoring Relevansi Konten pada Linimasa Agen (\(Score_{i,j}\))
Ketika Agen \(i\) melihat postingan \(j\) pada linimasa platform \(p\), relevansi yang dirasakan dihitung berdasarkan kombinasi linear dari kebaruan, popularitas, dan kesamaan ideologis:

\[
Score_{i,j}^{(p)} = \lambda_{rec}^{(p)} \cdot \exp\left(-\frac{\Delta t_{j}}{t_{half}^{(p)}}\right) + \beta_{pop}^{(p)} \cdot \log_{10}(1 + Eng_{j}) + \gamma_{echo}^{(p)} \cdot \text{Sim}(\mathbf{e}_i, \mathbf{e}_j)
\]

Di mana:
- \(\Delta t_j = t_{now} - t_{created}\) adalah selisih waktu dalam jumlah ronde simulasi.
- \(Eng_j = \text{Likes}_j + 2 \cdot \text{Shares}_j + 1.5 \cdot \text{Comments}_j\) adalah metrik interaksi postingan.
- \(\text{Sim}(\mathbf{e}_i, \mathbf{e}_j) \in [-1, 1]\) adalah *cosine similarity* antara vektor afektif/ideologis Agen \(i\) dan konten \(j\).

### 3.2 Formulasi Pemilihan Aksi Multinomial Softmax
Probabilitas Agen \(i\) mengambil aksi \(k\) pada ronde \(t\) dimodelkan dengan distribusi multinomial logit:

\[
P(\text{Action}_k \mid i, j, p) = \frac{\exp\left( \mathbf{w}_k^T \mathbf{x}_{i,j} + b_k^{(p)} \right)}{\sum_{m \in \mathcal{A}_p} \exp\left( \mathbf{w}_m^T \mathbf{x}_{i,j} + b_m^{(p)} \right)}
\]

Di mana \(\mathbf{x}_{i,j}\) adalah vektor gabungan profil psikologis agen, reputasi pembuat konten, dan skor sentimen:

\[
\mathbf{x}_{i,j} = \left[ O_i, C_i, E_i, A_i, N_i, \text{Rep}_j, Score_{i,j}^{(p)}, \text{Toxicity}_j \right]^T
\]

---

## 4. Profil Perilaku Psikologis Agen

Setiap agen yang dihasilkan oleh `OasisProfileGenerator` (`backend/app/services/oasis_profile_generator.py`) dilengkapi dengan metadata kognitif standar industri:

```json
{
  "agent_id": 42,
  "name": "Bambang Sudarmono",
  "username": "bambang_analis_id",
  "entity_uuid": "c3a1e9b2-7f8d-4e5a-9a1b-3c4d5e6f7a8b",
  "bio": "Pengamat Kebijakan Publik & Pengajar Ekonomi Moneter. Skeptis terhadap narasi viral instan.",
  "ocean_traits": {
    "openness": 0.85,
    "conscientiousness": 0.90,
    "extraversion": 0.45,
    "agreeableness": 0.60,
    "neuroticism": 0.25
  },
  "archetype": "EXPERT_SKEPTIC",
  "linguistic_style": {
    "dialect": "Bahasa Indonesia Formal (PUEBI)",
    "tone": "Objektif, akademis, menyertakan data empiris",
    "slang_tolerance": 0.1
  },
  "platform_affinities": {
    "twitter": 0.8,
    "reddit": 0.9,
    "x": 0.7,
    "tiktok": 0.1,
    "instagram": 0.3,
    "facebook": 0.5,
    "threads": 0.6
  }
}
```

### 4.1 Enam Arketipe Persona Sosial Utama
1. **INFLUENCER / PUBLIC_FIGURE**: Pengikut banyak, tingkat posting tinggi, memprioritaskan validasi sosial dan narasi yang menguntungkan status reputasi.
2. **LURKER / PASSIVE_OBSERVER**: Probabilitas tinggi untuk memilih `DO_NOTHING` atau `LIKE_POST`, jarang membuat konten orisinal, namun menjadi penyumbang rasio penayangan.
3. **EXPERT / SKEPTIC**: Sangat teliti, menolak hoaks, selalu menuntut rujukan sumber faktual, menggunakan bahasa tertata dan logis.
4. **TROLL / INSTIGATOR**: Tingkat *Neuroticism* tinggi dan *Agreeableness* rendah; sengaja memprovokasi kemarahan publik (*flame war*) di kolom komentar.
5. **ECHO_AMPLIFIER / PARTISAN**: Tingkat homofili sangat tinggi; menyebarkan (*repost/share*) informasi apa pun yang mendukung kelompoknya tanpa verifikasi kebenaran.
6. **NEUTRAL / PRAGMATIST**: Bereaksi proporsional, cenderung menengahi perdebatan, memiliki stabilitas emosional tinggi.

### 4.2 Personalisasi Bahasa Indonesia Berorientasi Konteks (PUEBI & Sosiolek)
Instruksi LLM untuk agen disesuaikan berdasarkan platform dan arketipe:
- **X & Twitter**: Menghasilkan mikro-opini singkat, penggunaan singkatan lazim (*dgn, yg, tbh, cmiiw*), tanggapan sarkastik, atau utas analitis berurutan (1/n).
- **Reddit / Kaskus**: Format argumentatif panjang, pemisahan paragraf terstruktur, pemakaian tanda kutip (*quote markdown*), dan gaya diskusi mendalam.
- **TikTok & Instagram**: Gaya bahasa santai, kasual, penggunaan partikel penegas (*sih, nih, deh, dong*), frasa pembuka menarik perhatian (*"Guys, kalian udah tau belum..."*).
- **Facebook**: Tutur kata santun bernuansa kekeluargaan, sering diawali salam, penggunaan emoji afektif, dan kecenderungan membagikan tautan eksternal.

---

## 5. Koordinator Paralel Lintas Platform (*Cross-Platform Parallel Coordinator*)

Untuk mengeksekusi 7 platform secara simultan tanpa terjadinya inkonsistensi waktu atau *race condition*, MiroFish v3.1 menggunakan arsitektur **Synchronized Multi-Worker Pool**:

```
                              ┌──────────────────────────────────┐
                              │  Cross-Platform Orchestrator     │
                              │ (backend/scripts/coordinator.py) │
                              └─────────────────┬────────────────┘
                                                │
             ┌──────────────┬──────────────┬────┴─────────┬──────────────┬──────────────┐
             ▼              ▼              ▼              ▼              ▼              ▼
       ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
       │  Twitter  │  │     X     │  │  Reddit   │  │  TikTok   │  │ Instagram │  │ Facebook  │
       │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │
       └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
             │              │              │              │              │              │
             └──────────────┴──────────────┼──────────────┴──────────────┴──────────────┘
                                           │
                                           ▼
                     ┌───────────────────────────────────────────┐
                     │         Sync Barrier Ronde t -> t+1       │
                     ├───────────────────────────────────────────┤
                     │ 1. Evaluasi Peluruhan Waktu Paruh         │
                     │ 2. Difusi Konten Lintas Platform (Spill)  │
                     │ 3. Update Memori Graf Zep Terpadu         │
                     │ 4. Pembuatan Checkpoint SHA-256           │
                     └───────────────────────────────────────────┘
```

### 5.1 Mekanisme Difusi Konten Silang (*Cross-Platform Information Spillover*)
Di dunia nyata, tangkapan layar cuitan di X kerap kali diunggah ulang ke Instagram dan TikTok, sementara diskusi mendalam di Reddit sering memicu perbincangan di Facebook. Fenomena ini dimodelkan melalui matriks transfer probabilitas:

\[
\text{Spillover}(p_{asal} \to p_{target}) = \sigma_{spill}^{(p_{asal})} \cdot \mathbf{M}_{trans}[p_{asal}, p_{target}]
\]

Konten viral di platform asal yang melampaui ambang batas \(\theta_{viral}\) memiliki peluang untuk disuntikkan secara otomatis ke antrean baca (*ingestion feed*) platform target pada ronde berikutnya, menyimulasikan kaskade opini publik lintas ekosistem digital.
