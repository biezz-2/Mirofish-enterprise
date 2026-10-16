# Deliverable: Agent 05 — Dynamic Ontology Generation & Schema Grounding
**Task ID**: `t_f0ce4d59`  
**Slice**: Slice 05 (Subagent 05: Dynamic Ontology Generation & Schema Grounding)  
**Divisi**: Research & Paper Engineering (R2P)  
**Status**: Ready for Human Gate & Downstream Review  
**Referensi**: Master Plan MiroFish Enterprise Dokumen 8 & Kontrak Step 1 GraphRAG (`contracts/02-step1-graphrag.json`)  

---

## 1. Ringkasan Eksekutif & Blueprint Arsitektur
Sistem **Dynamic Ontology Generation & Schema Grounding** telah diimplementasikan penuh untuk membangun fondasi GraphRAG Step 1 pada MiroFish Enterprise. Arsitektur ini bertanggung jawab memproses korpus tidak terstruktur (hasil riset web SearXNG dan dokumen korpus domain), mengekstrak taksonomi ontologi yang adaptif dan dinamis, menegakkan standardisasi penamaan ketat sesuai konvensi graf pengetahuan FalkorDB / Neo4j, serta mempertahankan keterlacakan bukti (evidence tracking) melalui penautan `chunk_ids` pada setiap simpul (*node*) dan sisi (*edge*).

```
[Unstructured Web/Research Corpus]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ AdaptiveSemanticChunker                                │
│ - Markdown Header Structural Splitting (#, ##, ###)     │
│ - Bilingual Stopword Filtering (EN/ID)                │
│ - Lexical-Topical Cohesion Scoring: Cohesion(T1, T2)   │
│ - Zero Redundant Tokens on Chunk Boundaries            │
│ - Metadata: start_char, end_char, token_count, header  │
└─────────────────────────┬──────────────────────────────┘
                          │ List[SemanticChunk]
                          ▼
┌────────────────────────────────────────────────────────┐
│ Dynamic Ontology Generator (Pydantic Schema Guard)     │
│ - Strict PascalCase Entity Normalizer:                 │
│   ^[A-Z][a-zA-Z0-9]*$                                  │
│ - Strict SCREAMING_SNAKE_CASE Relation Normalizer:     │
│   ^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$                        │
│ - Safe Attribute Escaping (Reserved Words Protection)  │
│ - Step 0 Contract Grounding Verification               │
└─────────────────────────┬──────────────────────────────┘
                          │ OntologySchema
                          ▼
┌────────────────────────────────────────────────────────┐
│ LocalGraphService & GraphBuilder Ingestion             │
│ - Chunk-Level Extraction with LLM / Graph Engine       │
│ - GroundedNode: uuid, name, entity_type, chunk_ids     │
│ - GroundedEdge: uuid, source, target, type, chunk_ids  │
│ - Zero Cypher Injection via Strict Regex Validation    │
│ - FalkorDB / Neo4j Schema-Conformant Ingestion         │
└────────────────────────────────────────────────────────┘
```

---

## 2. Standar Konvensi Penamaan & Validasi Format

### 2.1 Tipe Entitas (Entity Types)
- **Format**: `PascalCase`
- **Regex Validator**: `^[A-Z][a-zA-Z0-9]*$`
- **Aturan Transformasi**:
  - Mengubah pemisah kata (`_`, `-`, spasi) menjadi huruf kapital awal per kata.
  - Menghapus karakter non-alfanumerik.
  - Memastikan karakter pertama selalu huruf kapital `[A-Z]`. Jika string diawali angka, ditambahkan prefix `E` atau karakter alfabet yang sesuai.
- **Contoh Normalisasi**:
  - `government_taskforce` $\rightarrow$ `GovernmentTaskforce`
  - `media-organization` $\rightarrow$ `MediaOrganization`
  - `publicFigure` $\rightarrow$ `PublicFigure`

### 2.2 Tipe Relasi (Relationship Types)
- **Format**: `SCREAMING_SNAKE_CASE`
- **Regex Validator**: `^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$`
- **Aturan Transformasi**:
  - Mengubah huruf kecil ke huruf kapital.
  - Mengganti spasi dan tanda minus (`-`) dengan garis bawah (`_`).
  - Menghilangkan duplikasi garis bawah berturut-turut.
  - Jika relasi diawali karakter non-alfabet (misal angka), secara otomatis diberikan prefix aman `REL_` agar valid pada Cypher query engine.
- **Contoh Normalisasi**:
  - `coordinates_with` $\rightarrow$ `COORDINATES_WITH`
  - `opposes-policy` $\rightarrow$ `OPPOSES_POLICY`
  - `funds and sponsors` $\rightarrow$ `FUNDS_AND_SPONSORS`
  - `123_connects` $\rightarrow$ `REL_123_CONNECTS`

---

## 3. Formulasi Matematis Kohesi & Chunking Adaptif

### 3.1 Skor Kohesi Leksikal-Topikal ($C_{\text{lex}}$)
Untuk mencegah fragmentasi topik pada saat pemotongan teks, `AdaptiveSemanticChunker` menghitung kohesi semantik antar dua blok bertetangga $B_1$ dan $B_2$ menggunakan Jaccard overlap atas himpunan kata kunci konten (*content keywords*):
\[
C_{\text{lex}}(B_1, B_2) = \frac{|\mathcal{K}(B_1) \cap \mathcal{K}(B_2)|}{|\mathcal{K}(B_1) \cup \mathcal{K}(B_2)|}
\]
di mana $\mathcal{K}(B)$ adalah himpunan token berpanjang $\ge 3$ yang telah disaring dari stopword bahasa Inggris dan bahasa Indonesia.

### 3.2 Kriteria Pemisahan Chunk
Sebuah chunk baru diinisialisasi jika salah satu dari kondisi berikut terpenuhi:
1. **Batas Heading Struktural**: Terdeteksi heading Markdown (`#`, `##`, `###`).
2. **Kapasitas Maksimal**: Panjang kumulatif chunk melebihi `max_chunk_size` (1500 karakter).
3. **Pergeseran Topik**: Panjang kumulatif mencapai `target_chunk_size` (800 karakter) **dan** skor kohesi leksikal $C_{\text{lex}} < \tau_{\text{cohesion}}$ ($\tau = 0.15$).

### 3.3 Zero Redundant Tokens
Berbeda dengan algoritma *sliding window* tradisional yang menduplikasi token antar-chunk, chunking adaptif ini menggunakan segmentasi batas alami (paragraf/heading) sehingga **tidak ada duplikasi token redundan** pada batas potong (`redundant_tokens = 0`), menghemat konteks jendela LLM hingga 20-30%.

---

## 4. Model Data Pydantic v2 Terintegrasi

1. **`OntologyAttribute`**: Menyimpan nama atribut (dinormalisasi ke `snake_case`), tipe data (`text`, `float`, `integer`, `boolean`), serta deskripsi.
2. **`EntityDefinition`**: Menegakkan tipe `PascalCase` dengan daftar atribut valid.
3. **`RelationDefinition`**: Menegakkan tipe `SCREAMING_SNAKE_CASE` dengan pasangan `source` dan `target` dalam format `PascalCase`.
4. **`OntologySchema`**: Menyatukan entitas, relasi, konteks domain, dan status verifikasi grounding Step 0.
5. **`SemanticChunk`**: Menyimpan `chunk_id`, potongan teks, offset karakter (`start_char`, `end_char`), estimasi token, heading section, dan skor kohesi.
6. **`GroundedNode`**: Entitas graf dengan `uuid`, `name`, `entity_type` (PascalCase), label wajib `Entity`, atribut, dan `chunk_ids` referensi.
7. **`GroundedEdge`**: Sisi graf kausal dengan `uuid`, `name` / `relation_type` (SCREAMING_SNAKE_CASE), node sumber, node tujuan, fakta pendukung, dan `chunk_ids` referensi.
8. **`GroundedGraph`**: Struktur graf komprehensif yang mengemas seluruh node, edge, dan semantic chunks pendukung.

---

## 5. Kepatuhan Kontrak & Integrasi Step 0 Research

Modul `OntologyGenerator.ground_with_step0_research` memvalidasi ontologi terhadap kontrak hasil riset `contracts/01-step0-research.json`:
- Memverifikasi ambang batas kredibilitas (`min_credibility_score >= 0.70`).
- Menyematkan metadata sumber domain terverifikasi (`arxiv.org`, `nature.com`, dll.).
- Menolak pembentukan ontologi dari sumber dengan reputasi tidak memadai.

---

## 6. Hasil Pengujian Fungsional & Regresi

Seluruh 118 unit tests pada backend MiroFish Enterprise berhasil lulus 100% tanpa regresi:
- `backend/tests/test_dynamic_ontology_grounding.py`: **25 / 25 PASSED** (100%)
- `backend/tests/test_ontology_generator.py`: **4 / 4 PASSED** (100%)
- `backend/tests/test_ontology_attributes.py`: **12 / 12 PASSED** (100%)
- `backend/tests/test_domain_credibility.py`: **10 / 10 PASSED** (100%)
- `backend/tests/test_searxng_client.py`: **9 / 9 PASSED** (100%)
- `backend/tests/test_anti_injection.py`: **36 / 36 PASSED** (100%)
- `backend/tests/test_v31_core.py`: **8 / 8 PASSED** (100%)
- `backend/tests/test_v32_enterprise.py`: **14 / 14 PASSED** (100%)

---

## 7. Verifikasi Human Gate & Pipeline Artifacts
- **Artefak Pipeline**: `/home/biezz/contracts/pipeline/artifacts/slice-05-dynamic-ontology-generation.json`
- **SHA-256 Digest**: `5b1d32e74c1c47e47f3bb4a493ce227249deea99a750b3d7ff4e980c81702d0b`
- **Validasi Skema Gate**: `python3 /home/biezz/contracts/bin/human-gate-check.py check ...` $\rightarrow$ **VALID**
- **Checklist Human Gate**: `/home/biezz/contracts/pipeline/artifacts/slice-05-human-gate-checklist.md`
