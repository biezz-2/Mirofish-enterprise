"""Tests for mirofish.agent.decision — nested logit, DDM, prospect theory, copula.

Written against the real API but kept tolerant: missing pieces skip cleanly.
"""

import random

import pytest


def _dec():
    return pytest.importorskip("mirofish.agent.decision", reason="mirofish.agent.decision not implemented yet")


def _platform_spec():
    return {
        "platform_id": "mini",
        "actions": [
            {"action_id": "scroll", "verb": "consume"},
            {"action_id": "view", "verb": "consume"},
            {"action_id": "like", "verb": "react"},
            {"action_id": "share", "verb": "amplify"},
            {"action_id": "post", "verb": "create"},
            {"action_id": "follow", "verb": "relational"},
        ],
    }


def test_nested_logit_returns_valid_group_action():
    mod = _dec()
    cls = getattr(mod, "NestedLogit", None)
    if cls is None:
        pytest.skip("NestedLogit not implemented")
    model = cls(rng=random.Random(0))
    group, action = model.choose({"f0": 0.5, "f1": 0.2}, _platform_spec())
    valid = {
        "consume": {"scroll", "view"},
        "react": {"like"},
        "amplify": {"share"},
        "create": {"post"},
        "relational": {"follow"},
    }
    assert group in valid
    assert action in valid[group]


def test_ddm_dwell_positive():
    mod = _dec()
    cls = getattr(mod, "DriftDiffusion", None)
    if cls is None:
        pytest.skip("DriftDiffusion not implemented")
    for simulate in (True, False):
        ddm = cls(rng=random.Random(1), simulate=simulate)
        dwell, decision = ddm.dwell_and_decide(content_fit=0.8, platform_threshold=0.2)
        assert float(dwell) > 0
        assert decision in (-1, 1)


def test_prospect_vx_loss_aversion_asymmetry():
    mod = _dec()
    cls = getattr(mod, "ProspectValuation", None)
    if cls is None:
        pytest.skip("ProspectValuation not implemented")
    pv = cls()  # defaults: alpha=beta=0.88, loss_aversion=2.25 (>1)
    gain = pv.v(10.0)
    loss = pv.v(-10.0)
    assert gain > 0 and loss < 0
    # Loss aversion: |v(-x)| > v(x) for equal magnitude.
    assert abs(loss) > gain
    # Diminishing sensitivity: v(20)/v(10) < 2 (concave for gains).
    assert pv.v(20.0) / pv.v(10.0) < 2.0


def test_copula_theta_bounds_and_seeded_determinism():
    # The OCEAN copula lives in mirofish.agent.personality.
    mod = pytest.importorskip("mirofish.agent.personality", reason="mirofish.agent.personality not implemented")
    fn = getattr(mod, "sample_ocean_copula", None)
    if fn is None:
        pytest.skip("sample_ocean_copula not implemented")

    def _sample(seed):
        return fn(1, rng=random.Random(seed))

    a = _sample(42)
    b = _sample(42)
    c = _sample(7)
    row = lambda s: list(s[0]) if hasattr(s, "__getitem__") else list(s)
    fa, fb, fc = row(a), row(b), row(c)
    assert len(fa) == 5, "expected 5 OCEAN dimensions"
    assert all(0.0 <= v <= 1.0 for v in fa), "copula uniforms must lie in [0,1]"
    assert fa == fb, "same seed must produce identical samples"
    assert fa != fc, "different seeds should differ"
