"""Delivery dispatcher for PlatformSpec actions.

Two paradigms (see ``docs/SPEC_SCHEMA.md``):

- **PULL** (``delivery_mode: pull``): feed materialization is *deferred* to
  ``feed.py`` — ``deliver`` only acknowledges the mode.
- **PUSH** (``delivery_mode: push``): write-time fan-out. ``deliver`` resolves
  recipients through the spec's relation tables and calls
  ``EntityStore.fanout_push`` so each recipient gets an inbox entry ordered by
  the platform's ``feed.delivery_model.inbox_rules`` (pinned > unread >
  recency, enforced in ``EntityStore.inbox``).

Visibility is pre-checked via ``check_visibility`` against
``visibility_model.default_scope`` and its membership-predicate rules.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from .store import EntityStore, entity_key

# Relation semantics that describe an audience/container a message is
# delivered *into* — i.e. the counterpart endpoints are push recipients.
AUDIENCE_SEMANTICS = {
    "membership",
    "conversation_membership",
    "ordered_membership",
    "container_scoping",
    "containment",
    "grouping",
    "one_way_follow",
    "channel_followed",
    "mutual_connection",
    "mutual_affiliation_gate",
    "bidirectional_opt_in",
    "visibility_gate",
    "ownership",
    "status_audience",
    "community_unit",
    "group_member_of",
    "dm_between",
}

# Semantics that veto delivery outright when an edge exists between actor
# and target (blocks, mutes, hard exclusions).
EXCLUSION_SEMANTICS = {
    "hard_exclusion",
    "negative_feedback",
    "negative_feedback_edge",
    "feed_filter",
    "downrank_signal",
}

# Entity data keys that identify the "agent" endpoint of an edge when the
# edge's endpoint is itself an association/join entity (e.g. ChatMember).
_AGENT_ID_KEYS = ("user_id", "agent_id", "account_id", "owner_id", "member_id", "id")

_NO_GRANT = {None, "", "none", "none_required", "null", "self_only"}


# ----------------------------------------------------------------------
# spec access helpers (tolerate dicts, pydantic models, or attribute objects)
# ----------------------------------------------------------------------
def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    if hasattr(obj, key):
        return getattr(obj, key)
    if hasattr(obj, "model_dump"):  # pydantic v2
        return obj.model_dump().get(key, default)
    if hasattr(obj, "dict"):  # pydantic v1
        return obj.dict().get(key, default)
    return default


def _spec_dicts(spec: Any, key: str) -> list[dict]:
    """Normalize a spec section (relations, rules, ...) into plain dicts."""
    items = _get(spec, key, []) or []
    out = []
    for it in items:
        if isinstance(it, Mapping):
            out.append(dict(it))
        elif hasattr(it, "model_dump"):
            out.append(it.model_dump())
        elif hasattr(it, "dict"):
            out.append(it.dict())
        elif hasattr(it, "__dict__"):
            out.append(dict(vars(it)))
        else:
            out.append({"value": it})
    return out


def _parse_ref(ref: Any) -> Optional[tuple[str, str]]:
    """Parse an entity reference into ``(entity_type, entity_id)``.

    Accepts ``"Type:id"``, ``{"entity_type"/"type", "entity_id"/"id"}``,
    ``(type, id)`` tuples, or a bare id (type ``""``).
    """
    if ref is None:
        return None
    if isinstance(ref, (tuple, list)) and len(ref) == 2:
        return str(ref[0]), entity_key(ref[1])
    if isinstance(ref, Mapping):
        etype = ref.get("entity_type") or ref.get("type") or ref.get("entity") or ""
        eid = (
            ref.get("entity_id")
            or ref.get("id")
            or ref.get("entity")
            or ref.get("target_ref")
        )
        if eid is None and len(ref) == 1:
            eid = next(iter(ref.values()))
        return str(etype), entity_key(eid)
    s = str(ref)
    if ":" in s:
        etype, _, eid = s.partition(":")
        return etype, eid
    return "", s


def _ref_id(ref: Any) -> str:
    parsed = _parse_ref(ref)
    return parsed[1] if parsed else entity_key(ref)


# ----------------------------------------------------------------------
# recipient resolution
# ----------------------------------------------------------------------
def _agent_id_for_endpoint(
    store: EntityStore, endpoint_type: str, endpoint_id: str
) -> str:
    """Map a relation endpoint to an agent id.

    If the endpoint is an association entity (e.g. ``ChatMember`` whose id is
    a composite key), look inside its JSON data for a user/agent id field.
    """
    eid = entity_key(endpoint_id)
    if endpoint_type:
        ent = store.get_entity(endpoint_type, eid)
        if ent:
            data = ent.get("data") or {}
            for key in _AGENT_ID_KEYS:
                if data.get(key) is not None:
                    return entity_key(data[key])
    return eid


def _audience_relation_types(spec: Any, scope: Optional[str]) -> set[str]:
    """Relation types that define the audience for ``scope``.

    Sources: (a) spec relations whose semantics are audience-like, and
    (b) ``visibility_model.rules`` entries whose ``scope`` matches and whose
    ``grants`` names a relation type.
    """
    rel_types: set[str] = set()
    for rel in _spec_dicts(spec, "relations"):
        sem = str(rel.get("semantics") or "")
        rtype = rel.get("relation_type")
        if rtype and sem in AUDIENCE_SEMANTICS:
            rel_types.add(str(rtype))
    vm = _get(spec, "visibility_model") or {}
    rules = vm.get("rules") if isinstance(vm, Mapping) else _get(vm, "rules", [])
    for rule in rules or []:
        r = rule if isinstance(rule, Mapping) else getattr(rule, "__dict__", {})
        r_scope = r.get("scope")
        grants = r.get("grants")
        if scope and r_scope and str(r_scope) != str(scope):
            continue
        if isinstance(grants, str) and grants not in _NO_GRANT:
            rel_types.add(grants)
        elif isinstance(grants, (list, tuple)):
            rel_types.update(str(g) for g in grants if str(g) not in _NO_GRANT)
    return rel_types


def resolve_recipients(
    spec: Any,
    message: Mapping[str, Any],
    store: Optional[EntityStore] = None,
) -> list[str]:
    """Resolve push recipients for ``message`` via the spec's relations.

    Priority:
    1. Explicit ``message["recipients"]`` if present.
    2. Relation-table fan-out: find audience edges (membership etc.) that
       touch the message's target entity; counterpart endpoints become
       recipients. Association endpoints (e.g. ChatMember) are resolved to
       the underlying agent id via entity data.
    3. Empty list — caller decides whether that means "no delivery".
    """
    explicit = message.get("recipients")
    if explicit:
        if isinstance(explicit, (str, bytes)) or not isinstance(explicit, Iterable):
            explicit = [explicit]
        return [_ref_id(r) for r in explicit]

    if store is None:
        return []

    actor_id = _ref_id(message.get("actor_id") or message.get("actor"))
    target_ref = (
        message.get("target_ref")
        or message.get("target")
        or message.get("item_ref")
    )
    target = _parse_ref(target_ref)
    scope = message.get("visibility") or message.get("scope")

    recipients: list[str] = []
    seen: set[str] = set()

    for rel_type in _audience_relation_types(spec, scope):
        # Edges of this type touching the target entity id (either side).
        edges = store.relations_of(target[1] if target else "", rel_type)
        for edge in edges:
            # The endpoint that is NOT the target is the candidate audience.
            for side in ("from", "to"):
                ep_type = edge[f"{side}_type"]
                ep_id = edge[f"{side}_id"]
                if target and ep_id == target[1]:
                    continue
                agent = _agent_id_for_endpoint(store, ep_type, ep_id)
                if actor_id and agent == actor_id:
                    continue  # never deliver back to the sender
                if agent not in seen:
                    seen.add(agent)
                    recipients.append(agent)
    return recipients


# ----------------------------------------------------------------------
# visibility pre-check
# ----------------------------------------------------------------------
def _exclusion_between(
    store: EntityStore, spec: Any, a_id: str, b_id: str
) -> bool:
    """True if a hard-exclusion/negative-feedback edge links actor & target."""
    blocked_types = {
        str(rel.get("relation_type"))
        for rel in _spec_dicts(spec, "relations")
        if str(rel.get("semantics") or "") in EXCLUSION_SEMANTICS
        and rel.get("relation_type")
    }
    if not blocked_types:
        return False
    for rtype in blocked_types:
        if store.has_relation(a_id, b_id, rtype):
            return True
    return False


def _membership_holds(
    store: EntityStore,
    spec: Any,
    actor_id: str,
    target: tuple[str, str],
    relation_type: str,
) -> bool:
    """Basic membership-predicate check for a visibility rule's ``grants``.

    Handles both direct edges (User -membership-> Chat) and association
    entities (ChatMember -> Chat, where the actor endpoint resolves through
    the join entity's data).
    """
    target_type, target_id = target
    if store.has_relation(actor_id, target_id, relation_type):
        return True

    # General case: find every edge of this type touching the target, resolve
    # the *other* endpoint to an agent id, and compare with the actor. This
    # covers both direct edges (User -membership-> Chat) and association
    # entities (ChatMember -> Chat, where the user id lives in the join
    # entity's JSON data rather than in the edge endpoints).
    for edge in store.relations_of(target_id, relation_type):
        for side in ("from", "to"):
            ep_type, ep_id = edge[f"{side}_type"], edge[f"{side}_id"]
            if ep_id == target_id:
                continue
            agent = _agent_id_for_endpoint(store, ep_type, ep_id)
            if agent == actor_id:
                return True
    return False


def check_visibility(
    spec: Any,
    actor: Any,
    target: Any,
    store: Optional[EntityStore] = None,
) -> bool:
    """Evaluate ``visibility_model`` for an actor acting on a target.

    ``target`` may be a ref (``"Type:id"`` / dict / tuple) or a dict carrying
    ``scope``/``visibility`` to select a rule; otherwise
    ``visibility_model.default_scope`` applies. Basic level: broadcast/self
    scopes are decided locally; membership scopes require a matching relation
    edge (or join-entity path) in the store. Hard-exclusion edges veto.
    """
    vm = _get(spec, "visibility_model") or {}
    if isinstance(vm, Mapping):
        default_scope = vm.get("default_scope")
        rules = vm.get("rules") or []
    else:
        default_scope = _get(vm, "default_scope")
        rules = _get(vm, "rules", []) or []

    actor_id = _ref_id(actor if not isinstance(actor, Mapping) else actor.get("id") or actor.get("agent_id") or actor)
    target_ref = target.get("target_ref") if isinstance(target, Mapping) else None
    scope = None
    if isinstance(target, Mapping):
        scope = target.get("scope") or target.get("visibility")
        target = target_ref or target.get("entity") or target.get("id") or target
    scope = scope or default_scope

    t = _parse_ref(target)
    target_id = t[1] if t else _ref_id(target)
    target_type = t[0] if t else ""

    # Public/broadcast scopes need no relation.
    if scope in ("broadcast", "public", "everyone", "world"):
        return True
    # Self scope: actor may only see/touch its own objects.
    if scope == "self":
        return actor_id == target_id

    if store is None:
        # Without a store we can only honor unconditional scopes.
        return scope in ("broadcast", "public", "everyone", "world")

    # Hard exclusions veto everything.
    if _exclusion_between(store, spec, actor_id, target_id):
        return False

    # Find matching rules; a rule with grants=None/none_required allows.
    matched = False
    for rule in rules or []:
        r = rule if isinstance(rule, Mapping) else getattr(rule, "__dict__", {})
        r_scope = str(r.get("scope") or "")
        if scope and r_scope and r_scope != str(scope):
            continue
        matched = True
        grants = r.get("grants")
        grant_list = grants if isinstance(grants, (list, tuple)) else [grants]
        grant_list = [g for g in grant_list if g is not None]
        if not grant_list or all(str(g) in _NO_GRANT for g in grant_list):
            return True
        for g in grant_list:
            if str(g) in _NO_GRANT:
                continue
            if _membership_holds(store, spec, actor_id, (target_type, target_id), str(g)):
                return True
        # Rule matched but no grant satisfied → try next rule; if none match
        # at all below we fall through to default deny.
    if matched:
        return False

    # No explicit rule for this scope: fall back to audience relations of
    # the same scope name, then to default_scope semantics.
    rel_types = _audience_relation_types(spec, scope)
    if rel_types:
        for rtype in rel_types:
            if _membership_holds(store, spec, actor_id, (target_type, target_id), rtype):
                return True
        return False
    # Unknown scope with no rules: deny (fail closed for private platforms).
    return False


# ----------------------------------------------------------------------
# dispatcher
# ----------------------------------------------------------------------
def deliver(
    spec: Any,
    action_result: Mapping[str, Any],
    store: EntityStore,
) -> dict:
    """Dispatch an action result according to ``spec.delivery_mode``.

    - ``pull``  → deferred to feed materialization (``feed.py``); returns a
      ``deferred`` marker and writes nothing.
    - ``push``  → visibility pre-check, recipient resolution via relations,
      then ``store.fanout_push``.
    """
    mode = str(_get(spec, "delivery_mode", "pull") or "pull").lower()

    if mode == "pull":
        return {
            "mode": "pull",
            "delivered": False,
            "deferred": "feed.py",
            "reason": "pull delivery materializes feeds at query time",
        }

    if mode != "push":
        return {"mode": mode, "delivered": False, "reason": "unknown delivery_mode"}

    # Normalize the payload into a message dict.
    result = dict(action_result or {})
    message = dict(result.get("message") or {})
    for k, v in result.items():
        message.setdefault(k, v)
    if "item_ref" not in message:
        message["item_ref"] = (
            message.get("target_ref")
            or message.get("target")
            or f"{message.get('action_id', 'action')}:{store.tick()}"
        )

    actor = message.get("actor_id") or message.get("actor")
    target = message.get("target_ref") or message.get("target") or message.get("item_ref")

    if not check_visibility(spec, actor, target, store):
        store.record_interaction(
            actor_id=_ref_id(actor),
            action_id=str(message.get("action_id", "deliver")),
            target_ref=str(target) if target is not None else None,
            payload={"delivery": "push", "result": "visibility_denied"},
        )
        return {
            "mode": "push",
            "delivered": False,
            "reason": "visibility_denied",
        }

    recipients = resolve_recipients(spec, message, store)
    if not recipients:
        return {
            "mode": "push",
            "delivered": False,
            "reason": "no_recipients",
            "recipients": [],
        }

    deliveries = store.fanout_push(message, recipients)
    store.record_interaction(
        actor_id=_ref_id(actor),
        action_id=str(message.get("action_id", "deliver")),
        target_ref=str(target) if target is not None else None,
        payload={"delivery": "push", "recipients": recipients},
    )
    return {
        "mode": "push",
        "delivered": True,
        "recipients": recipients,
        "deliveries": deliveries,
    }


__all__ = [
    "deliver",
    "resolve_recipients",
    "check_visibility",
    "AUDIENCE_SEMANTICS",
    "EXCLUSION_SEMANTICS",
]
