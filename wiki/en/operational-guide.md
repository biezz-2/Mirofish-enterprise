---
title: Deployment, Execution, and Field Testing Runbook
type: guide
tags: [deployment, pm2, docker-compose, searxng, api-reference, recovery-testing, v3.1]
related:
  - "[[index]]"
  - "[[architecture]]"
  - "[[operational-readiness]]"
  - "[[codemap]]"
sources:
  - docker-compose.yml
  - backend/run.py
  - backend/app/config.py
  - frontend/vite.config.js
---

> 🌐 **Language / Bahasa**: [English](./operational-guide.md) | [Bahasa Indonesia](../panduan-operasional.md)

# Deployment, Execution, and Field Testing Runbook: MiroFish v3.1 Enterprise

This document serves as the hands-on operational runbook to install, configure, execute, and validate the **MiroFish v3.1** platform across local development environments and multi-OS enterprise server clusters (Linux, Windows, macOS).

---

## 1. System Prerequisites & Software Dependencies

Before initiating setup, ensure the host system satisfies the minimum requirements:

| Software | Minimum Version | Purpose / Verification Note | Version Command |
| :--- | :--- | :--- | :--- |
| **Node.js** | v18.16.0+ LTS | Frontend asset compilation & PM2 runtime | `node -v` |
| **npm** | v9.0.0+ | JavaScript dependency manager | `npm -v` |
| **Python** | 3.10.x - 3.12.x | Flask backend runtime & OASIS engine | `python3 --version` |
| **UV (Recommended)** | Latest | Ultra-fast Python package resolver | `uv --version` |
| **Docker Engine** | 24.0.0+ | Containerized SearXNG & Neo4j | `docker --version` |
| **Docker Compose** | v2.20.0+ | Containerized service orchestration | `docker compose version` |
| **PM2** | 5.3.0+ | Background enterprise process manager | `pm2 -v` |

---

## 2. Environment Management & Configuration (`.env`)

Copy the configuration template and customize the required environment secrets in the repository root:

```bash
cp .env.example .env
```

Populate `.env` with valid credentials:

```ini
# ========================================================
# MIROFISH v3.1 ENTERPRISE CONFIGURATION
# ========================================================

# Flask Server Config
SECRET_KEY=mirofish-super-deterministic-enterprise-key-2026
FLASK_DEBUG=False
PORT=5001

# LLM Gateway Config (Supports OpenAI / 9Router / vLLM)
LLM_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Zep Cloud Knowledge Graph Config
ZEP_API_KEY=z_cloud_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Step 0 Web Research (SearXNG Private Cluster)
SEARXNG_ENABLED=True
SEARXNG_ENDPOINT=http://127.0.0.1:8888

# OASIS Simulation Parameters
OASIS_DEFAULT_MAX_ROUNDS=10
REPORT_AGENT_MAX_TOOL_CALLS=8
REPORT_AGENT_MAX_REFLECTION_ROUNDS=3
REPORT_AGENT_TEMPERATURE=0.5

# Cryptographic Master Secret & Database
MASTER_APP_SECRET=bf38c71d6f5e4a8b9c2d1e0f3a5b7c9d
DATABASE_URL=sqlite:///backend/app/uploads/mirofish.db
```

---

## 3. Container Orchestration: SearXNG & Neo4j (`docker-compose.yml`)

Start supporting infrastructure (private SearXNG metasearch and Neo4j graph cluster) via Docker Compose:

```bash
# Start background supporting containers
docker compose -f docker-compose.yml up -d
```

Verify that all supporting containers report `healthy`:
```bash
docker compose ps
```

Expected healthy output:
```
NAME                    IMAGE                   COMMAND                  SERVICE             STATUS
mirofish-searxng        searxng/searxng:latest  "/sbin/tini -- /usr/…"   searxng             Up (healthy) (127.0.0.1:8888->8080/tcp)
mirofish-searxng-redis  redis:7-alpine          "docker-entrypoint.s…"   searxng-redis       Up (healthy)
mirofish-neo4j          neo4j:5.15-community    "tini -g -- /startup…"   neo4j               Up (healthy) (7474/tcp, 7687/tcp)
```

---

## 4. Production Process Management with PM2

PM2 ensures *always-on* availability, automated crash recovery, zero-downtime reloads, and centralized aggregated logging.

### 4.1 PM2 Configuration File (`ecosystem.config.js`)

Ensure `ecosystem.config.js` exists in the repository root:

```javascript
module.exports = {
  apps: [
    {
      name: 'mirofish-backend',
      cwd: './backend',
      script: 'run.py',
      interpreter: 'python3', // On Windows, specify the python.exe path inside the venv
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        PYTHONUNBUFFERED: '1',
        FLASK_ENV: 'production',
        PORT: 5001
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      merge_logs: true
    },
    {
      name: 'mirofish-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run preview -- --port 3000 --host 0.0.0.0',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      merge_logs: true
    }
  ]
};
```

### 4.2 Cross-Platform Execution Procedures

#### A. Linux (Ubuntu / Debian / WSL2)
```bash
# 1. Create logs directory
mkdir -p logs

# 2. Setup Python virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Setup Frontend
cd frontend
npm install
npm run build
cd ..

# 4. Launch via PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### B. Windows (PowerShell / CMD)
```powershell
# 1. Setup logs directory and venv
mkdir logs
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# 2. Build Frontend
cd frontend
npm install
npm run build
cd ..

# 3. Launch PM2 (Verify interpreter points to the venv python.exe)
pm2 start ecosystem.config.js
```

#### C. macOS (Apple Silicon M1/M2/M3 & Intel)
```bash
# Follow identical steps to Linux; ensure Xcode CLI tools are present
xcode-select --install
pm2 start ecosystem.config.js
```

PM2 Operational Commands:
- `pm2 status`: Inspect status across all cluster processes.
- `pm2 logs mirofish-backend`: Stream real-time backend execution logs.
- `pm2 restart all`: Perform a cluster-wide restart.
- `pm2 stop all`: Gracefully terminate all application workers.

---

## 5. Comprehensive REST API Reference Catalog

### 5.1 Knowledge Graph Endpoints (`/api/graph/*`)
- **`POST /api/graph/upload`**:
  Uploads one or more raw seed documents (`multipart/form-data`). Returns `project_id` and normalized corpus metrics.
- **`POST /api/graph/ontology`**:
  Triggers LLM entity and relation extraction on uploaded text corpus.
- **`POST /api/graph/build`**:
  Dispatches batch ingestion to Zep Cloud / Neo4j and builds the knowledge graph asynchronously. Returns `task_id`.
- **`GET /api/graph/task/<task_id>`**:
  Monitors asynchronous ingestion progress percentage and processing stages.
- **`GET /api/graph/data/<graph_id>`**:
  Retrieves complete node and relationship topology to render the interactive `GraphPanel.vue` canvas.

### 5.2 Social Simulation Endpoints (`/api/simulation/*`)
- **`GET /api/simulation/entities/<graph_id>`**:
  Reads and filters graph entities that qualify for persona generation.
- **`POST /api/simulation/prepare`**:
  Synthesizes agent psychological profiles (Big Five OCEAN) and data-driven parameters across 7 platforms.
- **`POST /api/simulation/start`**:
  Launches multi-platform simulation subprocesses.
- **`GET /api/simulation/status/<simulation_id>`**:
  Retrieves execution state, active round index, and cumulative engagement metrics.
- **`POST /api/simulation/pause` & `POST /api/simulation/resume`**:
  Pauses or resumes social simulation rounds.
- **`POST /api/simulation/stop`**:
  Gracefully halts the simulation and shifts personas into interactive standby mode.
- **`POST /api/simulation/interview`**:
  Sends direct interview inquiries to a target persona via filesystem IPC and awaits its response.

### 5.3 Analytical Prediction Report Endpoints (`/api/report/*`)
- **`POST /api/report/generate`**:
  Initializes `ReportAgent` outline planning and runs the multi-turn ReACT cycle. Returns `report_id`.
- **`GET /api/report/status/<report_id>`**:
  Inspects chapter drafting progress and finalization state.
- **`GET /api/report/get/<report_id>`**:
  Retrieves the complete compiled Markdown predictive report.
- **`GET /api/report/logs/<report_id>`**:
  Streams or fetches the ReACT cognitive audit trail (*Thought, Action, Observation*) from `agent_log.jsonl`.
- **`POST /api/report/chat`**:
  Conducts interactive Q&A directly with `ReportAgent` regarding report findings.

### 5.4 Step 0 Web Research Endpoints (`/api/research/*`)
- **`POST /api/research/search`**:
  Executes private metasearch via SearXNG, sanitizes prompt injection vectors, and returns credible weighted facts.

---

## 6. Resilience Proof Gate Testing Procedures

To certify enterprise operational readiness, MiroFish must pass two rigorous proof gates:

```
                   ENTERPRISE RESILIENCE PROOF GATES
                   
       [ Gate E1: Unannounced Subprocess Kill Test (SIGKILL) ]
       ───────────────────────────────────────────────────────
       Round t Active ──► kill -9 PID ──► Restart Backend
                                                │
                                                ▼
       Verification: Scanner recovers Job to Round t via SHA-256 Checkpoint
       Simulation resumes to Round t+1 with ZERO duplicate actions!
       
       
       [ Gate E2: Network Partition & Provider Outage Test ]
       ─────────────────────────────────────────────────────
       Simulation Active ──► Sever Primary LLM ──► 9Router Circuit Breaker
                                                        │
                                                        ▼
       Verification: Seamless failover to Secondary / Local vLLM
       Zep Batch Ingestion drains without crashing simulation!
```

### 6.1 Gate E1: Unannounced Subprocess Kill Test (`kill -9`)
**Objective**: Prove that an unannounced process termination mid-round does not corrupt database integrity and that the simulation resumes seamlessly from the last verified checkpoint.

**Execution Steps**:
1. Start a 10-round simulation:
   ```bash
   curl -X POST http://127.0.0.1:5001/api/simulation/start -H "Content-Type: application/json" \
     -d '{"simulation_id": "sim-test-e1", "project_id": "proj-test"}'
   ```
2. Monitor execution until round 4 is reached:
   ```bash
   tail -f backend/app/uploads/simulations/sim-test-e1/simulation.log
   ```
3. Locate the simulation worker PID and send an unannounced kill signal:
   ```bash
   kill -9 <SIMULATION_WORKER_PID>
   ```
4. Restart the backend process:
   ```bash
   pm2 restart mirofish-backend
   ```
5. **Gate E1 Passing Criteria**:
   - `CrashRecoveryScanner` detects that the recorded PID is dead.
   - The job state in SQLite/PostgreSQL transitions to `paused`.
   - The checkpoint snapshot `round_004.snap` is validated against `round_004.sha256`.
   - Triggering `/api/simulation/resume` resumes execution directly at round 5 without re-executing rounds 1–4 and without duplicate rows in `actions.jsonl`.

### 6.2 Gate E2: Network Partition & 9Router Failover Test
**Objective**: Prove that upstream API outages or rate limit spikes (HTTP 429) are mitigated transparently without task failure.

**Execution Steps**:
1. During an active simulation, sever access to the primary LLM provider (e.g., block the provider domain via local firewall rules or supply a temporary invalid API key).
2. Inspect the gateway logs in `logs/9router.log`.
3. **Gate E2 Passing Criteria**:
   - The gateway captures initial failures and triggers exponential backoff retries with jitter.
   - Upon breaching failure thresholds, the *Circuit Breaker* opens and routes traffic to secondary models (Anthropic Claude or local Ollama/vLLM).
   - Agent prompts receive valid responses, and the simulation completes without entering `FAILED` status.
