# Plan — Mirofish Enterprise: Analysis of All Projects + GitHub URL Migration

- Project ID: `mirofish-github-url-migration`
- Owner agent: HERMES
- Date: 2026-10-21
- Target URL: `https://github.com/biezz-2/Mirofish-enterprise`
- Legacy upstream: `https://github.com/666ghj/MiroFish`

## Objective & success criteria

1. Every project in the Mirofish Enterprise workspace is analysed (MCP `list_projects` roster + per-project report/ontology).
2. Every *repository-target* GitHub URL in the four local trees points to `https://github.com/biezz-2/Mirofish-enterprise`.
3. Third-party GitHub URLs, GitHub Pages demo links, dependency sponsor links, Trendshift badge, and legal attribution are NOT rewritten.
4. Star-history metadata + generated SVG are consistent (`scripts/star_history.py check` exits 0 in every tree).
5. Test suites pass; any pre-existing failure is proven pre-existing (clean `HEAD` worktree comparison), not introduced by the URL migration.

## Scope / non-scope

- IN: repository-target URL slug `666ghj/MiroFish` → `biezz-2/Mirofish-enterprise` across backend, docs, frontend, scripts, GitHub metadata, workflow, tests; star-history regeneration; analysis of MCP projects.
- OUT: legal attribution in `NOTICE`, `README*.md` "Upstream MiroFish" credit lines, `CHANGELOG.md` history; `666ghj/BettaFish` upstream port credits; `camel-ai/oasis`; sponsor URLs; Trendshift badge; `666ghj.github.io/mirofish-demo` live demo link (that repo belongs to the upstream owner).

## Phases

| Phase | Goal | Deliverables | Acceptance criteria | Risk | Depends on |
|---|---|---|---|---|---|
| p01 | Analyse all Mirofish projects | MCP roster + per-project insight table | 14 projects triaged with status/credibility/ontology size/insight | low | — |
| p02 | Migrate repo-target URLs (main repo) | 11 files patched + 2 SVGs regenerated | `git grep 666ghj/MiroFish` returns only attribution lines | med | — |
| p03 | Migrate Next15 + extra clone | same file set + workflow actor condition | star-history check exit 0 in both trees | med | p02 |
| p04 | Validate (V1–V8) | validation report, findings | star-history check 0/0/0, targeted tests green, full suite delta explained | med | p02,p03 |

## Validation plan

- V1 spec completeness: per-file slug audit on 4 trees (tracked + untracked).
- V2 logic: `pytest tests/test_local_star_history.py tests/test_local_star_count_fetch.py`; full `pytest tests`; clean-HEAD worktree comparison for failures.
- V3 security: no secret/credential introduced by the edits; workflow origin allow-list reviewed.
- V4 standards: workflow YAML validity, `star_history.py` CLI contract re-checked against repo usage.
- V5 performance: n/a (metadata-only change).
- V6 regression: clean detached worktree at `HEAD` proves pre-existing failures.
- V7 code quality: provider-name literals updated together with the router rename.
- V8 handoff: this plan, the validation report, and the session log entry.

## Board plan

- `project-mirofish-github-url-migration` (PROJECT) — phases p01–p04 as cards.
- `validation-mirofish-github-url-migration` (VALIDATION) — created when p04 hits IMPLEMENTED.
- Coordination: PHASE boards DEPENDS_ON `project-mirofish-github-url-migration`; VALIDATION board VALIDATES the PHASE board.

## Cron plan

- `audit:phase-regression` (every 24h × 7 days) — re-run V2+V6 on the URL slug + star-history check.
- `audit:project-daily` (every 24h) — board rollup to owner chat.

## Risk register

| Risk | Mitigation | Trigger |
|---|---|---|
| Legal attribution rewritten by accident | Explicit allow-list of attribution lines; verified by grep output | any `NOTICE`/`README` upstream line disappears |
| Star-history SVG desync after history.json edit | Regenerate via `star_history._write_outputs` + `star_history.py check` | `check` non-zero |
| Full-suite failure blamed on this change | Clean detached worktree at `HEAD` reproduces or refutes | any failing test |
| Workflow blocks pushes after actor rename | `triggering_actor` widened to owner handle, hard-coded actor id removed | workflow `if:` mismatch |
