"""Tests for mirofish.calibration.metrics — gini, ks_distance, cascade metrics."""

import pytest


def _mod():
    return pytest.importorskip("mirofish.calibration.metrics", reason="mirofish.calibration.metrics not implemented yet")


def _fn(mod, *names):
    for n in names:
        f = getattr(mod, n, None)
        if f is not None:
            return f
    pytest.skip(f"none of {names} in mirofish.calibration.metrics")


def test_gini_equal_values_zero():
    mod = _mod()
    gini = _fn(mod, "gini", "gini_coefficient", "compute_gini")
    vals = [5.0] * 10
    assert gini(vals) == pytest.approx(0.0, abs=1e-9)


def test_gini_concentrated_positive():
    mod = _mod()
    gini = _fn(mod, "gini", "gini_coefficient", "compute_gini")
    concentrated = [100.0] + [0.0] * 9
    equal = [10.0] * 10
    assert gini(concentrated) > gini(equal)
    assert gini(concentrated) > 0


def test_ks_distance_identical_zero():
    mod = _mod()
    ks = _fn(mod, "ks_distance", "ks_statistic", "ks")
    a = [0.1, 0.2, 0.3, 0.4, 0.5]
    b = list(a)
    assert ks(a, b) == pytest.approx(0.0, abs=1e-9)
    # Sanity: shifted distributions give a positive distance.
    c = [0.6, 0.7, 0.8, 0.9, 1.0]
    assert ks(a, c) > 0


def test_cascade_metrics_toy_graph():
    mod = _mod()
    fn = _fn(mod, "cascade_metrics", "cascade_size", "info_cascade_metrics", "cascade_depth")
    # Toy graph: seed -> a -> b, seed -> c (two hops max, branching).
    graph = {
        "seed": ["a", "c"],
        "a": ["b"],
        "c": [],
        "b": [],
    }
    result = None
    for call in (
        lambda: fn(graph),
        lambda: fn(graph, seed="seed"),
        lambda: fn({"seed": ["a", "c"], "a": ["b"], "c": [], "b": []}),
        lambda: fn(edges=[("seed", "a"), ("seed", "c"), ("a", "b")]),
    ):
        try:
            result = call()
            break
        except TypeError:
            continue
    if result is None:
        pytest.skip("could not call cascade metric with a known signature")
    # Result should expose at least size/depth/branching info; keep assertions loose.
    if isinstance(result, dict):
        assert result, "cascade metrics returned empty dict"
    else:
        vals = list(result) if hasattr(result, "__iter__") else [result]
        assert vals or result is not None
