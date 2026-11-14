# MiroFish Architecture

Multi-platform social simulation. A declarative `PlatformSpec` (see
`docs/SPEC_SCHEMA.md`, `platforms/*.yaml`) defines entities, relations, actions,
feed model, and moderation policy for one platform. A scenario YAML
(`examples/*.yaml`) binds agents, RNG, ticks, seeds, and observation probes to
a spec. The runtime executes agent decision rounds against the spec; feeds are
either materialized per user at read time (pull) or fanned out at write time
(push).

## Services

1. **Environment Server** — owns platform state: entities, relations, counters.
   Applies action effects (`creates`, `increments`, `queues_moderation`,
   `visibility`), enforces `preconditions` and `content_constraints`, resolves
   visibility scopes. Stateless w.r.t. agent cognition; all legality lives here.
2. **Time Engine** — simulation clock. Advances ticks, emits `tick_start` /
   `tick_end`, schedules seeds (news injections, ban waves) at fixed ticks,
   maintains warmup and observation windows. `temporal_model` in the spec
   selects round-based vs event-driven scheduling.
3. **Recsys Workers** — feed computation. For `delivery_mode: pull`, materialize
   each consuming agent's feed at consume time: retrieval quotas
   (`in_network`/`candidate_pool`/`trending`), signal evaluation against
   `signal_schema`, scorer plugin ranking (`custom:phoenix`,
   `bluesky_discover`, `chronological`, …), and diversity reranking. For
   `kind: chronological`, ordering is pure `created_at` — no scorer.
4. **Inferencer Pool** — LLM-backed cognition. Given an agent's persona
   (archetype action propensities, interest topics) and the observations it is
   legally allowed to see, the pool samples the agent's action for the tick.
   Runs behind an interface so math-only backends (propensity tables, nested
   logit) can substitute for LLMs in calibration runs.
5. **State Store** — persistence and replay. Snapshots per tick, action/event
   log, feed materialization traces, moderation queue records. Seeds and RNG
   streams are recorded so any run is bit-reproducible.

## Data flow per tick

```
Time Engine ──tick_start──▶ Inferencer Pool (agents sample actions)
        │                          │
        │                          ▼
        │                   Environment Server
        │                   (preconditions → legality; apply effects;
        │                    push? fan-out to recipient inboxes now)
        │                          │
        ▼                          ▼
   seeds due at tick         State Store (commit tick)
        │                          │
        └──── notifications ────────┘
                                   │
                    agents with consume actions
                                   ▼
                          Recsys Workers (pull only)
                    materialize per-user feed → agent
```

Push platforms skip Recsys Workers entirely: `feed.kind: push` means inbox
ordering rules (`pinned > unread > recency`) evaluated at write time.

## Math layer vs LLM layer

- **Math layer (deterministic, cheap, always on):** precondition evaluation,
  visibility gating, counter increments, feed retrieval quotas, signal
  computation, scorer ranking, inbox ordering, RNG draws, moderation
  metadata heuristics. Everything reproducible must live here.
- **LLM layer (stochastic, expensive):** agent action selection and content
  generation (post text, reply intent). The LLM sees only what the visibility
  model exposes to that agent; it never sees feed internals, other agents'
  hidden state, or E2EE plaintext (which is modeled as ciphertext refs).
- Boundary rule: LLM output is an *action proposal*; the Environment Server
  re-validates all preconditions before commit. LLMs cannot bypass legality.

## File map

```
mirofish/
├── core/            # spec models, validation, environment, time engine (planned)
│   ├── spec.py      #   pydantic models for PlatformSpec/ScenarioSpec
│   ├── validate.py  #   CLI: python3 -m mirofish validate <spec.yaml>
│   ├── env.py       #   Environment Server
│   └── clock.py     #   Time Engine
├── recsys/          # feed materialization: retrieval, signals, scorers (planned)
├── agent/           # persona/archetype defs, inferencer pool interface (planned)
├── state/           # State Store: snapshots, event log, replay (planned)
├── platforms/       # PlatformSpec YAMLs (x, threads, instagram, tiktok,
│                    #   linkedin, whatsapp, bluesky[parallel])
├── examples/        # ScenarioSpec YAMLs (bluesky_micro, whatsapp_group)
├── calibration/     # weight calibration harness vs observed data (planned)
├── tests/           # pytest suite
└── docs/
    ├── SPEC_SCHEMA.md   # canonical PlatformSpec contract
    └── ARCHITECTURE.md  # this file
```

## Determinism & provenance

All randomness flows through named RNG streams seeded per scenario
(`rng.streams`); default stream covers agent decisions, feed sampling, and
moderation jitter. Every feed weight/parameter carries
`provenance: documented | inferred | prior` — never present inferred or prior
values as measured production numbers.
