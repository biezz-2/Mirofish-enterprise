# PlatformSpec Schema v1.0 — Shared Reference

All `platforms/*.yaml` files MUST conform to this schema. This is the canonical
contract consumed by `mirofish.core.spec` (Pydantic models) and `mirofish.core.validate`.

## Top-level structure

```yaml
spec_version: "1.0"
platform_id: <snake_case>          # x | threads | instagram | facebook | linkedin
                                   # tiktok | youtube | telegram | bluesky | mastodon
                                   # whatsapp  (x & whatsapp exemplars in paper App. B)
display_name: <string>
archetype: public_ranked_feed | private_push_feed | private_ranked_feed | chronological
privacy_tier: public | semi_public | private
delivery_mode: pull | push          # pull = feed materialization; push = write-time fan-out
graph_visibility: public | private
temporal_model: round_based | event_driven
encryption: none | e2e | partial
timezone_anchor: UTC
```

## entities

List of entity types. Each:

```yaml
- entity_type: <Name>
  primary_key: [field, ...]
  attributes:
    <field>: {type: string|integer|float|boolean|enum|array|object,
              pattern?: string, unique?: bool, max_length?: int,
              min?: number, nullable?: bool, default?: any,
              enum?: [...], items?: {...}, ref?: <Entity.field>}
```

## relations

```yaml
- relation_type: <snake_case>
  from: <EntityType>
  to: <EntityType>
  cardinality: one_to_one | one_to_many | many_to_many
  semantics: <behavior class, e.g. directed_follow_graph | hard_exclusion |
              visibility_gate | bidirectional_opt_in | membership>
  transitive: bool
  symmetric_effect: bool
  attributes: {<optional edge attrs>}
```

## actions

```yaml
- action_id: <snake_case>
  actor: <EntityType>
  target: <EntityType | [list] | null>
  verb: <consume|react|amplify|create|relational>   # nested-logit group
  preconditions: {<predicate>: value, ...}          # evaluated before legality
  effects: {creates?: <Entity{...}>, increments?: <Counter>, updates?: <field>,
            queues_moderation?: bool, feeds_scorer_signal?: bool}
  visibility: <scope string>                        # output visibility
  cost: <int>                                       # token/compute cost weight
```

## feed

```yaml
feed:
  kind: ranked | chronological | hybrid | push | discover
  retrieval:                        # ranked/hybrid only
    - source: <in_network|candidate_pool|trending|federated_local|...>
      quota_ratio: <float>
  signal_schema:                    # canonical 10 signal families
    - {name: <recency|engagement_count|attention_dwell|shares_private|
              author_affinity|topic_graph|negative_feedback|popularity_velocity|
              content_type_prior|quality_satisfaction|...custom>,
       type: <type>, weight?: <float>, provenance?: documented|inferred|prior}
  scorer:
    plugin: <plugin:name>           # chronological | engagement_ranked |
                                    # push_inbox | bluesky_discover | custom
    params: {<tunable weights>}
  params: {<platform feed params, e.g. weights w_{p,k}>}
```

For `delivery_mode: push`, `feed.kind: push` and NO scorer plugin is allowed;
instead specify `delivery_model.inbox_rules` (ordering, pins, mutes, unread counts).

## content_constraints

Hard limits enforced at action-precondition time:

```yaml
content_constraints:
  max_length_chars: <int>           # note: bytes vs chars vs graphemes — say which
  length_unit: chars | utf8_bytes | graphemes
  media_policy: <string>
  max_media_per_post: <int>
  edit_window_seconds: <int|null>
  <other platform limits>
```

## privacy / visibility_model

```yaml
visibility_model:
  default_scope: <broadcast|followers|mutuals|conversation|group_members|contacts_only>
  rules:
    - {scope: <name>, predicate: <description>, grants: <relation required>}
```

## moderation

```yaml
moderation:
  tiers: [{tier: int, name: str, action: allow|label_only|downrank|remove_and_sanction|...}]
  enforcement_points: [<action_ids>]
  metadata_only: bool               # true for E2EE platforms
  <platform specifics>
```

## demographics / data_availability

```yaml
demographics: {mau: <string>, notes: <string>}
data_availability:
  tier: 1|2|3|4                     # 1=fully observable ... 4=near-blind
  sources: [<dataset names/URLs>]
```

## signal_schema conventions

The ten canonical signal families (from paper §6.1):
`recency`, `engagement_count`, `attention_dwell`, `shares_private`,
`author_affinity`, `topic_graph`, `negative_feedback`, `popularity_velocity`,
`content_type_prior`, `quality_satisfaction`.
Use `observation_mask` semantics: signals a platform does not expose are
omitted from `signal_schema` (not zero-weighted).

## Provenance discipline

Every weight/parameter cell should carry `provenance: documented|inferred|prior`
in comments or a `provenance` field. NEVER present inferred/priors as documented
production values.
