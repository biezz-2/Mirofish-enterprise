"""PlatformSpec validator — LINT + SEMANTIC checks beyond Pydantic.

Implements the rules from ``docs/SPEC_SCHEMA.md`` v1.0 that structural
validation (Pydantic) cannot express: cross-reference integrity, feed /
delivery-mode consistency, signal-schema conformance, and provenance
discipline.

Public API:
    validate_spec(spec)            -> list[ValidationIssue]
    smoke_test(spec)                -> dict(pass/fail + issues)
    validate_directory(path)        -> {filename: list[ValidationIssue]}
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from typing import Any

try:
    import yaml  # PyYAML is a declared dependency
except ImportError:  # pragma: no cover - defensive
    yaml = None

# ---------------------------------------------------------------------------
# Issue type
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """A single lint/semantic finding against a PlatformSpec."""

    severity: str          # "error" | "warning"
    code: str              # stable machine-readable code, e.g. "BAD_VERB"
    path: str              # dotted/jsonpath-ish location inside the spec
    message: str

    def __post_init__(self) -> None:
        if self.severity not in ("error", "warning"):
            raise ValueError(f"severity must be 'error' or 'warning', got {self.severity!r}")

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Canonical vocabularies (docs/SPEC_SCHEMA.md)
# ---------------------------------------------------------------------------

VALID_VERBS = {"consume", "react", "amplify", "create", "relational"}

VALID_FEED_KINDS = {"ranked", "chronological", "hybrid", "push", "discover"}

# "hybrid" is used in shipped specs (e.g. instagram.yaml) for platforms that
# combine pull feeds with push surfaces even though SPEC_SCHEMA.md only lists
# pull|push; it is accepted here as pull-compatible.
VALID_DELIVERY_MODES = {"pull", "push", "hybrid"}

VALID_ARCHETYPES = {
    "public_ranked_feed",
    "private_push_feed",
    "private_ranked_feed",
    "chronological",
}

# The ten canonical signal families (paper §6.1 / SPEC_SCHEMA.md §signal_schema).
CANONICAL_SIGNAL_FAMILIES = {
    "recency",
    "engagement_count",
    "attention_dwell",
    "shares_private",
    "author_affinity",
    "topic_graph",
    "negative_feedback",
    "popularity_velocity",
    "content_type_prior",
    "quality_satisfaction",
}

CUSTOM_SIGNAL_PREFIX = "custom_"

VALID_LENGTH_UNITS = {"chars", "utf8_bytes", "graphemes"}

PROVENANCE_LABELS = {"documented", "inferred", "prior"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_dict(spec: Any) -> dict[str, Any]:
    """Accept a plain dict or a Pydantic model; return a plain dict."""
    if spec is None:
        return {}
    if isinstance(spec, dict):
        return spec
    # Pydantic v2 model (or anything with model_dump)
    if hasattr(spec, "model_dump"):
        return spec.model_dump()
    # Pydantic v1 model
    if hasattr(spec, "dict"):
        return spec.dict()
    raise TypeError(
        f"validate_spec expects a dict or Pydantic model, got {type(spec).__name__}"
    )


def _issue(issues: list[ValidationIssue], severity: str, code: str,
           path: str, message: str) -> None:
    issues.append(ValidationIssue(severity=severity, code=code, path=path,
                                  message=message))


def _entity_types(spec: dict[str, Any]) -> set[str]:
    """Collect declared entity_type names."""
    names: set[str] = set()
    for ent in spec.get("entities") or []:
        if isinstance(ent, dict):
            name = ent.get("entity_type")
            if isinstance(name, str) and name:
                names.add(name)
    return names


def _resolve_entity_ref(ref: Any, declared: set[str]) -> list[str]:
    """Normalize an actor/target/relation endpoint to a list of entity names.

    ``target`` may be null, a single entity name, or a list of entity names.
    """
    if ref is None:
        return []
    if isinstance(ref, list):
        return [r for r in ref if isinstance(r, str)]
    if isinstance(ref, str):
        return [ref]
    return []


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------


def validate_spec(spec_dict_or_model: Any) -> list[ValidationIssue]:
    """Run LINT + SEMANTIC checks on a PlatformSpec.

    Args:
        spec_dict_or_model: a ``dict`` (already-parsed YAML) or a Pydantic
            model instance. Anything else raises ``TypeError``.

    Returns:
        A list of :class:`ValidationIssue`. Empty list means clean.
    """
    spec = _as_dict(spec_dict_or_model)
    issues: list[ValidationIssue] = []
    if not spec:
        _issue(issues, "error", "EMPTY_SPEC", "$", "spec is empty or None")
        return issues

    declared_entities = _entity_types(spec)

    # -- top-level enum lint -------------------------------------------------
    for field_name, valid in (
        ("archetype", VALID_ARCHETYPES),
        ("delivery_mode", VALID_DELIVERY_MODES),
    ):
        value = spec.get(field_name)
        if value is not None and value not in valid:
            _issue(issues, "error", "BAD_ENUM", field_name,
                   f"{field_name}={value!r} not in {sorted(valid)}")

    # -- entities -----------------------------------------------------------
    for i, ent in enumerate(spec.get("entities") or []):
        if not isinstance(ent, dict):
            _issue(issues, "error", "BAD_ENTITY", f"entities[{i}]",
                   "entity entry is not a mapping")
            continue
        path = f"entities[{i}]"
        name = ent.get("entity_type")
        if not name:
            _issue(issues, "error", "MISSING_ENTITY_TYPE", path,
                   "entity entry lacks 'entity_type'")
        pk = ent.get("primary_key")
        if not pk:
            _issue(issues, "warning", "MISSING_PRIMARY_KEY", path,
                   f"entity {name!r} declares no primary_key")

    # -- relations: from/to must reference declared entity types ------------
    for i, rel in enumerate(spec.get("relations") or []):
        path = f"relations[{i}]"
        if not isinstance(rel, dict):
            _issue(issues, "error", "BAD_RELATION", path,
                   "relation entry is not a mapping")
            continue
        for endpoint in ("from", "to"):
            ref = rel.get(endpoint)
            if ref is None:
                _issue(issues, "error", "MISSING_RELATION_ENDPOINT", path,
                       f"relation {rel.get('relation_type')!r} lacks '{endpoint}'")
                continue
            if isinstance(ref, str):
                if ref not in declared_entities:
                    _issue(issues, "error", "UNKNOWN_ENTITY_REF", f"{path}.{endpoint}",
                           f"relation endpoint {endpoint}={ref!r} is not a declared "
                           f"entity_type (declared: {sorted(declared_entities)})")
            elif isinstance(ref, list):
                for j, r in enumerate(ref):
                    if isinstance(r, str) and r not in declared_entities:
                        _issue(issues, "error", "UNKNOWN_ENTITY_REF",
                               f"{path}.{endpoint}[{j}]",
                               f"relation endpoint {endpoint}[{j}]={r!r} is not a "
                               f"declared entity_type")
            else:
                _issue(issues, "error", "BAD_RELATION_ENDPOINT", f"{path}.{endpoint}",
                       f"endpoint {endpoint} has unsupported type "
                       f"{type(ref).__name__!r}; expected str, list, or null")

    # -- actions: verb enum + actor/target entity refs ----------------------
    actions = spec.get("actions") or []
    action_ids: set[str] = set()
    for i, act in enumerate(actions):
        path = f"actions[{i}]"
        if not isinstance(act, dict):
            _issue(issues, "error", "BAD_ACTION", path,
                   "action entry is not a mapping")
            continue
        aid = act.get("action_id")
        if aid:
            action_ids.add(aid)

        verb = act.get("verb")
        if verb is not None and verb not in VALID_VERBS:
            _issue(issues, "error", "BAD_VERB", f"{path}.verb",
                   f"action {aid!r} verb={verb!r} not in {sorted(VALID_VERBS)}")

        for endpoint in ("actor", "target"):
            for j, ref in enumerate(_resolve_entity_ref(act.get(endpoint), declared_entities)):
                if ref not in declared_entities:
                    _issue(issues, "error", "UNKNOWN_ENTITY_REF",
                           f"{path}.{endpoint}" + (f"[{j}]" if endpoint == "target" else ""),
                           f"action {aid!r} {endpoint}={ref!r} is not a declared "
                           f"entity_type (declared: {sorted(declared_entities)})")

    # -- feed / delivery consistency ----------------------------------------
    feed = spec.get("feed")
    feed_kind = feed.get("kind") if isinstance(feed, dict) else None
    delivery_mode = spec.get("delivery_mode")
    archetype = spec.get("archetype")
    privacy_tier = spec.get("privacy_tier")

    if isinstance(feed, dict):
        if feed_kind is not None and feed_kind not in VALID_FEED_KINDS:
            _issue(issues, "error", "BAD_FEED_KIND", "feed.kind",
                   f"feed.kind={feed_kind!r} not in {sorted(VALID_FEED_KINDS)}")

        scorer = feed.get("scorer")
        scorer_plugin = scorer.get("plugin") if isinstance(scorer, dict) else None

        if feed_kind == "push":
            # Push delivery forbids ranking plugins (SPEC_SCHEMA.md feed section).
            if scorer_plugin:
                _issue(issues, "error", "PUSH_WITH_SCORER", "feed.scorer.plugin",
                       "feed.kind='push' must not declare scorer.plugin "
                       f"(got {scorer_plugin!r}); use delivery_model.inbox_rules instead")
            if feed.get("retrieval"):
                _issue(issues, "warning", "PUSH_WITH_RETRIEVAL", "feed.retrieval",
                       "feed.kind='push' declares retrieval sources; push delivery "
                       "has no candidate-pool retrieval")
            if delivery_mode == "pull":
                _issue(issues, "warning", "PUSH_PULL_MISMATCH", "delivery_mode",
                       "feed.kind='push' but delivery_mode='pull'; expected 'push'")
        elif feed_kind in ("ranked", "hybrid", "chronological"):
            if delivery_mode == "push":
                _issue(issues, "warning", "PULL_MODE_PUSH_DELIVERY",
                       "delivery_mode",
                       f"feed.kind={feed_kind!r} implies pull materialization but "
                       "delivery_mode='push'; expected 'pull'")
            if feed_kind == "chronological" and scorer_plugin \
                    and scorer_plugin != "chronological":
                _issue(issues, "warning", "CHRONOLOGICAL_WITH_SCORER",
                       "feed.scorer.plugin",
                       f"feed.kind='chronological' with scorer.plugin="
                       f"{scorer_plugin!r}; chronological feeds normally have no "
                       "ranking plugin")
        # discover is a browse surface; exempt from delivery-mode coupling.

        # -- signal_schema: canonical families + custom_* prefix --------------
        signal_schema = feed.get("signal_schema")
        if isinstance(signal_schema, list):
            for j, sig in enumerate(signal_schema):
                spath = f"feed.signal_schema[{j}]"
                if not isinstance(sig, dict):
                    _issue(issues, "error", "BAD_SIGNAL", spath,
                           "signal_schema entry is not a mapping")
                    continue
                name = sig.get("name")
                if not name:
                    _issue(issues, "error", "MISSING_SIGNAL_NAME", spath,
                           "signal_schema entry lacks 'name'")
                elif isinstance(name, str):
                    if name not in CANONICAL_SIGNAL_FAMILIES \
                            and not name.startswith(CUSTOM_SIGNAL_PREFIX):
                        _issue(issues, "error", "UNKNOWN_SIGNAL_FAMILY", f"{spath}.name",
                               f"signal {name!r} is not one of the 10 canonical "
                               f"families {sorted(CANONICAL_SIGNAL_FAMILIES)} and "
                               f"does not use the '{CUSTOM_SIGNAL_PREFIX}' prefix")
                # provenance discipline: weight cells must carry a label
                # (model_dump emits provenance=None, so check value not key)
                if "weight" in sig and sig.get("weight") is not None \
                        and sig.get("provenance") is None:
                    _issue(issues, "warning", "MISSING_PROVENANCE",
                           f"{spath}.weight",
                           f"signal {sig.get('name')!r} declares a weight without a "
                           "provenance label (documented|inferred|prior)")
                elif sig.get("provenance") is not None \
                        and sig.get("provenance") not in PROVENANCE_LABELS:
                    _issue(issues, "warning", "BAD_PROVENANCE", f"{spath}.provenance",
                           f"signal {sig.get('name')!r} provenance="
                           f"{sig.get('provenance')!r} not in "
                           f"{sorted(PROVENANCE_LABELS)}")

        # -- retrieval quota provenance (weight cells) ------------------------
        retrieval = feed.get("retrieval")
        if isinstance(retrieval, list):
            for j, r in enumerate(retrieval):
                if isinstance(r, dict) and r.get("quota_ratio") is not None \
                        and r.get("provenance") is None:
                    _issue(issues, "warning", "MISSING_PROVENANCE",
                           f"feed.retrieval[{j}].quota_ratio",
                           f"retrieval source {r.get('source')!r} declares "
                           "quota_ratio without a provenance label")

        # -- feed.params weights provenance -----------------------------------
        params = feed.get("params")
        if isinstance(params, dict):
            weights = params.get("weights")
            if isinstance(weights, dict):
                prov = params.get("provenance")
                if prov is None:
                    _issue(issues, "warning", "MISSING_PROVENANCE",
                           "feed.params.weights",
                           "feed.params.weights contains weight cells but no "
                           "provenance label at feed.params.provenance")
                elif prov not in PROVENANCE_LABELS:
                    _issue(issues, "warning", "BAD_PROVENANCE",
                           "feed.params.provenance",
                           f"feed.params.provenance={prov!r} not in "
                           f"{sorted(PROVENANCE_LABELS)}")

    # -- privacy_tier <-> delivery_mode sanity -------------------------------
    if privacy_tier == "private":
        # Private platforms must deliver via push fan-out or a private ranked
        # feed; a plain public pull feed contradicts the privacy tier.
        if delivery_mode not in ("push", "hybrid") \
                and archetype != "private_ranked_feed":
            _issue(issues, "warning", "PRIVATE_PULL_FEED", "privacy_tier",
                   "privacy_tier='private' but delivery_mode="
                   f"{delivery_mode!r} and archetype={archetype!r}; expected "
                   "push delivery or private_ranked_feed")

    # -- content_constraints -------------------------------------------------
    cc = spec.get("content_constraints")
    if isinstance(cc, dict):
        if cc.get("max_length_chars") is not None:
            unit = cc.get("length_unit")
            if unit is None:
                _issue(issues, "error", "MISSING_LENGTH_UNIT",
                       "content_constraints.length_unit",
                       "content_constraints.max_length_chars is set but "
                       "length_unit is undeclared (chars|utf8_bytes|graphemes)")
            elif unit not in VALID_LENGTH_UNITS:
                _issue(issues, "error", "BAD_LENGTH_UNIT",
                       "content_constraints.length_unit",
                       f"length_unit={unit!r} not in {sorted(VALID_LENGTH_UNITS)}")

    # -- moderation: metadata_only => e2e ------------------------------------
    mod = spec.get("moderation")
    if isinstance(mod, dict) and mod.get("metadata_only") is True:
        if spec.get("encryption") != "e2e":
            _issue(issues, "error", "METADATA_ONLY_WITHOUT_E2E",
                   "moderation.metadata_only",
                   "moderation.metadata_only=true requires encryption='e2e' "
                   f"(got encryption={spec.get('encryption')!r})")

    # -- moderation.enforcement_points should reference declared actions ------
    if isinstance(mod, dict):
        points = mod.get("enforcement_points") or []
        for p in points:
            if isinstance(p, str) and p not in action_ids \
                    and p not in declared_entities:
                _issue(issues, "warning", "UNKNOWN_ENFORCEMENT_POINT",
                       "moderation.enforcement_points",
                       f"enforcement point {p!r} matches neither a declared "
                       "action_id nor entity_type")

    return issues


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


def smoke_test(spec_dict_or_model: Any) -> dict[str, Any]:
    """Instantiate a minimal in-memory scenario for a PlatformSpec.

    Creates a store, registers the spec's entities/actions, and runs one
    fake action through its preconditions. Written defensively: the core
    ``store``/``spec`` modules are developed in parallel, so all imports and
    calls are guarded — if the runtime isn't available the result reports
    ``passed=None`` with an explanatory issue rather than raising.

    Returns:
        dict with keys:
            passed   : True | False | None (None = skipped, runtime missing)
            issues   : list[ValidationIssue]
            detail   : human-readable summary
    """
    issues: list[ValidationIssue] = []

    spec = _as_dict(spec_dict_or_model)
    if not spec:
        issues.append(ValidationIssue("error", "EMPTY_SPEC", "$",
                                      "smoke_test received an empty spec"))
        return {"passed": False, "issues": issues, "detail": "empty spec"}

    try:
        # Defensive imports — store.py / spec.py may not exist yet.
        from mirofish.core import store as store_mod  # type: ignore
        from mirofish.core import spec as spec_mod    # type: ignore
    except Exception as exc:  # ImportError or partially-written modules
        issues.append(ValidationIssue(
            "warning", "SMOKE_SKIPPED", "smoke_test",
            f"core runtime unavailable ({exc.__class__.__name__}: {exc}); "
            "smoke test skipped"))
        return {"passed": None, "issues": issues,
                "detail": "skipped — core modules not ready"}

    try:
        # 1. Build a store and register the spec's entity types.
        store_cls = getattr(store_mod, "Store", None) or getattr(
            store_mod, "InMemoryStore", None)
        if store_cls is None:
            raise AttributeError("store module exposes no Store/InMemoryStore")
        store = store_cls()

        register = getattr(store, "register_spec", None) or getattr(
            store, "load_spec", None) or getattr(store, "register", None)
        if register is not None:
            register(spec)
        else:
            # Fall back: register each declared entity type individually.
            reg_entity = getattr(store, "register_entity", None)
            if reg_entity is not None:
                for ent in spec.get("entities") or []:
                    if isinstance(ent, dict) and ent.get("entity_type"):
                        reg_entity(ent["entity_type"])

        # 2. Pick the first action and fabricate a minimal actor/target.
        actions = [a for a in (spec.get("actions") or [])
                   if isinstance(a, dict)]
        if not actions:
            issues.append(ValidationIssue(
                "warning", "SMOKE_NO_ACTIONS", "actions",
                "spec declares no actions; nothing to exercise"))
            return {"passed": True, "issues": issues,
                    "detail": "no actions declared — registration only"}

        action = actions[0]
        actor_type = action.get("actor")
        target_type = action.get("target")
        if isinstance(target_type, list):
            target_type = target_type[0] if target_type else None

        # Fabricate instances keyed by primary_key where possible.
        def _make_instance(entity_name):
            for ent in spec.get("entities") or []:
                if isinstance(ent, dict) and ent.get("entity_type") == entity_name:
                    pk = ent.get("primary_key") or []
                    attrs = ent.get("attributes") or {}
                    inst = {}
                    for k in pk:
                        spec_attr = attrs.get(k) or {}
                        t = spec_attr.get("type")
                        inst[k] = {"integer": 1, "float": 1.0,
                                   "boolean": True}.get(t, "smoke")
                    for k, v in attrs.items():
                        inst.setdefault(k, v.get("default")
                                        if isinstance(v, dict) else None)
                    return inst
            return {"id": "smoke"}

        actor = _make_instance(actor_type) if actor_type else {}
        target = _make_instance(target_type) if target_type else None

        # 3. Run the action through preconditions.
        run = (getattr(store, "run_action", None)
               or getattr(store, "apply_action", None)
               or getattr(store, "execute", None))
        if run is None:
            issues.append(ValidationIssue(
                "warning", "SMOKE_NO_RUNNER", "smoke_test",
                "store exposes no run_action/apply_action/execute; "
                "precondition evaluation skipped"))
            return {"passed": True, "issues": issues,
                    "detail": "registered entities; no action runner available"}

        # Prefer a spec-module precondition evaluator if present.
        eval_pre = getattr(spec_mod, "check_preconditions", None) or getattr(
            spec_mod, "evaluate_preconditions", None)
        preconditions = action.get("preconditions") or {}
        if eval_pre is not None and preconditions:
            ok = eval_pre(action, actor, target, store)
            if ok is False:
                issues.append(ValidationIssue(
                    "error", "SMOKE_PRECONDITION_FAIL",
                    f"actions[{actions.index(action)}].preconditions",
                    f"action {action.get('action_id')!r} failed its own "
                    "declared preconditions on fabricated inputs"))
                return {"passed": False, "issues": issues,
                        "detail": "precondition check failed"}

        result = run(action, actor=actor, target=target)
        if result is False:
            issues.append(ValidationIssue(
                "error", "SMOKE_ACTION_REJECTED", "actions[0]",
                f"action {action.get('action_id')!r} was rejected by the "
                "store on fabricated inputs"))
            return {"passed": False, "issues": issues,
                    "detail": "action rejected"}

        return {"passed": True, "issues": issues,
                "detail": f"registered spec; ran action "
                          f"{action.get('action_id')!r} -> {result!r}"[:200]}

    except Exception as exc:  # defensive: never let smoke_test crash callers
        issues.append(ValidationIssue(
            "error", "SMOKE_EXCEPTION", "smoke_test",
            f"smoke test raised {exc.__class__.__name__}: {exc}"))
        return {"passed": False, "issues": issues,
                "detail": f"exception: {exc}"}


# ---------------------------------------------------------------------------
# Directory validation
# ---------------------------------------------------------------------------


def validate_directory(path: str = "platforms/") -> dict[str, list[ValidationIssue]]:
    """Load every ``*.yaml`` under ``path`` and validate each spec.

    Returns a mapping ``{filename: [ValidationIssue, ...]}``. Files that fail
    to parse produce a single ``PARSE_ERROR`` issue under their filename.
    """
    results: dict[str, list[ValidationIssue]] = {}

    if yaml is None:
        raise RuntimeError("PyYAML is required for validate_directory")

    pattern = os.path.join(path, "*.yaml")
    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except Exception as exc:
            results[filename] = [ValidationIssue(
                "error", "PARSE_ERROR", "$",
                f"failed to load YAML: {exc.__class__.__name__}: {exc}")]
            continue
        if data is None:
            results[filename] = [ValidationIssue(
                "error", "EMPTY_FILE", "$", "YAML file parsed to None")]
            continue
        results[filename] = validate_spec(data)

    return results


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    import sys
    args = argv if argv is not None else sys.argv[1:]
    directory = args[0] if args else "platforms/"
    results = validate_directory(directory)
    total_errors = total_warnings = 0
    rc = 0
    for filename, issues in results.items():
        errs = [i for i in issues if i.severity == "error"]
        warns = [i for i in issues if i.severity == "warning"]
        total_errors += len(errs)
        total_warnings += len(warns)
        status = "FAIL" if errs else ("warn" if warns else "ok")
        print(f"[{status:>4}] {filename}: {len(errs)} error(s), "
              f"{len(warns)} warning(s)")
        for i in issues:
            print(f"       {i.severity:>7} {i.code} @ {i.path}: {i.message}")
        if errs:
            rc = 1
    print(f"\n{len(results)} file(s): {total_errors} error(s), "
          f"{total_warnings} warning(s)")
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
