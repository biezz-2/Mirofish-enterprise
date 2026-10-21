# Plan — Parallel embedding acceleration

## Objective
Add an optional 9Router-compatible embedding pipeline for graph building with batching, bounded parallelism, retries, hash cache, checkpoint/resume, timeout, and progress telemetry.

## Scope
- Backend embedding client and configuration.
- Integrate pre-embedding into local graph extraction without changing the LLM extraction contract.
- Add unit tests for batching, cache reuse, retry, and ordering.

## Non-scope
- Do not stop, restart, or mutate any live MiroFish job.
- Do not commit credentials or make the current production worker reload code.
- Do not replace ontology extraction with embeddings; embeddings provide reusable semantic vectors and telemetry.

## Acceptance
- Missing embedding credentials disables the optional stage safely.
- Requests use array input, bounded concurrency, timeout, exponential backoff, and no secret logging.
- Cache key includes model and chunk hash; cache survives process restarts.
- Partial failures are explicit and do not silently claim full embedding coverage.
- Existing graph build tests and Python compilation pass.

## Validation
- V1–V3: tests and security review.
- V4: current 9Router/OpenAI-compatible embedding docs checked.
- V5: concurrency, batching, bounded retries, SQLite WAL cache.
- V6: existing graph service tests/compile.
- V7–V8: diff review and docs/state update.
