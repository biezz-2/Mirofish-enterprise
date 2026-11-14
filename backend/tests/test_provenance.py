"""Tests for mirofish.core.provenance — ResponseCache, Watermark, RunManifest."""

import pytest


def _mod():
    return pytest.importorskip("mirofish.core.provenance", reason="mirofish.core.provenance not implemented yet")


def test_response_cache_hit_miss(tmp_path):
    mod = _mod()
    cls = getattr(mod, "ResponseCache", None) or getattr(mod, "Cache", None)
    if cls is None:
        pytest.skip("ResponseCache not implemented")
    cache = cls(":memory:")
    # Real API: put(key, response) / get(key) — response is a string.
    key = cache.key_for("m", "sys", "user prompt") if hasattr(cache, "key_for") else "k1"
    cache.put(key, '{"text": "hello"}')
    assert cache.get(key) == '{"text": "hello"}'
    assert cache.get("nonexistent-key") is None
    # Content-addressed: same inputs → same key → hit.
    if hasattr(cache, "key_for"):
        k2 = cache.key_for("m", "sys", "user prompt")
        assert k2 == key


def test_watermark_embed_extract_roundtrip():
    mod = _mod()
    cls = getattr(mod, "Watermark", None)
    if cls is not None and hasattr(cls, "embed"):
        marked = cls.embed("synthetic post text", run_id="run-42")
        assert cls.extract(marked) == "run-42"
        assert cls.extract("plain text") is None
        # Visible label roundtrip too.
        labeled = cls.label("synthetic post text", run_id="run-42")
        assert cls.extract_label(labeled) == "run-42"
        return
    embed = getattr(mod, "embed_watermark", None)
    extract = getattr(mod, "extract_watermark", None)
    if embed is None or extract is None:
        pytest.skip("watermark embed/extract not implemented")
    marked = embed("synthetic post text", run_id="run-42")
    recovered = extract(marked)
    assert "run-42" in str(recovered)


def test_run_manifest_json_roundtrip():
    mod = _mod()
    cls = getattr(mod, "RunManifest", None)
    if cls is None:
        pytest.skip("RunManifest not implemented")
    m = cls(run_id="r1", seed=7)
    m.spec_versions["x"] = "1.0"
    text = m.to_json() if hasattr(m, "to_json") else None
    if text is None:
        pytest.skip("RunManifest.to_json not implemented")
    back = cls.from_json(text) if hasattr(cls, "from_json") else None
    if back is None:
        pytest.skip("RunManifest.from_json not implemented")
    assert back.run_id == "r1"
    assert back.seed == 7
    assert back.spec_versions.get("x") == "1.0"
    # to_dict must be JSON-serializable.
    import json

    json.dumps(m.to_dict())
