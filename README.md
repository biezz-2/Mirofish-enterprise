<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="MiroFish Enterprise Logo" width="70%"/>

# 🌊 MiroFish Enterprise (v3.1)
### Autonomous Swarm Intelligence & Multi-Agent Predictive Simulation Sandbox
*Simulate high-fidelity parallel societies, forecast public opinion dynamics, and test macro decisions with zero risk.*

[![GitHub Release](https://img.shields.io/github/v/release/biezz-2/Mirofish-enterprise?style=for-the-badge&color=2563EB)](https://github.com/biezz-2/Mirofish-enterprise/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%20--%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B%20LTS-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)
[![PM2 Ready](https://img.shields.io/badge/PM2-Cluster%20%26%20Fork-2B037A?style=for-the-badge&logo=pm2&logoColor=white)](https://pm2.keymetrics.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](./LICENSE)

---

### 🌐 Language Navigation / Navigasi Bahasa
**[English (Default)](./README.md)** | **[Bahasa Indonesia](./README-ID.md)** | **[中文文档](./README-ZH.md)**

📚 **Comprehensive Architecture Wikipedia**:
[English Documentation (`wiki/en/`)](./wiki/en/index.md) | [Dokumentasi Bahasa Indonesia (`wiki/`)](./wiki/index.md)

</div>

---

## ⚡ What is MiroFish Enterprise?

**MiroFish Enterprise** is an industrial-grade swarm intelligence prediction and social simulation sandbox maintained by **[biezz-2](https://github.com/biezz-2)**.

By taking seed information from real-world materials (breaking news events, public policy drafts, market signals, or complex literature), MiroFish automatically orchestrates hundreds to thousands of autonomous AI agents within a high-fidelity digital twin society. Each agent is equipped with:
- **Big Five OCEAN Psychological Profiling**: Dynamic openness, conscientiousness, extraversion, agreeableness, and neuroticism.
- **Dual GraphRAG Long-Term Memory**: Structured temporal knowledge graphs powered by Zep Cloud and Neo4j.
- **7-Platform Behavioral Models**: Dedicated interaction and algorithmic feeds for modern social platforms.

Decision-makers can observe emergent phenomena from a "God's-eye view", inject dynamic counter-measures, and generate evidence-backed predictive intelligence reports.

---

## 🏛️ System Architecture & Workflow

```
                                  [ Seed Materials & Query ]
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   Step 0: Private Web Research (SearXNG)  │
                         │   • 3-Layer Anti-Prompt Injection Shield  │
                         │   • Domain Credibility Scoring (S_domain) │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   Step 1: GraphRAG Knowledge Modeling     │
                         │   • Entity / Relation Ontology Extraction │
                         │   • Zep Cloud & Graphiti Neo4j Ingestion  │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   Step 2: OCEAN & 7-Platform Environment  │
                         │   • Big Five Personality Synthesis        │
                         │   • Platform Feed Scoring Calibration     │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   Step 3: Parallel Swarm Simulation       │
                         │   • Synchronized Round Barriers           │
                         │   • SQLite WAL & SHA-256 Checkpoints      │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   Step 4: ReACT ReportAgent Deduction     │
                         │   • Autonomous Tool Use (InsightForge)    │
                         │   • Empirical Entity Citation Reports     │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   Step 5: Human-in-the-Loop & IPC Chat    │
                         │   • Real-Time Interactive Agent Interview │
                         │   • Dynamic Intervention & Variable Shift │
                         └───────────────────────────────────────────┘
```

---

## 🚀 Key Enterprise Features

### 1. 🌐 7-Platform Social Simulation Ecosystem
Simulate behavioral reactions across distinct platform algorithms:

| Platform | Display Name | Content Limit | Echo Chamber | Viral Threshold | Algorithm Persona |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Twitter** | Twitter | 280 chars | Medium (0.5) | 5,000 | Ephemeral, fast-paced |
| **X** | X | 25,000 chars | Medium (0.5) | 8,000 | Long-form debate & threads |
| **Reddit** | Reddit | 40,000 chars | High (0.7) | 300 | Deep threaded discussions |
| **TikTok** | TikTok | 150 chars | Low (0.4) | 50,000 | Algorithmic viral distribution |
| **Instagram** | Instagram | 2,200 chars | Medium (0.5) | 10,000 | Visual narrative & aesthetic |
| **Facebook** | Facebook | 63,000 chars | Very High (0.8)| 8,000 | Broad network & closed groups |
| **Threads** | Threads | 500 chars | Medium (0.5) | 5,000 | Conversational & text-first |

### 2. 🔍 Step 0 Autonomous Web Research (SearXNG)
- Self-hosted metasearch cluster querying unbiased global sources without tracking.
- **3-Layer Anti-Prompt Injection Shield**:
  1. *Heuristic Pattern Sanitizer*: Strips system override tokens, XML command escapes, and evasion attempts.
  2. *Model-Based Classifier*: Verifies semantic neutrality before feeding data to agents.
  3. *Structured Output Limiter*: Restricts external content to validated JSON fact schemas.
- Mathematical domain credibility scoring: $S_{\text{domain}} = w_{\text{tld}} \cdot c_{\text{author}} \cdot \text{decay}(\Delta t)$.

### 3. 🧠 GraphRAG Knowledge Engine
- Dual backend adapters:
  - **Zep Cloud Graph**: Real-time episodic memory graphs with temporal edge decay.
  - **Graphiti Neo4j**: Self-hosted on-premise graph storage for isolated enterprise deployments.
- Automatic extraction of entities, relationships, timeline events, and cross-agent sentiment affiliations.

### 4. 🛡️ Operational Resilience & Transactional Safety
- **SQLite Write-Ahead Logging (WAL)** & PostgreSQL multi-database ORM abstraction.
- **Deterministic Cryptographic Checkpoints**: Every round snapshot is hashed with SHA-256.
- **Boot-Time Crash Recovery Scanner**: Automatically detects interrupted simulation jobs and restores execution from the last valid checkpoint.
- **AES-256-GCM Vault**: Hardened credential security for API keys and endpoint secrets.

### 5. 🤖 ReACT ReportAgent Engine
- Multi-turn autonomous analyst using ReACT (*Reasoning + Acting*):
  - Formulates structured research hypotheses.
  - Dispatches targeted tool queries (`InsightForge`, `PanoramaSearch`, `IPCAgentInterview`).
  - Synthesizes comprehensive reports with citations to graph nodes and timeline timestamps.

### 6. 🔌 Model Context Protocol (MCP) Server
- Standardized MCP server integration via `mcp_server` (`stdio` transport) allowing AI assistants (Claude, Cursor, Cline) to:
  - Discover simulation projects (`list_projects`)
  - Poll job progress and checkpoint telemetry (`get_job_status`)
  - Run zero-leakage web research (`run_web_research`)
  - Search temporal knowledge graphs (`search_knowledge_graph`)

---

## 📸 Interface Screenshots

<div align="center">
<table>
<tr>
<td><img src="./static/image/Screenshot/运行截图1.png" alt="Platform Selection & Topic Input" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图2.png" alt="GraphRAG Knowledge Builder" width="100%"/></td>
</tr>
<tr>
<td><img src="./static/image/Screenshot/运行截图3.png" alt="Multi-Agent Persona Generator" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图4.png" alt="Parallel Social Simulation Monitor" width="100%"/></td>
</tr>
<tr>
<td><img src="./static/image/Screenshot/运行截图5.png" alt="Agent Interview & Dynamic Intervention" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图6.png" alt="ReACT Generated Intelligence Report" width="100%"/></td>
</tr>
</table>
</div>

---

## ⚙️ Quick Start Runbook

### Prerequisites

| Component | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Node.js** | 18+ LTS | Vite Frontend & PM2 runtime |
| **Python** | 3.10 – 3.13 | Flask Backend & OASIS Engine |
| **PM2** | Latest | Microservice process management |
| **Docker** (Optional) | 24+ | Containerized SearXNG & Neo4j |

---

### Step 1: Clone Repository

```bash
git clone https://github.com/biezz-2/Mirofish-enterprise.git
cd Mirofish-enterprise
```

---

### Step 2: Environment Configuration (`.env`)

```bash
cp .env.example .env
```

Configure your `.env` variables:

```env
# Operational Mode
DEVELOPMENT_MODE=true                # Set true to bypass external API checks during local testing
SECRET_KEY=mirofish-enterprise-secret-key-2026
FLASK_DEBUG=false
PORT=5001

# LLM Gateway (OpenAI-compatible)
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Knowledge Graph (Zep Cloud or Graphiti)
GRAPH_BACKEND=zep
ZEP_API_KEY=your-zep-api-key-here

# Step 0 Web Research (SearXNG)
SEARXNG_ENABLED=true
SEARXNG_ENDPOINT=http://127.0.0.1:8888

# Simulation Limits
OASIS_DEFAULT_MAX_ROUNDS=15
REPORT_AGENT_MAX_TOOL_CALLS=8
```

---

### Step 3: Install Dependencies

```bash
# Frontend dependencies
cd frontend && npm install && cd ..

# Backend dependencies (Python)
pip install -r backend/requirements.txt
```

---

### Step 4: Run Microservices via PM2 (Recommended)

MiroFish Enterprise includes a pre-configured `ecosystem.config.js`:

```bash
# Launch backend, frontend, and MCP services
pm2 start ecosystem.config.js

# Save process table for auto-restart on system reboot
pm2 save
```

Verify service status:
```bash
pm2 status
```

| ID | Name | Mode | Status | Address |
| :--- | :--- | :--- | :--- | :--- |
| `0` | **`mirofish-backend`** | fork | **online** | `http://localhost:5001` |
| `1` | **`mirofish-frontend`** | cluster | **online** | `http://localhost:3000` |
| `2` | **`mirofish-mcp`** | fork | **online** | `stdio / JSON-RPC` |

---

### Step 5: Verify Endpoints

```bash
# Backend Health Check
curl http://127.0.0.1:5001/health
# Response: {"database":"sqlite","multi_platform":true,"searxng":true,"service":"MiroFish Enterprise Backend (v3.1)","status":"healthy"}

# Platform Configuration Matrix
curl http://127.0.0.1:5001/api/platforms

# Frontend Web Interface
curl -I http://127.0.0.1:3000/
# Response: HTTP/1.1 200 OK
```

---

## 🧪 Comprehensive Core Test Suite

Run the full verification suite covering all 8 enterprise subsystems:

```bash
cd backend
python3 tests/test_v31_core.py
```

Expected output:
```
=================================================================
      MIROFISH BACKEND v3.1 CORE COMPREHENSIVE TEST SUITE        
=================================================================
[1/8] [PASS] 1. Database SQLite Init & Model Relations
[2/8] [PASS] 2. JobEngine State Transitions (queued->running->checkpointing->completed)
[3/8] [PASS] 3. Checkpoints Creation, SHA-256 Hash & Crash Recovery
[4/8] [PASS] 4. Secrets AES-GCM 256-bit Encryption & Decryption
[5/8] [PASS] 5. 7 Platform Behaviors & Multi-Param Feed Scoring
[6/8] [PASS] 6. MultiPlatformSimulator Parallel Execution Loop & Recovery
[7/8] [PASS] 7. SearXNG Web Research Service & Sanitization
[8/8] [PASS] 8. MCP Server Tools Discovery & Invocation
-----------------------------------------------------------------
Hasil Pengujian: 8/8 lolos (100.0%)
=================================================================
SEMUA PENGUJIAN LOLOS 100%!
```

---

## 📖 Complete Wiki Documentation Index

All architectural specs, mathematical formulas, and runbooks are available in the repository wiki:

| Chapter | English Document | Dokumentasi Bahasa Indonesia | Description |
| :--- | :--- | :--- | :--- |
| **Main Portal** | [`wiki/en/index.md`](./wiki/en/index.md) | [`wiki/index.md`](./wiki/index.md) | Executive summary, philosophy & components |
| **Architecture** | [`wiki/en/architecture.md`](./wiki/en/architecture.md) | [`wiki/arsitektur.md`](./wiki/arsitektur.md) | 7-tier architecture & Mermaid flowcharts |
| **7 Platforms** | [`wiki/en/multi-platform-expansion.md`](./wiki/en/multi-platform-expansion.md) | [`wiki/ekspansi-multi-platform.md`](./wiki/ekspansi-multi-platform.md) | Platform parameters & feed scoring math |
| **Web Research** | [`wiki/en/searxng-web-research.md`](./wiki/en/searxng-web-research.md) | [`wiki/riset-web-searxng.md`](./wiki/riset-web-searxng.md) | SearXNG setup & 3-layer anti-injection |
| **Resilience** | [`wiki/en/operational-readiness.md`](./wiki/en/operational-readiness.md) | [`wiki/kesiapan-operasional.md`](./wiki/kesiapan-operasional.md) | SQLite WAL, SHA-256 checkpoints & AES-GCM |
| **Codemap** | [`wiki/en/codemap.md`](./wiki/en/codemap.md) | [`wiki/codemap.md`](./wiki/codemap.md) | Directory structure & cross-module calls |
| **Runbook** | [`wiki/en/operational-guide.md`](./wiki/en/operational-guide.md) | [`wiki/panduan-operasional.md`](./wiki/panduan-operasional.md) | Setup, PM2 deployment & REST API guide |
| **LLMs Index** | [`wiki/en/llms.txt`](./wiki/en/llms.txt) | [`wiki/llms.txt`](./wiki/llms.txt) | Machine-readable index for LLM agents |

---

## 👥 Credits & Authorship

- **Project Lead & Maintainer**: **[biezz-2](https://github.com/biezz-2)**
- **Autonomous System Co-Author**: **[claude-biezz-2](https://github.com/apps/claude-code)**
- **Foundation Engine**: Supported by **[CAMEL-AI OASIS](https://github.com/camel-ai/oasis)** (Open Agent Social Interaction Simulations).
- **Technology Stack**: Python 3.13, Flask, SQLAlchemy, Vite, Vue 3, Tailwind CSS, PM2, SearXNG, Zep Cloud, Neo4j.

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).
