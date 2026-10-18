# MiroFish Enterprise - MCP Tools Catalog

> **Single-Source-of-Truth**: Dokumen ini dihasilkan secara otomatis dari `backend/mcp_server/tools.py` via `scripts/gen_docs.py`.
> **Status Epistemik**: `[VERIFIED]` | **Terakhir Disinkronkan**: 2026-10-18 04:59:24 UTC
> **Protokol Transport**: FastMCP Streamable HTTP (`:8080/mcp`), SSE, dan stdio fallback.
> **Autentikasi**: OAuth 2.1 (RFC 7636 PKCE S256 & RFC 7662 Introspection).

## Ringkasan Katalog

- **Total MCP Tools Terdaftar**: `22`
- **Canonical Lifecycle Tools (Step 0 - Step 5)**: `11`
- **BettaFish Downstream Analytics Tools**: `3`
- **Legacy Backward-Compatible Tools**: `8`

---

## Daftar Isi

1. [Canonical Enterprise Tools (11 Tools)](#1-canonical-enterprise-tools)
2. [BettaFish Sentiment & Risk Analytics (3 Tools)](#2-bettafish-sentiment--risk-analytics)
3. [Legacy Backward-Compatible Tools (8 Tools)](#3-legacy-backward-compatible-tools)
4. [Detail Spesifikasi Parameter & Schema](#4-detail-spesifikasi-parameter--schema)

---

## 1. Canonical Enterprise Tools

Tools utama yang menopang seluruh 6 fase siklus simulasi MiroFish Enterprise:

| No | Tool Name | Lifecycle Step | Deskripsi | Parameter Wajib |
|---|---|---|---|---|
| 1 | [`create_simulation_project`](#create-simulation-project) | **Step 0** | Membuat proyek simulasi baru pada platform MiroFish Enterprise dengan metadata lengkap. | `project_id`, `name` |
| 2 | [`trigger_web_research`](#trigger-web-research) | **Step 0** | Menjalankan riset web privat Step 0 via SearXNG dan sanitasi CaMeL Prompt Shield 3-layer. | `query` |
| 3 | [`build_knowledge_graph`](#build-knowledge-graph) | **Step 1** | Membangun atau mengekstrak ontologi graf pengetahuan Step 1 dari korpus fakta riset (GraphRAG). | `project_id`, `source_text` |
| 4 | [`generate_agent_profiles`](#generate-agent-profiles) | **Step 2** | Membuat populasi persona agen simulasi Step 2 dengan Whole Trait Theory Fleeson dan kebutuhan System 1 ODE. | `project_id` |
| 5 | [`calibrate_platform_algorithms`](#calibrate-platform-algorithms) | **Step 3** | Mengonfigurasi dan mengkalibrasi matriks bobot rekomendasi Step 3 untuk 7 platform sosial. | `platform` |
| 6 | [`execute_parallel_simulation`](#execute-parallel-simulation) | **Step 3** | Menjalankan eksekusi simulasi swarm paralel Bulk Synchronous Parallel (BSP) dengan perlindungan checkpoint WAL SHA-256. | `project_id`, `simulation_id` |
| 7 | [`fetch_simulation_stream`](#fetch-simulation-stream) | **Step 3** | Mengambil aliran log event aksi agen, kaskade Hawkes, dan metrik sentimen selama simulasi berjalan. | `simulation_id` |
| 8 | [`query_graph_insights`](#query-graph-insights) | **Step 4** | Mengekstrak wawasan subgraf temporal, relasi bitemporal, dan fakta terverifikasi NLI (threshold >= 0.85). | `project_id`, `query` |
| 9 | [`generate_executive_report`](#generate-executive-report) | **Step 4** | Menyusun laporan eksekutif strategis C-Level (BettaFish + ReACT) dengan klausul Safe Abstention dan integritas SHA-256. | `topic` |
| 10 | [`interview_simulation_agent`](#interview-simulation-agent) | **Step 4** | Mengirimkan wawancara IPC interaktif kepada agen persona tertentu dalam simulasi untuk klarifikasi opini. | `simulation_id`, `agent_id`, `question` |
| 11 | [`audit_system_diagnostics`](#audit-system-diagnostics) | **Step 5** | Melakukan audit diagnostik komprehensif Step 5 (FastMCP port 8080, OAuth 2.1, SearXNG, Graphiti, Vault AES-256-GCM). | *(tidak ada)* |

## 2. BettaFish Sentiment & Risk Analytics

Tools analitik hilir (Agent 16) untuk evaluasi polaritas, perumusan direktif C-Level, dan mitigasi krisis:

| No | Tool Name | Domain Analitik | Deskripsi | Parameter Wajib |
|---|---|---|---|---|
| 1 | [`bettafish_analyze_polar_sentiment`](#bettafish-analyze-polar-sentiment) | BettaFish Analytics | Menjalankan analisis polaritas sentimen kontinu [-1.0, 1.0], subjektivitas, dan vektor emosi Plutchik pada teks enterprise. | `text` |
| 2 | [`bettafish_generate_c_level_report`](#bettafish-generate-c-level-report) | BettaFish Analytics | Menghasilkan ringkasan eksekutif C-Level, analisis SWOT, dan direktif peran dengan bukti SHA-256. | `topic` |
| 3 | [`bettafish_assess_corporate_risk`](#bettafish-assess-corporate-risk) | BettaFish Analytics | Menilai risiko korporat, indeks polarisasi opini publik, dan status early warning sentinel. | `polarity_score` |

## 3. Legacy Backward-Compatible Tools

Tools kompatibilitas backward untuk menjaga interoperabilitas penuh dengan klien legacy:

| No | Tool Name | Scope Legacy | Deskripsi | Parameter Wajib |
|---|---|---|---|---|
| 1 | [`list_projects`](#list-projects) | Backward Compatibility | Mendapatkan daftar proyek simulasi MiroFish dari backend atau cache | *(tidak ada)* |
| 2 | [`get_job_status`](#get-job-status) | Backward Compatibility | Mengambil status progres pekerjaan simulasi dan checkpoint ronde | `job_id` |
| 3 | [`get_simulation_report`](#get-simulation-report) | Backward Compatibility | Mengambil laporan prediksi sentimen dan dinamika opini publik berdasarkan project_id atau simulation_id | *(tidak ada)* |
| 4 | [`search_knowledge_graph`](#search-knowledge-graph) | Backward Compatibility | Mencari fakta temporal dan relasi entitas pada graf pengetahuan memori agen | `project_id`, `query` |
| 5 | [`run_web_research`](#run-web-research) | Backward Compatibility | Menjalankan riset web privat Langkah 0 via SearXNG MiroFish tanpa pelacakan | `query` |
| 6 | [`create_simulation_job`](#create-simulation-job) | Backward Compatibility | Membuat konfigurasi dan pekerjaan simulasi baru untuk suatu proyek | `project_id` |
| 7 | [`start_simulation`](#start-simulation) | Backward Compatibility | Memulai atau melanjutkan jalannya simulasi OASIS multi-platform | `simulation_id` |
| 8 | [`stop_simulation`](#stop-simulation) | Backward Compatibility | Menghentikan simulasi yang sedang berjalan | `simulation_id` |

---

## 4. Detail Spesifikasi Parameter & Schema

### `create_simulation_project`

- **Kategori**: `Step 0` (Project Initialization & Workspace Setup)
- **Fungsi**: Membuat proyek simulasi baru pada platform MiroFish Enterprise dengan metadata lengkap.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | ID proyek unik |
| `name` | `string` | **Ya** | `-` | Nama proyek |
| `description` | `string` | Tidak | `` | - |
| `target_platforms` | `array` | Tidak | `-` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "ID proyek unik"
    },
    "name": {
      "type": "string",
      "description": "Nama proyek"
    },
    "description": {
      "type": "string",
      "default": ""
    },
    "target_platforms": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "project_id",
    "name"
  ]
}
```

---

### `trigger_web_research`

- **Kategori**: `Step 0` (Private Web Research & CaMeL Shield)
- **Fungsi**: Menjalankan riset web privat Step 0 via SearXNG dan sanitasi CaMeL Prompt Shield 3-layer.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `query` | `string` | **Ya** | `-` | Kueri riset |
| `project_id` | `string` | Tidak | `proj_default` | - |
| `max_results` | `integer` | Tidak | `10` | - |
| `search_type` | `string` | Tidak | `general` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Kueri riset"
    },
    "project_id": {
      "type": "string",
      "default": "proj_default"
    },
    "max_results": {
      "type": "integer",
      "default": 10
    },
    "search_type": {
      "type": "string",
      "default": "general"
    }
  },
  "required": [
    "query"
  ]
}
```

---

### `build_knowledge_graph`

- **Kategori**: `Step 1` (GraphRAG & Dynamic Ontology Construction)
- **Fungsi**: Membangun atau mengekstrak ontologi graf pengetahuan Step 1 dari korpus fakta riset (GraphRAG).

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | ID proyek |
| `source_text` | `string` | **Ya** | `-` | Teks korpus |
| `group_id` | `string` | Tidak | `-` | - |
| `extract_relations` | `boolean` | Tidak | `True` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "ID proyek"
    },
    "source_text": {
      "type": "string",
      "description": "Teks korpus"
    },
    "group_id": {
      "type": "string"
    },
    "extract_relations": {
      "type": "boolean",
      "default": true
    }
  },
  "required": [
    "project_id",
    "source_text"
  ]
}
```

---

### `generate_agent_profiles`

- **Kategori**: `Step 2` (Whole Trait Theory & System 1 ODE Personas)
- **Fungsi**: Membuat populasi persona agen simulasi Step 2 dengan Whole Trait Theory Fleeson dan kebutuhan System 1 ODE.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | - |
| `count` | `integer` | Tidak | `10` | - |
| `archetype` | `string` | Tidak | `balanced` | - |
| `target_platforms` | `array` | Tidak | `-` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string"
    },
    "count": {
      "type": "integer",
      "default": 10
    },
    "archetype": {
      "type": "string",
      "default": "balanced"
    },
    "target_platforms": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "project_id"
  ]
}
```

---

### `calibrate_platform_algorithms`

- **Kategori**: `Step 3` (7-Platform Matrix RecSys Calibration)
- **Fungsi**: Mengonfigurasi dan mengkalibrasi matriks bobot rekomendasi Step 3 untuk 7 platform sosial.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `platform` | `string` | **Ya** | `-` | - |
| `moral_emotional_weight` | `number` | Tidak | `-` | - |
| `outgroup_penalty` | `number` | Tidak | `-` | - |
| `echo_damping` | `number` | Tidak | `-` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "platform": {
      "type": "string"
    },
    "moral_emotional_weight": {
      "type": "number"
    },
    "outgroup_penalty": {
      "type": "number"
    },
    "echo_damping": {
      "type": "number"
    }
  },
  "required": [
    "platform"
  ]
}
```

---

### `execute_parallel_simulation`

- **Kategori**: `Step 3` (BSP Swarm Parallel Runner & WAL Checkpointing)
- **Fungsi**: Menjalankan eksekusi simulasi swarm paralel Bulk Synchronous Parallel (BSP) dengan perlindungan checkpoint WAL SHA-256.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | - |
| `simulation_id` | `string` | **Ya** | `-` | - |
| `max_rounds` | `integer` | Tidak | `10` | - |
| `platform` | `string` | Tidak | `parallel` | - |
| `run_bsp_barrier` | `boolean` | Tidak | `True` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string"
    },
    "simulation_id": {
      "type": "string"
    },
    "max_rounds": {
      "type": "integer",
      "default": 10
    },
    "platform": {
      "type": "string",
      "default": "parallel"
    },
    "run_bsp_barrier": {
      "type": "boolean",
      "default": true
    }
  },
  "required": [
    "project_id",
    "simulation_id"
  ]
}
```

---

### `fetch_simulation_stream`

- **Kategori**: `Step 3` (Hawkes Cascade & Action Event Streaming)
- **Fungsi**: Mengambil aliran log event aksi agen, kaskade Hawkes, dan metrik sentimen selama simulasi berjalan.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `simulation_id` | `string` | **Ya** | `-` | - |
| `from_round` | `integer` | Tidak | `0` | - |
| `limit` | `integer` | Tidak | `50` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "simulation_id": {
      "type": "string"
    },
    "from_round": {
      "type": "integer",
      "default": 0
    },
    "limit": {
      "type": "integer",
      "default": 50
    }
  },
  "required": [
    "simulation_id"
  ]
}
```

---

### `query_graph_insights`

- **Kategori**: `Step 4` (BiTemporal Graph & NLI Fact Extraction)
- **Fungsi**: Mengekstrak wawasan subgraf temporal, relasi bitemporal, dan fakta terverifikasi NLI (threshold >= 0.85).

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | - |
| `query` | `string` | **Ya** | `-` | - |
| `limit` | `integer` | Tidak | `10` | - |
| `as_of` | `string` | Tidak | `-` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string"
    },
    "query": {
      "type": "string"
    },
    "limit": {
      "type": "integer",
      "default": 10
    },
    "as_of": {
      "type": "string"
    }
  },
  "required": [
    "project_id",
    "query"
  ]
}
```

---

### `generate_executive_report`

- **Kategori**: `Step 4` (C-Level ReACT Strategic Report Synthesis)
- **Fungsi**: Menyusun laporan eksekutif strategis C-Level (BettaFish + ReACT) dengan klausul Safe Abstention dan integritas SHA-256.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `topic` | `string` | **Ya** | `-` | - |
| `project_id` | `string` | Tidak | `-` | - |
| `simulation_id` | `string` | Tidak | `-` | - |
| `verified_only` | `boolean` | Tidak | `True` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string"
    },
    "project_id": {
      "type": "string"
    },
    "simulation_id": {
      "type": "string"
    },
    "verified_only": {
      "type": "boolean",
      "default": true
    }
  },
  "required": [
    "topic"
  ]
}
```

---

### `interview_simulation_agent`

- **Kategori**: `Step 4` (Agent Opinion IPC Qualitative Interview)
- **Fungsi**: Mengirimkan wawancara IPC interaktif kepada agen persona tertentu dalam simulasi untuk klarifikasi opini.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `simulation_id` | `string` | **Ya** | `-` | - |
| `agent_id` | `string` | **Ya** | `-` | - |
| `question` | `string` | **Ya** | `-` | - |
| `max_tokens` | `integer` | Tidak | `256` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "simulation_id": {
      "type": "string"
    },
    "agent_id": {
      "type": "string"
    },
    "question": {
      "type": "string"
    },
    "max_tokens": {
      "type": "integer",
      "default": 256
    }
  },
  "required": [
    "simulation_id",
    "agent_id",
    "question"
  ]
}
```

---

### `audit_system_diagnostics`

- **Kategori**: `Step 5` (FastMCP, Vault & Transport Diagnostics)
- **Fungsi**: Melakukan audit diagnostik komprehensif Step 5 (FastMCP port 8080, OAuth 2.1, SearXNG, Graphiti, Vault AES-256-GCM).

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `include_vault` | `boolean` | Tidak | `True` | - |
| `include_backends` | `boolean` | Tidak | `True` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "include_vault": {
      "type": "boolean",
      "default": true
    },
    "include_backends": {
      "type": "boolean",
      "default": true
    }
  }
}
```

---

### `bettafish_analyze_polar_sentiment`

- **Kategori**: `Downstream` (BettaFish Polar Sentiment & Plutchik Emotion)
- **Fungsi**: Menjalankan analisis polaritas sentimen kontinu [-1.0, 1.0], subjektivitas, dan vektor emosi Plutchik pada teks enterprise.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `text` | `string` | **Ya** | `-` | Teks dokumen atau klaim korporat |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "text": {
      "type": "string",
      "description": "Teks dokumen atau klaim korporat"
    }
  },
  "required": [
    "text"
  ]
}
```

---

### `bettafish_generate_c_level_report`

- **Kategori**: `Downstream` (BettaFish Executive SWOT & C-Level Directives)
- **Fungsi**: Menghasilkan ringkasan eksekutif C-Level, analisis SWOT, dan direktif peran dengan bukti SHA-256.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `topic` | `string` | **Ya** | `-` | - |
| `claims` | `array` | Tidak | `-` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string"
    },
    "claims": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "topic"
  ]
}
```

---

### `bettafish_assess_corporate_risk`

- **Kategori**: `Downstream` (BettaFish Polarization Index & Sentinel Risk)
- **Fungsi**: Menilai risiko korporat, indeks polarisasi opini publik, dan status early warning sentinel.

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `polarity_score` | `number` | **Ya** | `-` | - |
| `virality_potential` | `number` | Tidak | `0.0` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "polarity_score": {
      "type": "number"
    },
    "virality_potential": {
      "type": "number",
      "default": 0.0
    }
  },
  "required": [
    "polarity_score"
  ]
}
```

---

### `list_projects`

- **Kategori**: `Legacy` (Backward-Compatible Project Listing)
- **Fungsi**: Mendapatkan daftar proyek simulasi MiroFish dari backend atau cache

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `limit` | `integer` | Tidak | `20` | Batas jumlah proyek |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "description": "Batas jumlah proyek",
      "default": 20
    }
  }
}
```

---

### `get_job_status`

- **Kategori**: `Legacy` (Backward-Compatible Job Progress Polling)
- **Fungsi**: Mengambil status progres pekerjaan simulasi dan checkpoint ronde

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `job_id` | `string` | **Ya** | `-` | ID pekerjaan atau ID simulasi |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "job_id": {
      "type": "string",
      "description": "ID pekerjaan atau ID simulasi"
    }
  },
  "required": [
    "job_id"
  ]
}
```

---

### `get_simulation_report`

- **Kategori**: `Legacy` (Backward-Compatible Simulation Report Fetching)
- **Fungsi**: Mengambil laporan prediksi sentimen dan dinamika opini publik berdasarkan project_id atau simulation_id

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | Tidak | `-` | ID proyek MiroFish (opsional) |
| `simulation_id` | `string` | Tidak | `-` | ID simulasi MiroFish (opsional) |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "ID proyek MiroFish (opsional)"
    },
    "simulation_id": {
      "type": "string",
      "description": "ID simulasi MiroFish (opsional)"
    }
  }
}
```

---

### `search_knowledge_graph`

- **Kategori**: `Legacy` (Backward-Compatible Knowledge Graph Search)
- **Fungsi**: Mencari fakta temporal dan relasi entitas pada graf pengetahuan memori agen

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | ID proyek atau graf |
| `query` | `string` | **Ya** | `-` | Kata kunci pencarian fakta/entitas |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "ID proyek atau graf"
    },
    "query": {
      "type": "string",
      "description": "Kata kunci pencarian fakta/entitas"
    }
  },
  "required": [
    "project_id",
    "query"
  ]
}
```

---

### `run_web_research`

- **Kategori**: `Legacy` (Backward-Compatible Web Search)
- **Fungsi**: Menjalankan riset web privat Langkah 0 via SearXNG MiroFish tanpa pelacakan

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `query` | `string` | **Ya** | `-` | Topik atau kueri riset |
| `research_type` | `string` | Tidak | `general` | - |
| `max_results` | `integer` | Tidak | `10` | - |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Topik atau kueri riset"
    },
    "research_type": {
      "type": "string",
      "enum": [
        "general",
        "news",
        "images"
      ],
      "default": "general"
    },
    "max_results": {
      "type": "integer",
      "default": 10
    }
  },
  "required": [
    "query"
  ]
}
```

---

### `create_simulation_job`

- **Kategori**: `Legacy` (Backward-Compatible Job Config Creation)
- **Fungsi**: Membuat konfigurasi dan pekerjaan simulasi baru untuk suatu proyek

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `project_id` | `string` | **Ya** | `-` | ID proyek MiroFish |
| `graph_id` | `string` | Tidak | `-` | ID graf pengetahuan (opsional) |
| `enable_twitter` | `boolean` | Tidak | `True` | Aktifkan platform Twitter/X |
| `enable_reddit` | `boolean` | Tidak | `True` | Aktifkan platform Reddit |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "ID proyek MiroFish"
    },
    "graph_id": {
      "type": "string",
      "description": "ID graf pengetahuan (opsional)"
    },
    "enable_twitter": {
      "type": "boolean",
      "default": true,
      "description": "Aktifkan platform Twitter/X"
    },
    "enable_reddit": {
      "type": "boolean",
      "default": true,
      "description": "Aktifkan platform Reddit"
    }
  },
  "required": [
    "project_id"
  ]
}
```

---

### `start_simulation`

- **Kategori**: `Legacy` (Backward-Compatible Simulation Trigger)
- **Fungsi**: Memulai atau melanjutkan jalannya simulasi OASIS multi-platform

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `simulation_id` | `string` | **Ya** | `-` | ID simulasi MiroFish |
| `platform` | `string` | Tidak | `parallel` | Platform simulasi (parallel, twitter, reddit) |
| `max_rounds` | `integer` | Tidak | `50` | Batas ronde simulasi |
| `force` | `boolean` | Tidak | `False` | Paksa restart simulasi dari awal |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "simulation_id": {
      "type": "string",
      "description": "ID simulasi MiroFish"
    },
    "platform": {
      "type": "string",
      "description": "Platform simulasi (parallel, twitter, reddit)",
      "default": "parallel"
    },
    "max_rounds": {
      "type": "integer",
      "description": "Batas ronde simulasi",
      "default": 50
    },
    "force": {
      "type": "boolean",
      "description": "Paksa restart simulasi dari awal",
      "default": false
    }
  },
  "required": [
    "simulation_id"
  ]
}
```

---

### `stop_simulation`

- **Kategori**: `Legacy` (Backward-Compatible Simulation Termination)
- **Fungsi**: Menghentikan simulasi yang sedang berjalan

#### Parameter Masukan (`inputSchema`):

| Nama Field | Tipe | Wajib | Default | Deskripsi |
|---|---|---|---|---|
| `simulation_id` | `string` | **Ya** | `-` | ID simulasi MiroFish |

#### JSON Schema:
```json
{
  "type": "object",
  "properties": {
    "simulation_id": {
      "type": "string",
      "description": "ID simulasi MiroFish"
    }
  },
  "required": [
    "simulation_id"
  ]
}
```

---
