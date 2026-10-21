# Plan — MiroFish multi-platform simulation

## Objective
Read the supplied Notion project documentation, reconcile the simulation contract, remove false mock-completion behavior, and implement one canonical seven-platform simulation configuration for Instagram, LinkedIn, Reddit, Threads, TikTok, X, and YouTube without interrupting active workers.

## Success criteria
- Notion root and accessible descendants are inventoried with source IDs and content evidence.
- Seven platform names/parameters are defined in one canonical contract.
- Create/prepare/run/report paths preserve the same simulation_id and project_id.
- MCP never reports mock data as `completed`; unavailable data is explicit.
- Per-platform status and metrics are persisted and exposed.
- Existing two-platform behavior remains compatible where explicitly requested.
- Unit/integration checks pass; no active worker is stopped or restarted.

## Scope
Backend simulation configuration, state/report schemas, MCP fallback semantics, platform orchestration, tests, and documentation.

## Non-scope
No production deployment, destructive database migration, credential changes, or stopping/restarting active graph/simulation workers without explicit approval.

## Phases
1. Research and contract inventory: Notion crawl, repository audit, current runtime evidence.
2. Design and implementation: canonical seven-platform config, lifecycle propagation, truthful MCP reporting, persistence.
3. Validation: tests, security/performance/regression review, documentation, controlled local smoke test.
4. Deployment remains separate and requires owner approval after validation.

## Risks
- Existing workers may assume two flags; mitigate with backward-compatible defaults.
- Platform metrics may be synthetic calibration values; label provenance and never present them as observed results.
- Notion access may expose incomplete pages; record pagination/truncation.
- Production API state may differ from checkout; use local tests and read-only smoke checks first.
