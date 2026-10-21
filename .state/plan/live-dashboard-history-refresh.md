# Plan — live-dashboard-history-refresh

## Objective
Backup the current workspace, implement end-to-end visibility for project `proj_5e996d7cdf4b`, graph `mirofish_7955644bda70404f`, simulation `sim_b839625f8ac2`, task `089e6d2d-508c-46c1-ac50-7c65441e6d5c`, expose all available simulation history and realtime monitoring in the dashboard, then restart only the identified application services and verify them.

## Scope
- Read-only backup before edits.
- Backend history/status endpoints and frontend dashboard rendering/polling.
- Preserve active simulation and worker state; no simulation rerun.
- Restart application processes after validation; do not restart unrelated MCP services.

## Phases
1. Inventory and backup: archive workspace changes and active state; acceptance: backup path and hashes recorded.
2. Backend contract: inspect existing APIs and add minimum history/realtime data path; acceptance: tests cover IDs, missing state, history ordering, and truthful unavailable state.
3. Dashboard: render all available state/history/platform data with realtime polling; acceptance: frontend build and component tests pass.
4. Validation: full backend/frontend checks, state hash unchanged, independent review.
5. Restart and smoke test: restart only app services, verify HTTP/UI/API; acceptance: URLs respond and no worker mutation.

## Risks
- Restart may interrupt an application process; mitigate by identifying PIDs and preserving state first.
- History may be incomplete in current state; display source/availability instead of inventing records.
- User-supplied task ID is not currently present in state; preserve it as requested metadata only unless backend confirms it.
