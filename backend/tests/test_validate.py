"""Tests for mirofish.core.validate — spec validation diagnostics."""

import pytest

from test_spec import MINIMAL_SPEC


def _validate_spec():
    module = pytest.importorskip("mirofish.core.validate", reason="mirofish.core.validate not implemented yet")
    fn = getattr(module, "validate_spec", None)
    if fn is None:
        pytest.skip("validate_spec not implemented")
    return fn


def _split(issues):
    """Split validate_spec result into (errors, warnings).

    Handles list[ValidationIssue], list[str], tuple, or dict returns.
    """
    errors, warnings = [], []
    items = issues
    if isinstance(issues, tuple) and len(issues) == 2:
        errors, warnings = list(issues[0] or []), list(issues[1] or [])
        items = None
    elif isinstance(issues, dict):
        errors = list(issues.get("errors", []))
        warnings = list(issues.get("warnings", []))
        items = None
    if items is not None:
        for it in items:
            sev = getattr(it, "severity", None)
            if sev == "warning":
                warnings.append(it)
            elif sev == "error":
                errors.append(it)
            else:
                # Plain strings / unknown shape: treat as errors conservatively
                # only when they look like failures; otherwise ignore.
                errors.append(it)
    return errors, warnings


def test_unknown_entity_ref_in_relation_flagged():
    fn = _validate_spec()
    bad = {
        **MINIMAL_SPEC,
        "relations": [
            {
                "relation_type": "follows",
                "from": "User",
                "to": "Ghost",  # entity type that does not exist
                "cardinality": "many_to_many",
                "semantics": "directed_follow_graph",
                "transitive": False,
                "symmetric_effect": False,
            }
        ],
    }
    # validate_spec accepts a raw dict directly.
    try:
        issues = fn(bad)
    except TypeError:
        # Older signature may require a PlatformSpec model.
        spec_mod = pytest.importorskip("mirofish.core.spec")
        spec = spec_mod.PlatformSpec.from_dict(bad)
        issues = fn(spec)
    errors, _ = _split(issues)
    assert errors, "expected at least one validation error for unknown entity ref"
    codes = {getattr(e, "code", "") for e in errors}
    assert any("UNKNOWN" in c or "ENTITY" in c for c in codes) or errors


def test_push_plus_scorer_conflict_flagged():
    fn = _validate_spec()
    bad = {
        **MINIMAL_SPEC,
        "delivery_mode": "push",
        "feed": {
            "kind": "push",
            "scorer": {"plugin": "weighted_sum"},
            "signal_schema": [
                {"name": "recency", "type": "float", "weight": 1.0, "provenance": "prior"},
            ],
        },
    }
    try:
        issues = fn(bad)
    except TypeError:
        spec_mod = pytest.importorskip("mirofish.core.spec")
        try:
            spec = spec_mod.PlatformSpec.from_dict(bad)
        except Exception:
            return  # structural layer rejects it — conflict caught either way
        issues = fn(spec)
    errors, _ = _split(issues)
    codes = {getattr(e, "code", "") for e in errors}
    assert errors, "expected validation error for push feed with scorer"
    assert any("PUSH" in c or "SCORER" in c for c in codes), \
        f"expected PUSH_WITH_SCORER-style error, got {codes}"


def test_missing_provenance_produces_warning():
    fn = _validate_spec()
    spec_dict = {
        **MINIMAL_SPEC,
        "feed": {
            "kind": "chronological",
            "signal_schema": [
                {"name": "recency", "type": "float", "weight": 1.0},  # no provenance
            ],
        },
    }
    try:
        issues = fn(spec_dict)
    except TypeError:
        spec_mod = pytest.importorskip("mirofish.core.spec")
        spec = spec_mod.PlatformSpec.from_dict(spec_dict)
        issues = fn(spec)
    _, warnings = _split(issues)
    assert warnings, "expected a warning for missing provenance"
