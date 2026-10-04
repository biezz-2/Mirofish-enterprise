---
title: Operational Readiness, Persistence, and System Resilience
type: concept
tags: [operational-readiness, sqlite-wal, postgresql, crash-recovery, aes-gcm, 9router, mcp-server, v3.1]
related:
  - "[[index]]"
  - "[[architecture]]"
  - "[[operational-guide]]"
  - "[[codemap]]"
sources:
  - backend/app/models/entities.py
  - backend/app/models/task.py
  - backend/app/models/project.py
  - backend/app/config.py
---

> 🌐 **Language / Bahasa**: [English](./operational-readiness.md) | [Bahasa Indonesia](../kesiapan-operasional.md)

# Operational Readiness, Persistence, and System Resilience: MiroFish v3.1 Enterprise

This document provides technical specifications for operational resilience and enterprise readiness in MiroFish v3.1. Large-scale social simulation sandboxes require robust data integrity guarantees, zero-loss crash recovery, encrypted secret vaults, and standard protocol integrations.

---

## 1. Transactional Relational Schema (SQLite WAL & PostgreSQL)

In legacy versions, project and task states were stored across disparate JSON files (`project_state.json`, `run_state.json`), which were susceptible to file corruption under ungraceful power loss or OS termination.

MiroFish v3.1 implements an enterprise persistence layer using **SQLAlchemy ORM** (`backend/app/models/entities.py`) supporting dual database environments:
- **SQLite with Write-Ahead Logging (WAL)**: Out-of-the-box standard for standalone, single-node, and development installations. WAL permits concurrent non-blocking reads while high-frequency simulation actions are committed.
- **PostgreSQL**: Clustered multi-instance enterprise deployments.

```
                      +-----------------------------+
                      |        ProjectModel         |
                      | (id, name, desc, created_at)|
                      +--------------+--------------+
                                     │ 1:N
                                     ▼
                      +-----------------------------+
                      |          TaskModel          |
                      | (id, project_id, type, stat)|
                      +--------------+--------------+
                                     │ 1:N
                                     ▼
                      +-----------------------------+
                      |          JobModel           |
                      | (id, task_id, state, pid,   |
                      |  current_round, total_round)|
                      +--------------+--------------+
                                     │ 1:N
                                     ▼
                      +-----------------------------+
                      |       CheckpointModel       |
                      | (id, job_id, round, path,   |
                      |  sha256_hash, created_at)   |
                      +-----------------------------+
```

### 1.1 Core Relational Schema Tables (`backend/app/models/entities.py`)

1. **`projects` (`ProjectModel`)**:
   Stores simulation project identity, narrative descriptions, timestamps, and cascading foreign-key relationships.
2. **`tasks` (`TaskModel`)**:
   Tracks macro tasks (`graph_build`, `profile_generation`, `simulation_run`, `report_generation`), status, and parameters.
3. **`jobs` (`JobModel`)**:
   Tracks operating system execution units. Records OS PID, active virtual round (`current_round`), progress percentage, and error logs.
4. **`checkpoints` (`CheckpointModel`)**:
   Preserves per-round simulation snapshots complete with file paths and SHA-256 cryptographic hashes.
5. **`platforms_config` (`PlatformConfigModel`)**:
   Stores parameterized weights and configurations for all 7 social platforms tied to a project.
6. **`research_reports` (`ResearchReportModel`)**:
   Step 0 SearXNG research outputs: verified facts, extracted entities, and domain credibility scores.
7. **`settings` (`SettingsModel`)**:
   Encrypted key-value store for API keys and secrets (`value_encrypted`).
8. **`audit_log` (`AuditLogModel`)**:
   Immutable append-only audit trail logging administrative and user actions.

---

## 2. Finite State Machine & WAL Pragmas

```
  [QUEUED] ──► [INITIALIZING] ──► [RUNNING] ──► [CHECKPOINTING] ──► [COMPLETED]
                                     │   ▲              │
                            (Pause)  │   │ (Resume)     │
                                     ▼   │              │
                                  [PAUSED]              │
                                     │                  │
                          (Crash / SIGKILL)             │
                                     │                  ▼
                                     ▼          [INTEGRITY_CHECK]
                              [ABNORMAL_EXIT]           │
                                     │                  ▼
                                     ▼          [ROUND_COMMITTED]
                              [RECOVERING] ─────────────┘
```

SQLite databases initialize with strict concurrency pragmas:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

---

## 3. Round Checkpoint Hashing & Crash Recovery Scanner

Multi-agent simulations running over hundreds of rounds face operational disruptions (out-of-memory errors, kernel kills, server reboots).

### 3.1 Per-Round Checkpointing Algorithm
At the conclusion of each virtual round \(R\):
1. **Barrier Synchronization**: The orchestrator waits until all 7 platform workers finish round \(R\).
2. **State Serialization**: Agent cognitive memories, feed states, and message queues are written to:
   `uploads/simulations/<sim_id>/checkpoints/round_<R>.snap`
3. **Checksum Verification**: The system calculates a cryptographic SHA-256 hash:
   \[
   H = \text{SHA256}(\text{FileBytes})
   \]
4. **Transactional Commit**: A row is inserted into `checkpoints` recording `round_number`, `snapshot_path`, and `sha256_hash`.
5. **Job Update**: The `current_round` in `jobs` is bumped to \(R\).

### 3.2 Boot-Time Crash Recovery Scanner
Upon server startup, the `CrashRecoveryScanner` automatically audits orphaned jobs:

```python
# backend/app/services/recovery_scanner.py (Core Logic)
import os, hashlib
from datetime import datetime

def scan_and_recover_orphaned_jobs(db_session):
    orphaned_jobs = db_session.query(JobModel).filter(
        JobModel.state.in_(["running", "checkpointing"])
    ).all()

    for job in orphaned_jobs:
        if not is_process_alive(job.pid):
            logger.warning(f"Detected orphaned job: {job.id} (PID {job.pid})")
            latest_cp = db_session.query(CheckpointModel).filter_by(job_id=job.id)\
                .order_by(CheckpointModel.round_number.desc()).first()

            if latest_cp and verify_sha256(latest_cp.snapshot_path, latest_cp.sha256_hash):
                job.state = "paused"
                job.current_round = latest_cp.round_number
                job.error_message = f"Recovered at round {latest_cp.round_number} during startup"
                logger.info(f"Job {job.id} successfully restored to round {latest_cp.round_number}")
            else:
                job.state = "failed"
                job.error_message = "Unrecoverable crash: Checkpoint missing or corrupted"
            
            job.updated_at = datetime.utcnow()
            db_session.commit()
```

---

## 4. Secret Management & AES-256-GCM Encryption

To comply with enterprise data protection regulations, sensitive API tokens and credentials are never stored in plaintext.

- **Algorithm**: AES-256-GCM (*Galois/Counter Mode*) ensuring simultaneous confidentiality and message authentication.
- **Key Derivation**: Master key derived from `MASTER_APP_SECRET` using PBKDF2-HMAC-SHA256 (100,000 iterations + unique salt).
- **Format**: Stored as Base64-encoded `[IV 12-byte] + [Ciphertext] + [Auth Tag 16-byte]` in the `settings` table.

```python
# backend/app/utils/crypto.py
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecretVault:
    def __init__(self, master_key_bytes: bytes):
        self.aesgcm = AESGCM(master_key_bytes)

    def encrypt_secret(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt_secret(self, payload_b64: str) -> str:
        raw = base64.b64decode(payload_b64.encode('utf-8'))
        nonce = raw[:12]
        ciphertext = raw[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
```

---

## 5. 9Router Intelligent Gateway Architecture

Multi-agent simulations dispatch thousands of LLM API requests within minutes. Relying on a single provider endpoint introduces acute rate-limiting risks (HTTP 429) and upstream outage vulnerabilities.

**9Router** serves as an intelligent proxy gateway:

```
                  ┌────────────────────────────────────────┐
                  │            Agent / LLM Call            │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │            9Router Gateway             │
                  │  - Circuit Breaker Status Tracker      │
                  │  - Dynamic Quota Load Balancer         │
                  │  - Semantic Response Cache             │
                  └──────┬────────────┬────────────┬───────┘
                         │            │            │
           (Primary)     │    (Fail)  │    (Fail)  │
            ┌────────────┘            │            └────────────┐
            ▼                         ▼                         ▼
  ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
  │  OpenAI Endpoint  │     │ Anthropic Claude  │     │ DeepSeek / Local  │
  │  (gpt-4o / mini)  │     │ (claude-3-5-sonnet│     │ (vLLM / Ollama)   │
  └───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 5.1 9Router Key Features
1. **Exponential Retry with Jitter**: Automatically absorbs transient network glitches (500, 502, 503, 504, 429).
2. **Multi-Provider Failover**: Seamlessly routes traffic to secondary models (Anthropic, DeepSeek, local vLLM) when primary quotas exhaust.
3. **Semantic Caching**: In-memory caching for deterministic persona generation and grammar validations to minimize latency and token expenditure.

---

## 6. Integrated Model Context Protocol (MCP) Server

MiroFish v3.1 features a native **Model Context Protocol (MCP)** server (`backend/mcp_server/`), enabling external AI assistants (Claude Desktop, Cursor IDE, agent swarms) to drive simulations programmatically.

### 6.1 Provided MCP Tools Catalog

| MCP Tool Name | Arguments | Description |
| :--- | :--- | :--- |
| `run_simulation` | `project_id`, `platforms`, `rounds`, `requirement` | Triggers a predictive social simulation run and returns Job ID. |
| `query_social_graph` | `graph_id`, `query_text`, `limit` | Extracts nodes, relational paths, and collective memories from Zep/Neo4j. |
| `interview_agent` | `simulation_id`, `agent_id`, `question` | Dispatches real-time interview inquiries via IPC directly to simulated personas. |
| `get_prediction_report`| `report_id` | Fetches draft sections or final compiled analytical prediction reports. |
| `search_step0` | `query`, `categories` | Executes private SearXNG research to verify real-time topics and news facts. |
