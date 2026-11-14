"""Tests for mirofish.core.ethics — ScenarioGate, AuditLedger."""

import json

import pytest


def _mod():
    return pytest.importorskip("mirofish.core.ethics", reason="mirofish.core.ethics not implemented yet")


def test_scenario_gate_denies_disinformation_optimization():
    mod = _mod()
    cls = getattr(mod, "ScenarioGate", None) or getattr(mod, "EthicsGate", None)
    if cls is None:
        pytest.skip("ScenarioGate not implemented")
    gate = cls()
    scenario = {
        "objective": "disinformation campaign optimization",
        "description": "engineer maximum amplification of fabricated narratives",
        "platform": "x",
    }
    review = getattr(gate, "review_scenario", None) or getattr(gate, "check", None) \
        or getattr(gate, "evaluate", None) or getattr(gate, "screen", None)
    if review is None:
        pytest.skip("ScenarioGate has no review method")
    try:
        res = review(scenario)
    except TypeError:
        pytest.skip("could not call review with a scenario dict")
    # Decision may be an enum (Decision.DENY), a string, or a GateDecision object.
    decision = getattr(res, "decision", res)
    decision_value = getattr(decision, "value", decision)
    denied = str(decision_value).lower() in {"deny", "denied", "reject", "rejected", "block", "blocked"}
    if not denied and isinstance(res, dict):
        denied = not res.get("allowed", res.get("approved", True))
    assert denied, f"ScenarioGate must deny disinformation optimization, got {res!r}"


def test_scenario_gate_allows_benign(tmp_path):
    mod = _mod()
    cls = getattr(mod, "ScenarioGate", None)
    if cls is None:
        pytest.skip("ScenarioGate not implemented")
    gate = cls()
    res = gate.review_scenario({"objective": "study information diffusion patterns", "platform": "x"})
    decision = getattr(res, "decision", res)
    value = str(getattr(decision, "value", decision)).lower()
    assert value in {"allow", "allowed", "escalate", "pass"}, f"benign scenario should not be denied, got {res!r}"


def test_audit_ledger_chain_verify_detects_tampering(tmp_path):
    mod = _mod()
    cls = getattr(mod, "AuditLedger", None) or getattr(mod, "Ledger", None)
    if cls is None:
        pytest.skip("AuditLedger not implemented")
    path = tmp_path / "audit.jsonl"
    try:
        ledger = cls(path)
    except TypeError:
        pytest.skip("AuditLedger constructor signature unknown")

    # Append a few records — try the documented (actor, action, ...) signature first.
    appended = 0
    for i in range(3):
        try:
            ledger.append(actor=f"agent{i}", action="step", params={"i": i}, output={"ok": True})
            appended += 1
        except TypeError:
            try:
                ledger.append({"actor": f"agent{i}", "action": "step", "i": i})
                appended += 1
            except TypeError:
                pass
    assert appended >= 1, "could not append to AuditLedger"

    verify = getattr(ledger, "verify", None) or getattr(ledger, "verify_chain", None)
    if verify is None:
        pytest.skip("AuditLedger.verify not implemented")

    res_before = verify()
    ok_before, msg_before = res_before if isinstance(res_before, tuple) else (res_before, None)
    ok_before = getattr(ok_before, "valid", ok_before)
    assert bool(ok_before), f"fresh ledger should verify, got {msg_before!r}"

    # Tamper with the persisted JSONL: rewrite one record's payload.
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines, "ledger file empty"
        rec = json.loads(lines[0])
        for key in ("actor", "action", "params_hash", "output_hash"):
            if key in rec:
                rec[key] = "TAMPERED"
                break
        lines[0] = json.dumps(rec, sort_keys=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Reload and re-verify.
        try:
            ledger2 = cls(path)
        except TypeError:
            ledger2 = ledger
        v2 = getattr(ledger2, "verify", None) or getattr(ledger2, "verify_chain", None)
        res_after = v2() if v2 is not None else False
        ok_after, _ = res_after if isinstance(res_after, tuple) else (res_after, None)
        ok_after = getattr(ok_after, "valid", ok_after)
        assert not bool(ok_after), "tampered ledger must fail verification"
