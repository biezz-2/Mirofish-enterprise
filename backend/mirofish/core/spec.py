"""Pydantic v2 models for the PlatformSpec schema (docs/SPEC_SCHEMA.md v1.0).

Strict ``Literal`` enums are used where the schema fixes a value set;
open-ended sections use flexible ``dict``/extra-allowed models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enumerations fixed by SPEC_SCHEMA.md
# ---------------------------------------------------------------------------

Archetype = Literal["public_ranked_feed", "private_push_feed", "private_ranked_feed", "chronological"]
PrivacyTier = Literal["public", "semi_public", "private"]
# `hybrid` appears in shipped specs (e.g. instagram.yaml: pull feeds + push DMs).
DeliveryMode = Literal["pull", "push", "hybrid"]
GraphVisibility = Literal["public", "private"]
TemporalModel = Literal["round_based", "event_driven"]
Encryption = Literal["none", "e2e", "partial"]

FeedKind = Literal["ranked", "chronological", "hybrid", "push", "discover"]
ActionVerb = Literal["consume", "react", "amplify", "create", "relational"]
# Schema lists one_to_one|one_to_many|many_to_many; many_to_one occurs in specs.
Cardinality = Literal["one_to_one", "one_to_many", "many_to_one", "many_to_many"]
LengthUnit = Literal["chars", "utf8_bytes", "graphemes"]
Provenance = Literal["documented", "inferred", "prior"]


class _Open(BaseModel):
    """Base for open-ended schema sections: unknown keys are preserved."""

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class AttributeSpec(_Open):
    """A single attribute declaration inside an entity type."""

    type: str  # string|integer|float|boolean|enum|array|object|timestamp|...
    pattern: str | None = None
    unique: bool | None = None
    max_length: int | None = None
    min: float | None = None
    max: float | None = None
    nullable: bool | None = None
    default: Any = None
    enum: list[Any] | None = None
    items: AttributeSpec | dict[str, Any] | None = None  # for type: array
    ref: str | None = None  # "EntityType.field"


class EntityType(_Open):
    entity_type: str
    primary_key: list[str] = Field(default_factory=list)
    # Values are AttributeSpec dicts; bare strings are tolerated for inline
    # notes some specs place directly under `attributes:`.
    attributes: dict[str, AttributeSpec | str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


class RelationSpec(_Open):
    relation_type: str
    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    cardinality: Cardinality
    semantics: str | None = None
    transitive: bool = False
    symmetric_effect: bool = False
    attributes: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


class ActionEffects(_Open):
    """Open-ended effects block (creates/increments/updates/...)."""

    creates: dict[str, Any] | None = None
    increments: dict[str, Any] | None = None
    updates: dict[str, Any] | str | None = None
    queues_moderation: bool | None = None
    feeds_scorer_signal: bool | None = None


class ActionSpec(_Open):
    action_id: str
    actor: str
    target: str | list[str] | None = None
    verb: ActionVerb
    # Schema shows a predicate->value dict; some specs use a plain list of
    # predicate names. Both are accepted.
    preconditions: dict[str, Any] | list[Any] = Field(default_factory=dict)
    effects: ActionEffects | dict[str, Any] = Field(default_factory=dict)
    visibility: str | None = None
    cost: int = 0


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------


class FeedSource(_Open):
    source: str
    quota_ratio: float | None = None


class SignalSpec(_Open):
    """One entry in feed.signal_schema (canonical 10 families + customs)."""

    name: str
    type: str | None = None  # float|integer|boolean|object|timestamp|...
    weight: float | None = None
    provenance: Provenance | None = None


class ScorerSpec(_Open):
    plugin: str | None = None  # e.g. chronological | engagement_ranked | custom:phoenix
    params: dict[str, Any] = Field(default_factory=dict)


class DeliveryModel(_Open):
    """Push-mode delivery semantics (inbox rules, fan-out)."""

    mode: str | None = None
    inbox_rules: dict[str, Any] | None = None


class FeedSpec(_Open):
    kind: FeedKind
    retrieval: list[FeedSource] | None = None
    signal_schema: list[SignalSpec] = Field(default_factory=list)
    scorer: ScorerSpec | dict[str, Any] | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    delivery_model: DeliveryModel | dict[str, Any] | None = None
    # Open extensions used by real specs: instagram `surfaces`, telegram `discover`.


# ---------------------------------------------------------------------------
# Content / visibility / moderation / demographics
# ---------------------------------------------------------------------------


class ContentConstraints(_Open):
    max_length_chars: int | None = None
    length_unit: LengthUnit | None = None
    media_policy: str | None = None
    max_media_per_post: int | None = None
    edit_window_seconds: int | None = None


class VisibilityRule(_Open):
    scope: str
    predicate: str | None = None
    grants: str | None = None
    effect: str | None = None


class VisibilityModel(_Open):
    default_scope: str
    rules: list[VisibilityRule] = Field(default_factory=list)


class ModerationTier(_Open):
    tier: int
    name: str | None = None
    action: str | None = None  # allow|label_only|downrank|remove_and_sanction|throttle|...


class ModerationSpec(_Open):
    tiers: list[ModerationTier] = Field(default_factory=list)
    enforcement_points: list[str] = Field(default_factory=list)
    metadata_only: bool = False


class Demographics(_Open):
    mau: str | None = None
    notes: str | None = None


class DataAvailability(_Open):
    tier: Literal[1, 2, 3, 4]
    sources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level PlatformSpec
# ---------------------------------------------------------------------------


class PlatformSpec(_Open):
    """Top-level declarative description of one social platform."""

    spec_version: str = "1.0"
    platform_id: str
    display_name: str
    archetype: Archetype
    privacy_tier: PrivacyTier
    delivery_mode: DeliveryMode
    graph_visibility: GraphVisibility
    temporal_model: TemporalModel
    encryption: Encryption = "none"
    timezone_anchor: str = "UTC"

    entities: list[EntityType] = Field(default_factory=list)
    relations: list[RelationSpec] = Field(default_factory=list)
    actions: list[ActionSpec] = Field(default_factory=list)
    feed: FeedSpec | None = None
    content_constraints: ContentConstraints | None = None
    visibility_model: VisibilityModel | None = None
    moderation: ModerationSpec | None = None
    demographics: Demographics | None = None
    data_availability: DataAvailability | None = None

    # -- constructors -------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlatformSpec:
        return cls.model_validate(data)

    @classmethod
    def from_yaml(cls, path: str | Path) -> PlatformSpec:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a YAML mapping at top level")
        return cls.from_dict(data)
