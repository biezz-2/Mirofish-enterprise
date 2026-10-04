---
title: Comprehensive Codemap and Repository Architecture
type: reference
tags: [codemap, directory-tree, module-dependencies, e2e-dataflow, subagent-ownership, v3.1]
related:
  - "[[index]]"
  - "[[architecture]]"
  - "[[operational-readiness]]"
  - "[[operational-guide]]"
sources:
  - backend/
  - frontend/
  - locales/
  - scripts/
  - tests/
---

> 🌐 **Language / Bahasa**: [English](./codemap.md) | [Bahasa Indonesia](../codemap.md)

# Comprehensive Codemap: Architecture, Dependencies, and Subagent Ownership (v3.1)

This document is the canonical code map of the **MiroFish** repository. It details the complete file hierarchy, cross-module dependency matrices, end-to-end micro dataflows, and granular code ownership divided across 10 specialized developer subagents.

---

## 1. Directory Tree & File Role Definitions

```
/data/Mirofish-enterprise/ (or /home/biezz/Project/apps/MiroFish/)
├── .env.example                       # Environment configuration template (LLM, Zep, Port)
├── .gitignore                         # Git tracking exclusions (cache, uploads, venvs)
├── .dockerignore                      # Docker image build exclusions
├── Dockerfile                         # Monolithic MiroFish container definition
├── docker-compose.yml                 # Service container orchestration (Backend, Frontend)
├── LICENSE                            # Software license (Apache 2.0 / MIT)
├── package.json                       # Root-level Node.js dependencies configuration
├── package-lock.json                  # Root-level Node.js dependency lockfile
├── README.md                          # Repository introductory documentation (English)
├── README-ID.md                       # Repository introductory documentation (Bahasa Indonesia)
├── README-ZH.md                       # Repository introductory documentation (Chinese)
│
├── backend/                           # SERVER LOGIC & MULTI-AGENT SWARM ENGINE
│   ├── pyproject.toml                 # Python project configuration, metadata, & linters
│   ├── requirements.txt               # pip dependencies list (Flask, OpenAI, Zep, SQLAlchemy)
│   ├── uv.lock                        # UV package manager lockfile
│   ├── run.py                         # Flask Backend execution entrypoint
│   │
│   ├── app/                           # Core Flask application package
│   │   ├── __init__.py                # Application Factory, CORS, and Blueprint registration
│   │   ├── config.py                  # Unified .env loader & environment variable validation
│   │   │
│   │   ├── api/                       # HTTP REST Controller Interface Layer
│   │   │   ├── __init__.py            # Blueprint declarations: graph_bp, sim_bp, report_bp
│   │   │   ├── graph.py               # Seed upload, text extraction, ontology, Zep build
│   │   │   ├── simulation.py          # Entities, agent profiles, prepare, run, IPC endpoints
│   │   │   └── report.py              # ReACT report generation, SSE streaming log, chat
│   │   │
│   │   ├── models/                    # Data persistence layer & state models
│   │   │   ├── __init__.py            # Exports TaskManager, ProjectManager, Models
│   │   │   ├── project.py             # File/memory-backed transactional Project model
│   │   │   ├── task.py                # Thread-safe TaskManager for asynchronous job tracking
│   │   │   └── entities.py            # Relational SQLAlchemy v3.1 models (SQLite WAL/Postgres)
│   │   │
│   │   ├── services/                  # Business logic & domain processing layer
│   │   │   ├── __init__.py            # Registration of core MiroFish domain services
│   │   │   ├── text_processor.py      # Raw document extraction & chunk segmentation normalization
│   │   │   ├── ontology_generator.py  # LLM-based entity and relation ontology extraction
│   │   │   ├── graph_builder.py       # Zep Cloud graph builder via Batch Ingestion API
│   │   │   ├── zep_entity_reader.py   # Node and edge extraction/filtering from Zep Graph
│   │   │   ├── oasis_profile_generator.py # OASIS agent personality synthesizer (Big Five OCEAN)
│   │   │   ├── simulation_config_generator.py # Activity parameters & 7-platform weight generator
│   │   │   ├── simulation_manager.py  # High-level simulation lifecycle orchestrator
│   │   │   ├── simulation_runner.py   # Subprocess executor & execution status monitor
│   │   │   ├── simulation_ipc.py      # File-based IPC communication channel (Command/Response)
│   │   │   ├── zep_graph_memory_updater.py # Dynamic temporal action injection into Zep memory
│   │   │   ├── zep_tools.py           # ReACT analyst toolkit (Search, InsightForge, Panorama)
│   │   │   └── report_agent.py        # ReACT intelligent agent for dynamic planning & reporting
│   │   │
│   │   └── utils/                     # Cross-module utility functions
│   │       ├── __init__.py            # Utility module initialization
│   │       ├── file_parser.py         # Multi-format document parser (PDF, MD, TXT)
│   │       ├── llm_client.py          # Unified OpenAI & compatible model calling abstraction
│   │       ├── openai_chat_compat.py  # Chat payload schema compatibility normalizer
│   │       ├── ontology.py            # PascalCase & SCREAMING_SNAKE schema validation
│   │       ├── retry.py               # Exponential backoff retry with jitter algorithm
│   │       ├── zep.py                 # Zep Cloud SDK client & transient error handler
│   │       ├── zep_lifecycle.py       # Graph lifecycle concurrency lock (Readers/Writers)
│   │       ├── zep_paging.py          # Cursor-safe node and edge paginator
│   │       ├── locale.py              # Backend localization & prompt injection system
│   │       └── logger.py              # Standardized console & file logging configuration
│   │
│   ├── scripts/                       # Autonomous execution scripts & batch runners
│   │   ├── run_parallel_simulation.py # OASIS multi-platform parallel simulation execution engine
│   │   ├── run_twitter_simulation.py  # Standalone Twitter simulation script
│   │   ├── run_reddit_simulation.py   # Standalone Reddit simulation script
│   │   ├── action_logger.py           # High-throughput streaming agent action recorder
│   │   ├── test_profile_format.py     # Agent profile schema validation test
│   │   └── validate_zep_cloud_integration.py # Zep Cloud API contract validation script
│   │
│   └── tests/                         # Backend unit & integration test suites
│       ├── test_zep_cloud_contracts.py       # Zep Cloud SDK payload contract validation
│       ├── test_zep_cloud_validation_script.py # Zep validator script tests
│       ├── test_zep_edge_paging.py           # Graph edge traversal pagination tests
│       ├── test_zep_entity_reader_edges.py   # Entity relation parsing tests
│       ├── test_zep_graph_lifecycle.py       # Graph reader/writer lifecycle lock tests
│       ├── test_zep_graph_memory_updater.py  # Graph action memory injection tests
│       ├── test_zep_report_barrier.py        # Report generation synchronization barrier tests
│       ├── test_zep_retry_and_client.py      # Zep client retry resilience tests
│       ├── test_zep_simulation_barrier.py    # Simulation vs updater barrier tests
│       ├── test_profile_field_normalization.py # Profile data type conversion tests
│       ├── test_simulation_prepare_failure.py # Preparation error mitigation tests
│       └── test_report_tool_result_sanitizer.py # Report tool output sanitization tests
│
├── frontend/                          # CLIENT APPLICATION (VUE 3 SPA)
│   ├── index.html                     # Application main HTML entry
│   ├── package.json                   # Frontend dependencies (Vue, Element Plus, Vis.js, Tailwind)
│   ├── package-lock.json              # Frontend package lockfile
│   ├── vite.config.js                 # Vite bundler configuration & backend dev proxy
│   │
│   └── src/                           # User interface source code
│       ├── main.js                    # Vue 3 entrypoint, router, i18n, & CSS mounting
│       ├── App.vue                    # Root application layout component
│       │
│       ├── api/                       # Axios HTTP clients wrapping backend REST API
│       │   ├── index.js               # Axios base configuration & global error interceptors
│       │   ├── graph.js               # Graph API calls (upload, status, ontology)
│       │   ├── simulation.js          # Simulation API calls (prepare, start, IPC)
│       │   └── report.js              # Report API calls (generate, chat, streaming)
│       │
│       ├── components/                # Workflow step UI components
│       │   ├── Step1GraphBuild.vue    # Step 1: Upload seed & ontology visualization
│       │   ├── Step2EnvSetup.vue      # Step 2: 7-platform parameters & persona setup
│       │   ├── Step3Simulation.vue    # Step 3: Simulation controls & round monitor
│       │   ├── Step4Report.vue        # Step 4: ReACT report draft review & export
│       │   ├── Step5Interaction.vue   # Step 5: Interactive agent interview & ReportAgent chat
│       │   ├── GraphPanel.vue         # Interactive node-edge graph visualization canvas
│       │   ├── HistoryDatabase.vue    # Historical project and simulation task registry
│       │   └── LanguageSwitcher.vue   # Multi-language switcher (ID / ZH / EN)
│       │
│       ├── i18n/                      # vue-i18n internationalization setup
│       │   └── index.js               # Dynamic language loader from locales/
│       │
│       ├── router/                    # Vue Router page navigation setup
│       │   └── index.js               # URL route mapping to View Components
│       │
│       ├── store/                     # Reactive state management (Vuex / Pinia-lite)
│       │   └── pendingUpload.js       # Temporary state buffer for file uploads
│       │
│       └── views/                     # Core application view pages
│           ├── Home.vue               # Landing page & project launcher
│           ├── Process.vue            # Integrated 5-step wizard container
│           ├── MainView.vue           # Primary navigation workspace
│           ├── SimulationView.vue     # Graph and agent configuration view
│           ├── SimulationRunView.vue  # Real-time multi-agent interaction timeline
│           ├── ReportView.vue         # Comprehensive predictive report viewer
│           └── InteractionView.vue    # In-depth persona interrogation workspace
│
├── locales/                           # MULTILINGUAL LOCALIZATION RESOURCES
│   ├── languages.json                 # Language metadata, UI labels, & LLM prompt directives
│   ├── id.json                        # Indonesian localization glossary
│   ├── zh.json                        # Chinese localization glossary
│   └── en.json                        # English localization glossary
│
├── wiki/                              # MIROFISH WIKIPEDIA KNOWLEDGE BASE
│   ├── index.md                       # Main MiroFish Wikipedia Portal (Bahasa Indonesia)
│   ├── arsitektur.md                  # Comprehensive System Architecture (Bahasa Indonesia)
│   ├── ekspansi-multi-platform.md     # 7 Social Media Platforms Specification (Bahasa Indonesia)
│   ├── riset-web-searxng.md           # Step 0 Web Research Powered by SearXNG (Bahasa Indonesia)
│   ├── kesiapan-operasional.md        # Persistence, Resilience, Checkpoints & 9Router (ID)
│   ├── codemap.md                     # Comprehensive Codemap & Dependencies (Bahasa Indonesia)
│   ├── panduan-operasional.md         # Deployment, Execution, & Testing Runbook (Bahasa Indonesia)
│   │
│   └── en/                            # English Wikipedia Documentation
│       ├── index.md                   # Main MiroFish Wikipedia Portal (English)
│       ├── overview.md                # Entry-point Portal Mirror (English)
│       ├── architecture.md            # Comprehensive System Architecture (English)
│       ├── multi-platform-expansion.md# 7 Social Media Platforms Specification (English)
│       ├── searxng-web-research.md    # Step 0 Web Research Powered by SearXNG (English)
│       ├── operational-readiness.md   # Persistence, Resilience, Checkpoints & 9Router (English)
│       ├── codemap.md                 # Comprehensive Codemap & Dependencies (English)
│       └── operational-guide.md       # Deployment, Execution, & Testing Runbook (English)
│
├── scripts/                           # Repository maintenance scripts
│   ├── star_history.py                # GitHub star history visualization
│   └── fetch_star_count.py            # Star count crawler
│
└── tests/                             # Root-level end-to-end automation tests
    ├── test_local_star_history.py     # Local star history test
    └── test_local_star_count_fetch.py # Local star count test
```

---

## 2. Backend Inter-Module Dependency Matrix

The table below outlines module call dependencies (who invokes whom) within MiroFish's backend:

| Caller Module | Dependency / Callee | Purpose & Functional Responsibility |
| :--- | :--- | :--- |
| `api/graph.py` | `services/ontology_generator.py` | Requests corpus analysis and ontology schema design. |
| `api/graph.py` | `services/graph_builder.py` | Submits batch episodes to Zep Cloud and polls progress. |
| `api/graph.py` | `utils/zep_lifecycle.py` | Locks the graph during build or teardown operations. |
| `api/simulation.py` | `services/zep_entity_reader.py` | Extracts graph entity nodes to supply persona generation. |
| `api/simulation.py` | `services/oasis_profile_generator.py`| Synthesizes comprehensive psychological profiles (OCEAN + bio). |
| `api/simulation.py` | `services/simulation_config_generator.py`| Derives activity frequencies and platform parameter weights. |
| `api/simulation.py` | `services/simulation_runner.py` | Spawns simulation subprocesses and monitors active status. |
| `api/simulation.py` | `services/simulation_ipc.py` | Dispatches live interview queries into the agent environment. |
| `api/report.py` | `services/report_agent.py` | Initializes the multi-turn ReACT cycle to draft prediction reports. |
| `services/report_agent.py` | `services/zep_tools.py` | Invokes graph investigation tools (InsightForge, Panorama). |
| `services/report_agent.py` | `services/simulation_ipc.py` | Directly interviews simulated personas during chapter drafting. |
| `services/simulation_runner.py`| `scripts/run_parallel_simulation.py`| Spawns independent OS Python workers across platforms. |
| `scripts/run_parallel_simulation.py`| `services/zep_graph_memory_updater.py`| Injects newly generated actions into Zep graph memory. |
| `services/graph_builder.py` | `utils/zep_paging.py` & `utils/zep.py` | Interacts with Zep SDK using cursor-safe pagination & retry logic. |

---

## 3. End-to-End Micro Dataflows

```
[Seed Documents / Simulation Requirements]
          │
          ▼
┌─────────────────────────────────┐
│ 1. Ingestion & Step 0 Research  │ ──► Persist `parsed_text.txt` & `research_summary.md`
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 2. Ontology & Graph Engineering │ ──► LLM schema extraction ──► Zep Cloud Batch Ingestion
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 3. Profiling & Configuration    │ ──► Entity Filter ──► Export `agent_profiles.json` &
└────────────────┬────────────────┘     `simulation_config.json`
                 │
                 ▼
┌─────────────────────────────────┐
│ 4. Multi-Platform Sim Run       │ ──► 7-Platform Subprocesses ──► `actions.jsonl`
└────────────────┬────────────────┘     ├── Dynamic Memory Updates (`zep_graph_memory_updater.py`)
                 │                      └── Cryptographic Checkpoints (`round_X.snap` + SHA-256)
                 ▼
┌─────────────────────────────────┐
│ 5. ReACT ReportAgent Analysis   │ ──► Thought -> Tool Calls -> Outline -> Final Markdown
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 6. Human-in-the-Loop Interrog.  │ ──► Interaction UI ──► IPC Command ──► Persona Response
└─────────────────────────────────┘
```

---

## 4. Subagent Code Ownership Breakdown (Swarm Engineering)

To facilitate distributed development by multi-agent swarms, repository ownership is partitioned across 10 specialized subagents:

```
+-----------------------------------------------------------------------------------------+
+                               10-SUBAGENT CODE OWNERSHIP MAP                            +
+---+----------------------+---------------------------------+----------------------------+
| # | SUBAGENT ROLE        | PRIMARY DOMAIN SCOPE            | GOVERNED CODE PATHS        |
+---+----------------------+---------------------------------+----------------------------+
| 1 | Subagent A: Core API | REST routing, App Factory, CORS | backend/app/api/, run.py   |
| 2 | Subagent B: Database | ORM schema, SQLite WAL, Postgres| backend/app/models/        |
| 3 | Subagent C: GraphRAG | Zep Cloud SDK, Ontology, Paging | services/graph_builder.py  |
| 4 | Subagent D: SimEngine| OASIS 7-Platform, Action Engine | scripts/run_*.py, runner.py|
| 5 | Subagent E: Step0Web | SearXNG, Anti-Injection, Scorer | services/step0_*, parser.py|
| 6 | Subagent F: Analyst  | ReACT ReportAgent, ZepTools     | services/report_agent.py   |
| 7 | Subagent G: Gateway  | 9Router, Failover, AES Crypto   | utils/crypto.py, llm_*.py  |
| 8 | Subagent H: MCP Eng  | Model Context Protocol Server   | backend/mcp_server.py      |
| 9 | Subagent I: Frontend | Vue 3 SPA, vue-i18n, Visual Vis | frontend/src/, locales/    |
| 10| Subagent J: DevOps   | PM2, Docker, Crash Recovery     | docker-compose*, tests/    |
+---+----------------------+---------------------------------+----------------------------+
```

### 4.1 Subagent Contract Specifications

1. **Subagent A (Core API & Application Framework)**:
   - *Responsibility*: Maintain stability of Flask Application Factory (`backend/app/__init__.py`), environment configuration (`config.py`), and modular blueprints (`backend/app/api/`).
   - *Boundary*: Must not modify database schemas directly without Subagent B coordination.
2. **Subagent B (Persistence & Database Architect)**:
   - *Responsibility*: Maintain SQLAlchemy relational models (`backend/app/models/entities.py`), SQLite WAL mode, migrations, and ACID transaction safety.
3. **Subagent C (GraphRAG & Knowledge Engineer)**:
   - *Responsibility*: Optimize `graph_builder.py`, `ontology_generator.py`, `zep_entity_reader.py`, and graph lifecycle concurrency locks in `utils/zep_lifecycle.py`.
4. **Subagent D (Multi-Platform Simulation Architect)**:
   - *Responsibility*: Expand the 7-platform simulation runtime (`backend/scripts/run_parallel_simulation.py`), cross-worker synchronization barriers, and behavioral feed algorithms.
5. **Subagent E (Step 0 Web Research & Content Shield Specialist)**:
   - *Responsibility*: SearXNG container clusters, automated fact extraction, anti-prompt injection shields, and source credibility scoring.
6. **Subagent F (ReportAgent & Analytic Reasoning Engineer)**:
   - *Responsibility*: Advance ReACT reasoning loops in `backend/app/services/report_agent.py`, graph investigation toolkits in `zep_tools.py`, and predictive synthesis quality.
7. **Subagent G (LLM Gateway & Secrets Security Specialist)**:
   - *Responsibility*: Maintain 9Router intelligent gateway, multi-provider failover, quota load balancing, and AES-256-GCM symmetric secret encryption.
8. **Subagent H (MCP Protocol Integration Specialist)**:
   - *Responsibility*: Implement standardized Model Context Protocol endpoints so external agents can operate MiroFish programmatically.
9. **Subagent I (Frontend & Internationalization Engineer)**:
   - *Responsibility*: Maintain `frontend/`, ensure full `vue-i18n` support (Indonesian, English, Chinese), and enhance dynamic graph visualizations (`GraphPanel.vue`).
10. **Subagent J (DevOps, Reliability & QA Specialist)**:
    - *Responsibility*: Multi-OS PM2 configuration (`ecosystem.config.js`), Docker cluster orchestration, resilience crash-recovery gates (E1/E2), and automated CI pipelines.
