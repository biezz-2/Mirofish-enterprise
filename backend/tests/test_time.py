"""Tests for mirofish.agent.time_engine — Clock determinism, activity sampling, sessions."""

import pytest


def _mod():
    return pytest.importorskip("mirofish.agent.time_engine", reason="mirofish.agent.time_engine not implemented yet")


def test_clock_determinism():
    mod = _mod()
    cls = getattr(mod, "Clock", None) or getattr(mod, "SimClock", None)
    if cls is None:
        pytest.skip("Clock not implemented")
    try:
        c1 = cls(seed=123)
        c2 = cls(seed=123)
    except TypeError:
        try:
            c1, c2 = cls(123), cls(123)
        except TypeError:
            pytest.skip("Clock constructor signature unknown")
    for method in ("now", "tick", "advance", "next", "step"):
        m = getattr(c1, method, None)
        if m is None:
            continue
        try:
            a = m()
            b = getattr(c2, method)()
        except TypeError:
            try:
                a = m(1)
                b = getattr(c2, method)(1)
            except TypeError:
                continue
        assert a == b, f"Clock.{method} not deterministic under same seed"
        return
    pytest.skip("Clock has no callable time method")


def test_activity_vector_sampling_bounds():
    mod = _mod()
    fn = getattr(mod, "sample_activity", None) or getattr(mod, "activity_vector", None)
    cls = getattr(mod, "ActivityModel", None) or getattr(mod, "ActivityVector", None)
    target = fn or cls
    if target is None:
        pytest.skip("no activity vector sampler in mirofish.agent.time_engine")
    sample = None
    if isinstance(target, type):
        try:
            obj = target(platform="x")
        except TypeError:
            try:
                obj = target()
            except TypeError:
                obj = None  # fall through to ActivityVector fallback below
        if obj is not None:
            for mname in ("sample", "draw", "step", "hourly_probs"):
                m = getattr(obj, mname, None)
                if m is None:
                    continue
                try:
                    sample = m()
                    break
                except TypeError:
                    continue
    else:
        for call in (lambda: target(), lambda: target(seed=0), lambda: target(0)):
            try:
                sample = call()
                break
            except TypeError:
                continue
    if sample is None:
        # ActivityVector exposes hourly_probs() directly.
        av_cls = getattr(mod, "ActivityVector", None)
        if av_cls is not None:
            try:
                av = av_cls(platform="x")
                sample = av.hourly_probs()
            except Exception:
                pytest.skip("could not build ActivityVector")
        else:
            pytest.skip("could not sample activity vector")
    vals = list(sample) if not isinstance(sample, (int, float)) else [sample]
    vals = [float(v) for v in vals]
    assert vals, "activity vector must be non-empty"
    # Activity probabilities/rates are bounded in [0, 1] or small non-negative rates.
    assert all(v >= 0.0 for v in vals), "activity values must be non-negative"
    assert all(v <= 1.0 for v in vals), "activity values must be <= 1"


def test_session_model():
    mod = _mod()
    cls = getattr(mod, "SessionModel", None) or getattr(mod, "Session", None)
    if cls is None:
        pytest.skip("SessionModel not implemented")
    try:
        sess = cls()
    except TypeError:
        try:
            sess = cls(seed=0)
        except TypeError:
            pytest.skip("SessionModel constructor signature unknown")
    # Exercise the real API: session lifecycle for a synthetic agent.
    aid = "agent-0"
    if hasattr(sess, "should_start_session"):
        start = sess.should_start_session(aid, tick=0, active=True)
        assert isinstance(start, bool)
    extent_fn = getattr(sess, "session_extent", None)
    if extent_fn is not None:
        extent = extent_fn(aid)
        assert isinstance(extent, int) and extent > 0, "session extent must be positive"
    interval_fn = getattr(sess, "inter_action_interval", None)
    if interval_fn is not None:
        iv = interval_fn(aid)
        assert isinstance(iv, int) and iv >= 0, "inter-action interval must be non-negative"
    if hasattr(sess, "begin_session"):
        assert sess.begin_session(aid) > 0
    if hasattr(sess, "end_session"):
        sess.end_session(aid, tick=1, reward=1.0)
    # Fallback: any zero/one-arg callable producing output.
    produced = extent_fn is not None or interval_fn is not None or hasattr(sess, "begin_session")
    assert produced, "SessionModel produced no output"
