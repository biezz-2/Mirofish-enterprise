# 8. Makalah: Arsitektur Riset Web Step 0 & Pemodelan GraphRAG Step 1 — Penjaminan Data Faktual & Eliminasi Halusinasi MiroFish Enterprise

> **Klasifikasi Dokumen**: Spesifikasi Teknis & Landasan Ilmiah MiroFish Enterprise v3.1  
> **Status**: Approved & Aligned with Canonical 6-Step Workflow  
> **Notion Page URL**: [Notion Page 8](https://app.notion.com/p/8-Makalah-Arsitektur-Riset-Web-Step-0-Pemodelan-GraphRAG-Step-1-Penjaminan-Data-Faktual-Elim-3f73e6031ab781848354c09735cd7831)  
> **Notion Page ID**: `3f73e603-1ab7-8184-8354-c09735cd7831`  

---

## Abstrak
Sistem simulasi sosial dan intelijen multi-agen berskala enterprise menuntut kepatuhan mutlak terhadap kebenaran faktual. Ketergantungan pada inferensi model bahasa mentah tanpa validasi eksternal menimbulkan risiko halusinasi stokastik dan kerentanan terhadap data palsu (*fabricated data*).

Makalah ini menyajikan arsitektur penjaminan integritas data dan mitigasi halusinasi pada **MiroFish Enterprise**, yang bertumpu pada sinergi terpadu antara **Step 0: Private Web Research (SearXNG)** dan **Step 1: GraphRAG Knowledge Modeling**. Sebelum simulasi multi-agen dijalankan, sistem secara mandiri dan deterministik menelusuri data faktual dari internet melalui klaster SearXNG privat yang dilindungi *3-Layer Anti-Prompt Injection Shield* dan formula *Domain Credibility Scoring*. Hasil riset yang terverifikasi kemudian dimodelkan menjadi graf pengetahuan terstruktur menggunakan dual adapter (*Zep Cloud* dan *Graphiti Neo4j*) dengan pengawalan *Graph Readiness Barrier* dan evaluasi *Natural Language Inference (NLI)*. Arsitektur ini menjamin bahwa seluruh data benih, kepribadian agen OCEAN, dinamika interaksi 7 platform, hingga laporan ReACT ReportAgent berakar 100% pada bukti empiris yang terverifikasi.

---

## 1. Posisi Strategis dalam 6-Step Workflow MiroFish Enterprise

Alur eksekusi kanonikal MiroFish Enterprise dirancang berurutan secara ketat untuk memastikan tidak ada celah bagi data palsu masuk ke dalam rantai inferensi:

```
[Reality Seed / Berita / Kebijakan]
               ↓
[Step 0] Private Web Research (SearXNG) ───> Korpus Tervalidasi & Bersih (Zero Data Bohong)
               ↓
[Step 1] GraphRAG Knowledge Modeling    ───> Graf Pengetahuan Berbasis Fakta (Zero Halusinasi)
               ↓
[Step 2] OCEAN & 7-Platform Environment  ───> Parameter & Persona Agen Realistis
               ↓
[Step 3] Parallel Swarm Simulation      ───> Simulasi Dinamika Multi-Platform (Round Barriers)
               ↓
[Step 4] ReACT ReportAgent Deduction    ───> Laporan Intelijen Bersitasi Empiris
               ↓
[Step 5] Human-in-the-Loop & IPC Chat   ───> Eksplorasi & Intervensi Interaktif
```

Penjaminan ketiadaan data bohong dan pencegahan halusinasi diselesaikan secara tuntas pada gerbang **Step 0** dan **Step 1** sebelum masuk ke fase simulasi agen.

---

## 2. Step 0: Private Web Research (SearXNG) — Pondasi Pencarian Fakta Tanpa Data Bohong

### 2.1 Klaster Metasearch Privat Tanpa Pelacakan (*Zero-Tracking Search*)
Untuk mencegah AI menggunakan asumsi internal atau data usang (*knowledge cutoff*), agen pencari mengkueri klaster metasearch SearXNG self-hosted (`http://127.0.0.1:8888`). Klaster ini mengumpulkan data dari berbagai mesin pencari global (Google, Bing, DuckDuckGo, Wikipedia, portal berita resmi) tanpa menyimpan riwayat pencarian atau profil pengguna, menghasilkan spektrum fakta yang luas tanpa bias algoritma tunggal.

### 2.2 Perisai Pertahanan 3 Lapis (*3-Layer Anti-Prompt Injection Shield*)
Data mentah dari internet berpotensi disusupi manipulasi atau injeksi prompt. Step 0 menerapkan 3 lapisan filter keamanan:
1. **Heuristic Pattern Sanitizer**: Menghilangkan token override sistemik (`<|im_start|>`, `system:`, `IGNORE PREVIOUS INSTRUCTIONS`), escape XML/JSON, dan pola obfuski regex.
2. **Model-Based Classifier**: Model klasifikasi ringan mengevaluasi netralitas semantik dan mendeteksi apakah teks web mencoba mengarahkan AI untuk berbohong atau mengabaikan batasan sistem.
3. **Structured Output Limiter**: Hasil ekstraksi dipaksa masuk ke dalam skema JSON tervalidasi strictly-typed, mengabaikan konten bebas yang mencurigakan.

### 2.3 Formula Domain Credibility Scoring
Setiap domain sumber dinilai secara matematis menggunakan rumus kredibilitas:

$$S_{\text{domain}} = w_{\text{tld}} \cdot c_{\text{author}} \cdot \text{decay}(\Delta t)$$

- $w_{\text{tld}}$: Bobot kredibilitas TLD/domain (domain pemerintah `.gov` / `.go.id` = 1.0, institusi riset `.edu` = 0.95, media berita arus utama terakreditasi = 0.85, portal agregator = 0.50, media sosial terbuka = 0.25).
- $c_{\text{author}}$: Koefisien reputasi penulis atau lembaga penerbit.
- $\text{decay}(\Delta t) = e^{-\alpha \Delta t}$: Peluruhan temporal fakta dengan laju penuaan $\alpha$ agar data mutakhir mendapat prioritas lebih tinggi.
- **Threshold Eliminasi**: Sumber dengan skor $S_{\text{domain}} < 0.40$ ditolak secara otomatis dan tidak dimasukkan ke dalam korpus rujukan.

---

## 3. Step 1: GraphRAG Knowledge Modeling — Pemodelan Graf & Mitigasi Halusinasi Total

Setelah korpus dokumen terverifikasi dari Step 0 dihasilkan, Step 1 bertugas mengubah teks menjadi model pengetahuan terstruktur. Pada tahap inilah risiko halusinasi dimitigasi secara komprehensif:

### 3.1 Ekstraksi Ontologi Berbasis Korpus Nyata (Grounded Ontology Extraction)
LLM tidak dibiarkan mendefinisikan ontologi dari memori imajinatif. Sebaliknya, LLM Ontology Extractor diwajibkan hanya mengekstrak kelas entitas dan skema relasi yang terbukti keberadaannya dalam korpus dokumen Step 0. Hal ini mencegah terciptanya entitas fiktif atau relasi semu.

### 3.2 Dual Backend Adapters: Zep Cloud Graph & Graphiti Neo4j
MiroFish mengimplementasikan dua adapter penyimpanan graf dengan karakteristik spesifik:
- **Zep Cloud Graph**: Digunakan untuk memori episodik dinamis dengan *temporal edge decay*, melacak perubahan persepsi dan sentimen agen seiring berjalannya waktu.
- **Graphiti Neo4j**: Penyimpanan grafik *self-hosted* enterprise yang terisolasi, menyimpan fakta inti, topologi hubungan kausal, dan bukti kutipan permanen.

### 3.3 Text Chunking Adaptif & Ekstraksi Entitas Otomatis
Dokumen dibagi menggunakan chunking adaptif berdasar batas semantik kalimat (bukan potongan token acak). Dari setiap chunk, diekstraksi: entitas (*node*), relasi (*edge*), lini masa peristiwa (*timeline events*), dan afiliasi sentimen. Setiap node dan edge wajib mengaitkan ID referensi chunk asalnya.

### 3.4 Ingestion Polling & Graph Readiness Barrier
Salah satu penyebab utama halusinasi pada sistem multi-agen adalah kondisi balapan (*race condition*) di mana agen memulai simulasi sebelum basis pengetahuan selesai dibangun. MiroFish menerapkan **Graph Readiness Barrier**: sistem melakukan polling status ingesti secara berkala dan memblokir transisi ke Step 2 hingga seluruh node, edge, dan indeks embedding diverifikasi 100% siap.

### 3.5 Evaluasi Skor Entailment NLI (Natural Language Inference)
Untuk setiap relasi (Subjek - Predikat - Objek) yang diekstrak, dilakukan verifikasi entailment silang menggunakan model NLI terhadap kalimat sumber:
$$E_{\text{score}} = P(\text{Entailment} \mid \text{Sumber Chunk}, \text{Relasi Graf})$$
Jika $E_{\text{score}} < 0.85$ atau relasi terindikasi kontradiktif/netral, relasi tersebut langsung digugurkan dan dilarang masuk ke dalam graf pengetahuan.

---

## 4. Integritas Rantai Nilai: Pengaruh Grounding Faktual ke Step 2 - Step 5

Keberhasilan memusnahkan data bohong di Step 0 dan mencegah halusinasi di Step 1 secara langsung melindungi kualitas tahap berikutnya:

### 4.1 Step 2: OCEAN & 7-Platform Environment Setup
Profil psikologis Big Five (OCEAN) agen tidak diinisialisasi secara arbitrer, melainkan dikalibrasi berdasarkan fakta demografis dan data kultural nyata dari korpus Step 0. Bobot echo chamber (0.4 - 0.8) dan threshold viral pada 7 platform (Twitter, X, Reddit, TikTok, Instagram, Facebook, Threads) mencerminkan kondisi lapangan riil.

### 4.2 Step 3: Parallel Swarm Simulation & Dynamic Graph Memory
Ketika agen menjalankan aksi (Post, Comment, Share, Like, Mute) dalam putaran paralel dengan synchronized round barriers, memori temporal yang diinjeksikan kembali ke graf selalu mengacu pada simpul fakta asli. Snapshot tiap putaran di-hash dengan SHA-256 dan dilindungi SQLite WAL untuk crash recovery.

### 4.3 Step 4: ReACT ReportAgent Deduction & Empirical Citations
ReportAgent menggunakan siklus ReACT (Thought -> Tool Call -> Reflection) dengan peralatan InsightForge (PanoramaSearch, IPCAgentInterview). Laporan prediktif yang dihasilkan wajib menyertakan tautan sitasi langsung (*empirical entity citation*) ke node graf dan timestamp lini masa, menjamin laporan intelijen 100% dapat diaudit.

### 4.4 Step 5: Human-in-the-Loop & IPC Chat
Pengguna dapat menguji langsung konsistensi agen melalui wawancara IPC real-time di antarmuka Vue 3, menyuntikkan variabel intervensi baru, dan mengamati respon simulasi tanpa risiko distorsi narasi palsu.

---

## 5. Standar Operasional Prosedur (SOP) Penjaminan Nol Data Bohong

1. **Pre-flight Web Research**: Setiap eksekusi simulasi wajib mendahului dengan Step 0 SearXNG query; dilarang bypass langsung ke Step 2 tanpa data eksternal.
2. **3-Layer Shield Validation**: Pastikan data mentah lolos Heuristic Pattern Sanitizer, Model Classifier, dan Structured Output Limiter.
3. **Credibility Threshold**: Hanya masukkan sumber dengan $S_{\text{domain}} \ge 0.40$ ke dalam korpus Step 1.
4. **Readiness Barrier Gate**: Tunggu sinyal Graph Readiness Barrier tervalidasi sebelum memulai Step 2 dan Step 3.
5. **Citation Audit**: Pastikan setiap kesimpulan pada laporan akhir Step 4 memiliki bukti sitasi node graf ber-hash valid.

---

## Daftar Pustaka & Landasan Ilmiah
- Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020.
- Ji, Z., et al. (2023). *Survey of Hallucination in Natural Language Generation*. ACM Computing Surveys.
- Edge, D., et al. (2024). *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*. Microsoft Research.
- Park, J. S., et al. (2023). *Generative Agents: Interactive Simulacra of Human Behavior*. Stanford University & Google Research.
