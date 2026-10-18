# Changelog

All notable changes to the MiroFish Enterprise project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.6.0-enterprise] - 2026-10-18

### Added
- **Multi-Platform Algorithm & Human-Like AI Comment Simulator Engine (`backend/app/services/simulation/`)**:
  - Implemented 6-stage Home-Mixer feed pipeline (`Source`, `Hydrator`, `Filter`, `Scorer`, `Selector`, `SideEffect`) in `feed_pipeline.py`.
  - Added versioned YAML platform profile store in `platform_profile_store.py` (`x@2026-10.yaml`, `reddit@2026-10.yaml`, `tiktok@2026-10.yaml`, `meta@2026-10.yaml`), unifying Twitter and X into a single platform with 280 / 25,000 character regimes.
  - Added rich multi-dimensional agent persona generator in `persona_store.py` (Big Five OCEAN, Indonesian demographics, registers, log-normal comment length distributions, baseline anger).
  - Implemented 7-intent taxonomy multinomial sampler in `intent_sampler.py` calibrated to empirical Dataset B frequencies.
  - Added thread transcript few-shot prompt builder in `style_realizer.py` for realistic conversational dynamics.
  - Added deterministic post-LLM noise layer in `noise_layer.py` (Indonesian internet slang/abbreviation dictionary, 1-3% QWERTY neighbor key swaps, repeated punctuation quirks, and regional dialect mixing).
  - Implemented opinion dynamics modeling in `opinion_dynamics.py` combining Bounded Confidence (Deffuant/Hegselmann-Krause), emotional contagion, and Hawkes self-exciting point processes for cascade arrival bursts.
  - Implemented stylized facts validator in `calibration_harness.py` (90-9-1 participation inequality, Pareto heavy-tail cascade distribution, diurnal cycles).
  - Implemented comprehensive evaluation suite in `evaluation_suite.py` (Classifier Two-Sample Test proxy, Type-Token Ratio, perplexity, Self-BLEU, and 8-gram leakage detection with zero seed overlap).
  - Implemented `EthicsGuard` sandbox lock in `ethics_guard.py` (refusal of live social platform API connections, mandatory `is_synthetic: true` metadata, export watermark "HASIL SIMULASI — BUKAN DATA NYATA", and structured audit logs).
  - Added comprehensive test suite `backend/tests/test_simulation_engine_v36.py` (10/10 passed).
- **Personal Data Protection & Privacy Compliance (UU PDP No. 27/2022)**:
  - Created automatic PII scrubber in `backend/app/services/pii_scrubber.py` redacting 16-digit NIK, Indonesian phone numbers (+62 / 08xx), email addresses, financial/banking numbers, and targeted names with idempotent execution.
  - Integrated PII scrubbing into Step 0 web research ingestion and Step 1 knowledge graph building pipelines (`web_research_service.py`, `anti_injection.py`, `text_processor.py`, `graph_builder.py`, `local_graph_service.py`).
  - Added formal compliance policy in `docs/privacy-ID.md` and ethical usage guidelines in `USAGE.md`.
  - Added test suite `backend/tests/test_pii_scrubber.py` (17/17 passed).
- **Token Budget & Cost Estimator (`backend/app/services/token_cost_estimator.py`)**:
  - Calibrated against empirical OASIS baseline (~335.6k tokens per 100 agents / 10 rounds).
  - Multi-provider pricing models (Claude 3.5 Sonnet, GPT-4o, local Llama 3) with USD/IDR conversion and phase budget allocation recommendations.
  - Added test suite `backend/tests/test_token_cost_estimator.py` (17/17 passed).
- **Automated Documentation & Test Registry Generator (`scripts/gen_docs.py`)**:
  - Deterministic AST extraction generating `docs/mcp-catalog.md` (22 tools) and `docs/test-registry.md` (48 test files, 449 test cases) with `--check` verification for CI/CD zero-drift enforcement.
- **Service Containerization & Multi-Stage Builds**:
  - Created `backend/Dockerfile` multi-stage `python:3.12-slim` with non-root user `mirofish` (1000:1000), internal port 8000, and HTTP healthcheck.
  - Created `backend/Dockerfile.graphiti` (port 8090, uvicorn service, healthcheck).
  - Created `backend/Dockerfile.mcp` (port 8091, FastMCP streamable-http, healthcheck).
  - Created `frontend/Dockerfile` multi-stage Node 20 + Nginx alpine (port 3000, SPA routing fallback, `/health` endpoint).
  - Documented MCP transport dual-mode specification in `wiki/en/mcp-specification.md`.
- **Automated Blocking CI Workflow (`.github/workflows/tests.yml`)**:
  - Added automated GitHub Actions test runner executing backend pytest suite and frontend production build on push and pull request to `main`.

### Changed
- **License Reconciliation & Legal Attribution**:
  - Synchronized `README.md` and `README-ID.md` license declaration and badges from MIT to GNU AGPL-3.0 to match `LICENSE`.
  - Created root `NOTICE` file containing explicit AGPL-3.0 Section 13 network source code notice and attribution to upstream `666ghj/MiroFish` (AGPL-3.0) and `camel-ai/oasis` (Apache-2.0).
- **Port Unification & SQLite WAL Concurrency**:
  - Unified all backend ports to 8000 across configuration, documentation, Vite frontend proxy, and docker-compose.
  - Enforced `instances: 1, exec_mode: 'fork'` in `ecosystem.config.js` to eliminate multi-process write corruption on SQLite WAL databases.
- **Docker Compose Hardening (`docker-compose.yml`)**:
  - Removed deprecated `version: '3.8'` syntax.
  - Removed default password `mirofish_secret_pass`, mandating `${NEO4J_PASSWORD:?}` and `${REDIS_PASSWORD:?}` via environment interpolation.
  - Added healthchecks across all database, graphiti, mcp-server, backend, and frontend containers.

### Security
- **Fail-Fast Startup Security Guard (`validate_startup_security`)**:
  - Server boot immediately aborts in production mode (`FLASK_DEBUG=false`) if `SECRET_KEY` is missing, short, or matches insecure test patterns, or if `DEVELOPMENT_MODE=true`.
  - Added unit test suite `backend/tests/test_startup_security_guard.py` (16/16 passed).
- **JWT Authentication Hardening (`backend/app/utils/auth.py`)**:
  - Pinned algorithm to `HS256` (`ALLOWED_JWT_ALGORITHMS = ["HS256"]`).
  - Enforced signature verification and validated claims (`exp`, `iss`, `aud`) with explicit 401 error payloads.
  - Added unit test suite `backend/tests/test_jwt_hardening.py` (16/16 passed).
- **Frontend Strict XSS & DOM Sanitization (`frontend/src/utils/sanitize.js`)**:
  - Hardened markdown link rendering against dangerous URI schemes (`javascript:`, `vbscript:`, `data:text/html`).
  - Sanitized dynamic HTML to block script injection and dangerous inline event handlers.
- **Redis Password Authentication & SQLite WAL Enforcement**:
  - Created `backend/app/utils/redis_client.py` enforcing authentication credentials and blocking anonymous connections when `REDIS_PASSWORD` is configured.
  - Created `backend/app/utils/sqlite_engine.py` standardizing `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` across SQLAlchemy connection pools.
  - Added unit test suite `backend/tests/test_redis_auth_hardening.py` (14/14 passed).
- **Blocking Security Scanning CI (`.github/workflows/security-scan.yml`)**:
  - Removed `|| true` from Bandit and pip-audit steps.
  - Removed `continue-on-error: true` from Gitleaks.
  - Enforced exit code 1 on Trivy filesystem scan when HIGH or CRITICAL vulnerabilities are found.

---

## [3.5.0-enterprise] - 2026-10-15

### Added
- **API Authentication & IDOR Protection**:
  - Implemented `@require_auth` and `@require_resource_ownership` decorators with JWT token validation and configurable `AUTH_REQUIRED` mode.
  - Added access control protection across `/api/graph/*`, `/api/report/*`, `/api/simulation/*`, and `/api/research/*`.
  - Added comprehensive test suite `backend/tests/test_auth.py` for token verification, expiration, and IDOR validation.
- **Infrastructure Hardening & Security Headers**:
  - Configured dedicated non-privileged user `appuser` (UID 10001) in Dockerfile to prevent container privilege escalation.
  - Injected standard HTTP security headers (`Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection`, `Strict-Transport-Security`).
  - Enforced CORS origin filtering via `ALLOWED_CORS_ORIGINS`.
  - Restricted internal database ports (Neo4j: 7474, 7687; SearXNG: 8080) to localhost (`127.0.0.1`) binding in `docker-compose.yml`.
- **Full Security Audit Report (`SECURITY_AUDIT_REPORT.md`)**:
  - Complete security audit documentation in Indonesian detailing findings, CVSS ratings, patch verification, and ongoing hardening guidelines.

### Security
- **DOM XSS Sanitization in Markdown Rendering**:
  - Sanitized raw HTML entities (`&`, `<`, `>`, `"`, `'`) in frontend `renderMarkdown` (`Step4Report.vue` and `Step5Interaction.vue`) prior to parsing, preventing script injection through simulated agent responses.
- **Dependency Hardening & CVE Patching**:
  - Upgraded Python backend packages via `uv.lock` and `pyproject.toml` to patch vulnerabilities.
  - Hardened frontend dependencies via `package-lock.json` and `npm audit`.

---

## [3.4.0-enterprise] - 2026-10-15

### Added
- **Epistemic Protocol & Anti-Hallucination Guardrails**:
  - Implemented epistemic pre-tool and post-tool audit hooks (`.claude/hooks/block-blind-installs.sh`, `epistemic-audit.sh`, `verify-after-edit.sh`) to prevent hallucinated packages, unsanctioned tool invocations, and blind writes.
  - Hardened subagent prompts across all swarms with explicit evidence-grounding constraints, anti-hallucination verification, and strict citation rules.
  - Enforced domain whitelist validation and anti-hallucination source verification in web research service (`backend/app/services/web_research_service.py`).
  - Added hallucination mitigation checks in report generation agent (`backend/app/agents/report_agent.py`).
- **Interactive Stitch UI Prototypes Suite (`stitch-prototypes/`, `frontend/public/stitch/`)**:
  - Created high-fidelity enterprise UI prototypes hub via Google Stitch with full interactive previews.
  - Included 10 comprehensive workflow screens: Step 0 (SearXNG Deep Grounding), Step 1 (FalkorDB / Graphiti Knowledge Graph), Step 2 (Graph-Driven Persona Generation), Step 3 (Simulation Orchestrator & Live Feed), Step 4 (Multi-Agent Swarm Interviews), Step 5 (Epistemic Decision Report), Epistemic Audit Dashboard, Swarm Topology Visualizer, Historical Graph Temporal Explorer, and System Health Monitor.
- **Automated GitHub Security & Vulnerability Scanning**:
  - **GitHub CodeQL SAST (`.github/workflows/codeql.yml`)**: Semantic static application security testing for Python and JavaScript/TypeScript on pushes, pull requests, and weekly schedules.
  - **GitHub Dependabot (`.github/dependabot.yml`)**: Continuous automated vulnerability monitoring and automated security PRs across Python (`backend`), Node.js (`frontend` and root), and GitHub Actions.
  - **Security & Vulnerability Audit CI (`.github/workflows/security-scan.yml`)**: Automated CI pipeline featuring `pip-audit`, `npm audit`, Bandit AST security analysis, Gitleaks secret leak detection, and Trivy filesystem/container vulnerability scanner.
  - **Security Policy (`SECURITY.md`)**: Formal security reporting guidelines, supported version matrix, and private vulnerability reporting workflow.

### Fixed
- Fixed critical command injection vulnerability in `shell-quote` root dependency.
- Fixed 6 frontend npm package vulnerabilities via `npm audit fix`.
- Fixed MCP server test suite assertion robustness against existing database state in `backend/tests/test_v31_core.py`.

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
