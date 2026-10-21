# Plan — Seven-platform direct prepared-state upgrade

## Objective
Safely migrate ready simulation `sim_b839625f8ac2` to the canonical Instagram, LinkedIn, Reddit, Threads, TikTok, Twitter, and YouTube set without preparation, graph extraction, LLM calls, or worker/simulation control.

## Success criteria
- Existing generated Reddit and Twitter profiles remain intact.
- Five JSON profile artifacts are copied from the legitimate existing Reddit generated profile data.
- State and configuration list exactly seven canonical platforms and coherent per-platform status/configuration.
- `status=ready`, `profiles_count=478`, `current_round=0`, and generated flags remain unchanged.
- A temporary-copy migration and the backend suite pass before active-state application.

## Scope
A reusable migration helper, its tests, state/config/artifact migration, backup, targeted/full backend validation.

## Non-scope
No graph extraction, profile/config LLM generation, frontend change, process start/stop/restart, or simulated results.

## Phases
1. Test migration behavior and implement guarded artifact/state/config transformation. Risk: data integrity; guard requires ready/generation/artifacts/count.
2. Validate a copied temporary simulation, back up active artifacts, then run the guarded migration. Risk: active state; atomic JSON replacement and no process APIs.
3. Run targeted/full regression tests and gate review. V1–V8 with Python stdlib/shutil documentation checked for copy semantics.

## Risk register
- Partial write: sibling temporary JSON then `os.replace`.
- Wrong source profile count: verify Reddit JSON list matches persisted count.
- Active/running migration: reject any non-`ready` status.
- Profile fabrication: copy already-generated Reddit profile records only; no generation or result fields added.
