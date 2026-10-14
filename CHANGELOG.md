# Changelog

All notable changes to the MiroFish Enterprise project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.3.0-enterprise] - 2026-10-15

### Added
- **Complete Indonesian Localization & 100% Key Parity (`locales/id.json`)**:
  - Full formal Indonesian translation across all namespaces: navigation, simulation workflow (Steps 0–5), graph exploration, historical databases, job recovery, system health monitoring, reporting, and logs.
  - Full 3-way key parity across `locales/en.json`, `locales/zh.json`, and `locales/id.json` (857 keys each, 0 missing keys, 0 placeholder mismatches).
- **Multi-locale Fallback Configuration (`frontend/src/i18n/index.js`)**:
  - Configured fallback chain `['en', 'zh']` ensuring clean fallback behavior without defaulting to untranslated Mandarin strings.
- **Dynamic Localization for Graph & Report Inspection**:
  - Extracted dynamic i18n keys for graph node properties, UUID, timestamps, entity types, edge labels, and self-relations in `frontend/src/components/GraphPanel.vue`.
  - Added localized interview dialogue state, selection reasons, and status labels in `frontend/src/components/Step4Report.vue`.
  - Localized dashboard recovery table status and health metric badges in `frontend/src/components/JobRecoveryTable.vue` and `frontend/src/components/HealthCards.vue`.

### Fixed
- Fixed untranslated English and Chinese strings appearing across UI views when Indonesian language is selected.
- Eliminated hardcoded Chinese characters in `GraphPanel.vue` and `Step4Report.vue` templates.
- Fixed missing i18n binding for dashboard subtitle and back button in `frontend/src/views/DashboardView.vue`.

---

## [3.2.0-enterprise] - 2026-10-14

### Added
- **MCP Server Stdio & REST API Integration (`backend/mcp_server`)**:
  - Implemented 7 operational MCP tools conforming to Model Context Protocol specification: `list_projects`, `get_job_status`, `get_simulation_report`, `search_knowledge_graph`, `run_web_research`, `create_simulation_job`, `start_simulation`, and `stop_simulation`.
  - Added real-time REST API fallback bridging MCP tool calls directly into MiroFish backend routes.
  - Dual schema compatibility: supporting both `inputSchema` (MCP standardized) and `parameters`.
  - Added automatic backend module path resolution in `backend/mcp_server/main.py`.
- **Domain Whitelist Support in Frontend (`frontend/vite.config.js`)**:
  - Added `allowedHosts: ['mirofish.biezz.my.id', 'localhost']` to allow secure reverse proxy access and Cloudflare Tunnel integration.
- **Graphiti Memory Platform Integration**:
  - Migrated knowledge graph memory layer from Zep Cloud to self-hosted Graphiti Platform with FalkorDB backends.
  - Added `GraphitiAdapter` with FastMCP ingestion queue and fallback to local GraphRAG.
  - Added 11 specialized Claude Swarm subagent definitions in `.claude/agents/`.
- **Step 0 & Step 1 Grounding & Anti-Hallucination Architecture (`wiki/step1-web-grounding-anti-halusinasi.md`)**:
  - Comprehensive scientific and technical documentation on Step 0 SearXNG web research and Step 1 GraphRAG knowledge modeling.
- **End-to-End Integration Test Runner (`backend/tests/test_all_steps.py`)**:
  - Automated integration testing suite verifying Steps 0 through 5.

### Changed
- **PM2 Ecosystem Configuration (`ecosystem.config.js`)**:
  - Updated working directories to canonical paths (`/home/biezz/Documents/Project/coding/Mirofish-enterprise`).
  - Switched Python interpreter to virtual environment executable (`.venv/bin/python`).
  - Set default LLM model to `mirofish-agent` via gateway `http://192.168.101.19:20128/v1`.
  - Configured SearXNG URL to `http://192.168.101.19:8089`.
  - Updated frontend PM2 dev server to port 3001.
- **Backend Configuration (`backend/app/config.py`)**:
  - Added default fallback for `SEARCHXNG_URL` pointing to `http://192.168.101.19:8089`.

### Fixed
- Fixed `Blocked request. This host ("mirofish.biezz.my.id") is not allowed` in Vite development server.
- Fixed NameError `name 'uuid' is not defined` in graph API route (`backend/app/api/graph.py`).
- Handled UTF-8 BOM stripping on stdio input lines in MCP server.
- Resolved HTTP 401 Unauthorized errors caused by missing Zep Cloud keys by introducing `LocalGraphService`.

---

## [3.1.0-enterprise] - 2026-10-04

### Added
- **Multi-Platform Social Simulation (7 Platforms)**:
  - Supported Twitter, X, Reddit, TikTok, Instagram, Facebook, and Threads algorithmic spaces.
  - Mathematical feed ranking algorithms and OCEAN psychological personality profiling.
- **Step 0 Web Research Powered by SearXNG**:
  - Self-hosted metasearch with 3-layer anti-prompt injection shield and domain credibility scoring.
- **SQLite WAL & Resilience Architecture**:
  - SHA-256 state checkpoint hashing, crash recovery scanner, and AES-256-GCM encrypted secrets vault.
- **Comprehensive Bilingual Documentation**:
  - Industrial-grade English (`README.md`, `wiki/en/`) and Indonesian (`README-ID.md`, `wiki/`) documentation.
- **Core Test Suite**:
  - 8/8 comprehensive tests passing with 100% coverage across core modules (`tests/test_v31_core.py`).

---

## [3.0.0-enterprise] - 2026-09-15

### Added
- Initial enterprise refactor of MiroFish social simulation engine.
- ReACT ReportAgent deduction and autonomous public sentiment forecasting.
- Local GraphRAG knowledge graph ingestion and dynamic ontology extraction.
