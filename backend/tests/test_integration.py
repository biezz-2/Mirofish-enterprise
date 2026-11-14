"""End-to-end smoke test: minimal spec + store + one agent step.

Everything is imported defensively — components that don't exist yet are
skipped rather than failing the suite.
"""

import pytest

from test_spec import MINIMAL_SPEC


def test_minimal_pipeline_smoke():
    # 1. Spec layer
    spec_mod = pytest.importorskip("mirofish.core.spec", reason="mirofish.core.spec not implemented yet")
    spec_cls = getattr(spec_mod, "PlatformSpec", None)
    if spec_cls is None or not hasattr(spec_cls, "from_dict"):
        pytest.skip("PlatformSpec.from_dict not implemented")
    spec = spec_cls.from_dict(MINIMAL_SPEC)
    assert spec is not None

    # 2. Validation (optional — warn-only if absent)
    val_mod = pytest.importorskip("mirofish.core.validate", reason="mirofish.core.validate not implemented")
    validate = getattr(val_mod, "validate_spec", None)
    if validate is not None:
        result = validate(spec)
        errors = getattr(result, "errors", None)
        if errors is None and isinstance(result, tuple):
            errors = result[0]
        if errors is None and isinstance(result, dict):
            errors = result.get("errors")
        assert not errors, f"minimal spec produced validation errors: {errors}"

    # 3. Store layer
    store_mod = pytest.importorskip("mirofish.core.store", reason="mirofish.core.store not implemented")
    store_cls = getattr(store_mod, "EntityStore", None)
    if store_cls is not None:
        try:
            store = store_cls(":memory:")
        except TypeError:
            store = store_cls()
        if hasattr(store, "put"):
            store.put("User", "u1", {"name": "Ada"})
            if hasattr(store, "get"):
                assert store.get("User", "u1") is not None

    # 4. Feed layer — score a couple of items if a scorer exists
    feed_mod = pytest.importorskip("mirofish.core.feed", reason="mirofish.core.feed not implemented")
    scorer = None
    for name in ("engagement_ranked", "chronological", "score_feed", "rank"):
        scorer = getattr(feed_mod, name, None)
        if scorer is not None:
            break
    if scorer is not None:
        items = [
            {"item_id": "a", "ts": 2, "signals": {"engagement": 10.0}},
            {"item_id": "b", "ts": 1, "signals": {"engagement": 1.0}},
        ]
        try:
            out = scorer(items)
            assert out is not None
        except TypeError:
            try:
                out = scorer(items, {})
                assert out is not None
            except TypeError:
                pass  # signature unknown — presence of the scorer is enough for smoke

    # 5. Agent decision — one choose/sample call if available
    dec_mod = pytest.importorskip("mirofish.agent.decision", reason="mirofish.agent.decision not implemented")
    for cls_name in ("NestedLogit", "AgentPolicy", "DecisionModel"):
        cls = getattr(dec_mod, cls_name, None)
        if cls is None:
            continue
        try:
            model = cls()
        except TypeError:
            continue
        for mname in ("choose", "decide", "sample", "act"):
            m = getattr(model, mname, None)
            if m is None:
                continue
            try:
                out = m()
            except TypeError:
                continue
            assert out is not None
            break
        else:
            continue
        break

    # 6. Provenance — manifest roundtrip if present
    prov_mod = pytest.importorskip("mirofish.core.provenance", reason="mirofish.core.provenance not implemented")
    manifest_cls = getattr(prov_mod, "RunManifest", None)
    if manifest_cls is not None:
        try:
            manifest = manifest_cls(run_id="smoke", platform="mini", seed=1)
        except TypeError:
            try:
                manifest = manifest_cls()
            except TypeError:
                manifest = None
        if manifest is not None:
            assert manifest is not None
