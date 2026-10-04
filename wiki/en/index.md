---
title: MiroFish - Swarm Intelligence & Predictive Social Simulation Engine
type: overview
tags: [mirofish, swarm-intelligence, social-simulation, graphrag, multi-platform, v3.1]
sources:
  - ./
  - backend/
  - frontend/
  - locales/
---

> 🌐 **Language / Bahasa**: [English](./index.md) | [Bahasa Indonesia](../index.md)

# MiroFish: Main Wiki Portal (v3.1 Enterprise)

Welcome to the Official Documentation and Architectural Wiki Portal of **MiroFish**. This documentation synthesizes the theoretical foundations, system architecture, codebase implementation, multi-platform specifications, integrated research capabilities, operational resilience, and deployment runbooks for this cutting-edge swarm intelligence social simulation platform.

---

## 1. System Overview (Executive Summary)

**MiroFish** is a next-generation social prediction and simulation engine powered by autonomous multi-agent systems. By extracting real-world seed information—such as breaking news headlines, public policy drafts, financial market signals, or complex literary narratives—MiroFish automatically constructs a high-fidelity parallel digital sandbox.

Within this simulation space, hundreds to thousands of intelligent agents with distinct psychological profiles, long-term episodic and semantic memory (powered by GraphRAG), and individual action logic interact dynamically. These microscopic agent-level interactions trigger collective emergence, enabling analysts, policymakers, and researchers to rehearse future scenarios, conduct "what-if" impact analyses, and proactively mitigate social risks before they manifest in reality.

```
                          ┌────────────────────────┐
                          │     Seed Material      │
                          │(News / Data / Policy)  │
                          └───────────┬────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │   Step 0: SearXNG Web Research │
                      │ (Validation & Fact Enrichment) │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │   GraphRAG Knowledge Engine    │
                      │ (Zep Cloud / Standalone Graph) │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 7-Platform Simulation Sandbox  │
                      │ (Twitter, X, Reddit, TikTok,   │
                      │  Instagram, Facebook, Threads) │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │    ReportAgent ReACT Engine    │
                      │ (Interviews, Analytics, Report)│
                      └────────────────────────────────┘
```

---

## 2. Vision and Design Philosophy

### 2.1 Bridging Macro and Micro
1. **Macro Level (Zero-Risk Decision Laboratory)**: Government institutions and enterprise organizations can test regulatory reception, crisis PR responses, and capital market sentiment volatility in a digital sandbox without real-world consequences.
2. **Micro Level (Creative Sandbox & Narrative Exploration)**: Researchers and creators can deduce literary plotlines (such as reconstructing the lost ending of the classical masterpiece *Dream of the Red Chamber*), map campus community public opinion dynamics (such as the Wuhan University case study), or engage in interactive sociological exploration.

### 2.2 Core Architectural Principles (The Architecture Creed)
- **Data-Driven Parameterization**: Simulation parameters are not arbitrary guesses; they are derived deterministically from entity graph analysis and empirical factual enrichment.
- **Strict Isolation & Idempotency**: Each simulation run maintains an isolated storage workspace, per-round state checkpoints, and robust crash-recovery capabilities.
- **Anti-Hallucination & Content Shielding**: All external web data gathered via metasearch undergoes rigorous anti-prompt injection sanitization before reaching agent memory or the knowledge graph.
- **Full Bilingual & Localization Support**: First-class support for English, standard Indonesian (PUEBI-compliant), and Chinese across UI strings (`vue-i18n`), agent cognitive personas, error handling, and generated analytical reports.

---

## 3. Evolution Timeline: Towards v3.1 Enterprise Architecture

MiroFish has evolved significantly from an experimental prototype to an industry-grade, production-ready simulation platform:

| Architectural Dimension | MiroFish v1.0 / v2.0 (Legacy) | MiroFish v3.1 Enterprise (Current) |
| :--- | :--- | :--- |
| **Platform Support** | Limited to Twitter & Reddit (dual-platform OASIS script). | **7-Platform Ecosystem**: Twitter, X, Reddit, TikTok, Instagram, Facebook, and Threads with custom algorithmic profiles. |
| **Initial Fact Injection** | Reliant strictly on static user-uploaded text/PDF files. | **Step 0 Autonomous Web Research**: Private self-hosted SearXNG metasearch cluster with source credibility scoring and anti-injection shields. |
| **State Persistence** | Volatile in-memory dictionaries and fragmented local JSON files. | **Transactional SQLAlchemy (SQLite WAL / PostgreSQL)**: Full ACID relational schema, round-by-round checkpoints, and automated recovery scanning. |
| **Process Resilience** | Vulnerable to complete progress loss if background process terminated. | **Zero-Loss Crash Recovery Scanner**: Resumes simulations seamlessly from the latest confirmed round (\(R_{last}\)) without history loss. |
| **LLM Gateway** | Direct single-endpoint calls to OpenAI API. | **9Router Intelligent Gateway**: Multi-provider failover (Anthropic, DeepSeek, vLLM), dynamic quotas, circuit breaking, and AES-GCM secret encryption. |
| **Ecosystem & Integration** | Isolated internal REST endpoints for web dashboard. | **Model Context Protocol (MCP) Server**: MiroFish functions as a standardized MCP tool provider for external AI agent ecosystems. |
| **Localization** | Predominantly Chinese and English. | **Comprehensive Multi-language Support**: Complete Vue-i18n UI, localized persona prompts (English, Indonesian PUEBI, Chinese), standardized API errors. |
| **Orchestration & Ops** | Ad-hoc manual Python script execution. | **PM2 Multi-Platform Process Manager & Multi-Service Docker Compose** (Neo4j, SearXNG, Flask Backend, Vite Frontend). |

---

## 4. Core System Components

1. **GraphRAG Builder & Zep Cloud Integration (`backend/app/services/graph_builder.py`)**:
   Automatically extracts entity and relationship ontologies using LLMs, constructing high-performance Standalone Knowledge Graphs in Zep Cloud via episode-oriented Batch Ingestion APIs.
2. **OASIS Profile & Config Generator (`backend/app/services/oasis_profile_generator.py` & `simulation_config_generator.py`)**:
   Translates graph entity nodes into comprehensive OASIS agent psychological profiles (name, bio, Big Five OCEAN traits, affective biases, and temporal activity distributions).
3. **Multi-Platform Simulation Runner (`backend/scripts/run_parallel_simulation.py` & `simulation_runner.py`)**:
   Orchestrates multi-round parallel simulation runs across social media platforms, monitors posts, comments, reposts, and reactions, updates temporal graph memory dynamically, and streams structured logs (`actions.jsonl`).
4. **ReportAgent Engine (`backend/app/services/report_agent.py`)**:
   Autonomous analyst agent operating on the ReACT (*Reasoning + Acting*) paradigm, leveraging investigation tools (InsightForge, Panorama, Search, and Direct Agent Interviews) to generate rigorous predictive reports.
5. **Interactive Interview Subsystem (`backend/app/services/simulation_ipc.py`)**:
   Transactional file-based Inter-Process Communication (*IPC*) mechanism enabling human analysts or ReportAgent to interview any simulated agent persona in real-time.
6. **Modern Web Frontend (`frontend/`)**:
   Responsive SPA built with Vue 3, Vite, TailwindCSS, and Element Plus featuring dynamic knowledge graph visualization (GraphPanel), real-time action telemetry, and runtime locale switching.

---

## 5. Documentation Wiki Index & Navigation

Explore the technical depth of MiroFish v3.1 across the following dedicated chapters:

* **[[architecture|architecture.md]] - Comprehensive System Architecture**:
  Detailed comparison of legacy vs. v3.1 tiers, end-to-end dataflow diagrams, service topologies, and multi-tenant data partitioning.
* **[[multi-platform-expansion|multi-platform-expansion.md]] - 7 Social Media Platform Specifications**:
  Mathematical algorithms (recency, popularity, echo chamber, virality thresholds), action space enums, and agent behavioral models for Twitter, X, Reddit, TikTok, Instagram, Facebook, and Threads.
* **[[searxng-web-research|searxng-web-research.md]] - Step 0 SearXNG Web Research**:
  Private metasearch engine architecture, Docker deployment, factual entity linking, credibility scoring heuristics, and anti-prompt injection shielding.
* **[[operational-readiness|operational-readiness.md]] - Persistence, Resilience, and Infrastructure**:
  ACID SQLAlchemy models, SQLite WAL state machine, SHA-256 round checkpointing, zero-loss crash recovery, AES-256-GCM encryption, 9Router Gateway, and MCP server.
* **[[codemap|codemap.md]] - Canonical Code Map**:
  Repository directory hierarchy, module dependency matrix, micro end-to-end data pipelines, and subagent module ownership breakdown.
* **[[operational-guide|operational-guide.md]] - Deployment, Runbook, and Field Testing**:
  Production deployment with PM2 across Linux/Windows/macOS, Docker Compose orchestration, comprehensive REST API catalog, and recovery fault-injection tests.

---

## 6. Glossary of Technical Terms

* **Swarm Intelligence**: The emergent collective behavior of decentralized, self-organized agents interacting locally with their environment and one another.
* **GraphRAG**: Retrieval-Augmented Generation that utilizes knowledge graph structures (entities and semantic relations) to enrich contextual reasoning in LLMs.
* **Standalone Graph**: An isolated knowledge graph instance in Zep Cloud dedicated to a single project session without cross-contamination.
* **Episode Batch Ingestion**: Grouped transaction submission of text fragments to graph APIs to construct nodes and edges deterministically.
* **OASIS Platform**: An open-source simulation engine modeling social media feeds, user actions, and temporal progression.
* **ReACT Pattern**: An LLM reasoning paradigm combining interleaved cycles of *Thought*, *Action* (tool execution), and *Observation*.
* **Step 0**: The pre-simulation phase where the system autonomously gathers and validates external web facts to enrich seed data before graph construction.
* **IPC (Inter-Process Communication)**: A file-based protocol using `commands/` and `responses/` channels between the Flask REST API and OASIS simulation workers.
* **WAL (Write-Ahead Logging)**: An SQLite concurrency mode allowing concurrent reads while writes are committed in an append-only log.
* **9Router**: An intelligent LLM proxy layer managing provider failover, dynamic rate limits, and load distribution.
