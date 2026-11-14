"""Tests for mirofish.core.spec — PlatformSpec construction/validation."""

import pytest

VALID_VERBS = {"consume", "react", "amplify", "create", "relational"}

MINIMAL_SPEC = {
    "spec_version": "1.0",
    "platform_id": "mini",
    "display_name": "Mini Platform",
    "archetype": "chronological",
    "privacy_tier": "public",
    "delivery_mode": "pull",
    "graph_visibility": "public",
    "temporal_model": "round_based",
    "encryption": "none",
    "entities": [
        {
            "entity_type": "User",
            "primary_key": ["user_id"],
            "attributes": {
                "user_id": {"type": "string", "unique": True},
            },
        },
        {
            "entity_type": "Post",
            "primary_key": ["post_id"],
            "attributes": {
                "post_id": {"type": "string", "unique": True},
                "author": {"type": "string", "ref": "User.user_id"},
            },
        },
    ],
    "relations": [
        {
            "relation_type": "follows",
            "from": "User",
            "to": "User",
            "cardinality": "many_to_many",
            "semantics": "directed_follow_graph",
            "transitive": False,
            "symmetric_effect": False,
        }
    ],
    "actions": [
        {
            "action_id": "create_post",
            "actor": "User",
            "target": "Post",
            "verb": "create",
            "preconditions": {},
            "effects": {"creates": {"Post": {}}, "feeds_scorer_signal": True},
        }
    ],
    "feed": {
        "kind": "chronological",
        "signal_schema": [
            {"name": "recency", "type": "float", "weight": 1.0, "provenance": "prior"},
        ],
    },
}


def _spec_cls():
    module = pytest.importorskip("mirofish.core.spec", reason="mirofish.core.spec not implemented yet")
    cls = getattr(module, "PlatformSpec", None)
    if cls is None:
        pytest.skip("PlatformSpec not implemented in mirofish.core.spec")
    if not hasattr(cls, "from_dict"):
        pytest.skip("PlatformSpec.from_dict not implemented")
    return cls


def test_minimal_spec_from_dict_valid():
    cls = _spec_cls()
    spec = cls.from_dict(MINIMAL_SPEC)
    assert spec is not None
    assert getattr(spec, "platform_id", "mini") == "mini"


def test_bad_verb_rejected():
    cls = _spec_cls()
    bad = {**MINIMAL_SPEC}
    bad["actions"] = [
        {
            "action_id": "hack",
            "actor": "User",
            "target": "Post",
            "verb": "teleport",  # not in {consume, react, amplify, create, relational}
            "preconditions": {},
            "effects": {},
        }
    ]
    with pytest.raises(Exception):
        cls.from_dict(bad)


def test_push_feed_with_scorer_rejected():
    cls = _spec_cls()
    bad = {**MINIMAL_SPEC}
    bad["delivery_mode"] = "push"
    bad["feed"] = {
        "kind": "push",
        "scorer": {"plugin": "weighted_sum"},
        "signal_schema": [
            {"name": "recency", "type": "float", "weight": 1.0, "provenance": "prior"},
        ],
    }
    # The conflict may be caught structurally (Pydantic model_validator) or
    # semantically (validate_spec) — either satisfies the requirement.
    try:
        spec = cls.from_dict(bad)
    except Exception:
        return  # structural rejection is a valid outcome
    val_mod = pytest.importorskip("mirofish.core.validate", reason="mirofish.core.validate not implemented")
    validate = getattr(val_mod, "validate_spec", None)
    if validate is None:
        pytest.skip("validate_spec not implemented")
    # Pass the raw dict: model_dump() drops the 'from'/'to' aliases.
    issues = validate(bad)
    severities = {getattr(i, "severity", None) for i in issues}
    codes = {getattr(i, "code", "") for i in issues}
    assert "error" in severities or any("PUSH" in c or "SCORER" in c for c in codes), \
        f"push+scorer must produce a validation error, got {issues!r}"
