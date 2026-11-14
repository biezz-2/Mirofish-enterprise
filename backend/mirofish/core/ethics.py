"""Ethics & governance layer for MiroFish.

Stdlib-only module implementing:
  - AccessTier / capability gating per paper §21 governance split
  - ScenarioGate: pre-run ethics review (prohibited patterns + escalation triggers)
  - AuditLedger: append-only hash-chained JSONL audit log
  - ProvenanceMarker: C2PA-compatible metadata for exported artifacts
  - DataProvenance: per-run registry of data sources with legality tags
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "AccessTier",
    "Capability",
    "capabilities_for",
    "GateDecision",
    "Decision",
    "ScenarioGate",
    "AuditLedger",
    "AuditRecord",
    "ProvenanceMarker",
    "HUMAN_LABEL",
    "DataProvenance",
    "ProhibitedSourceError",
]

try:  # package version if available; fallback otherwise
    from mirofish import __version__ as _VER
except Exception:  # pragma: no cover
    _VER = "0.1.0"


# ---------------------------------------------------------------------------
# 1. Access tiers & capabilities
# ---------------------------------------------------------------------------


class AccessTier(str, Enum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


class Capability(str, Enum):
    PLATFORM_SCHEMAS = "platform_schemas"            # PlatformSpec schemas
    MATH_LAYER = "math_layer"                        # core math/simulation layer
    VALIDATION_HARNESS = "validation_harness"        # validation harness
    CALIBRATED_PARAMS = "calibrated_params"          # calibrated sensitive-platform params
    SCENARIO_TEMPLATES = "scenario_templates"        # realistic scenario templates
    BULK_POPULATION = "bulk_population"              # bulk-population configs


_CAPABILITIES: dict[AccessTier, frozenset[Capability]] = {
    AccessTier.PUBLIC: frozenset(
        {Capability.PLATFORM_SCHEMAS, Capability.MATH_LAYER, Capability.VALIDATION_HARNESS}
    ),
    AccessTier.RESTRICTED: frozenset(
        {
            Capability.PLATFORM_SCHEMAS,
            Capability.MATH_LAYER,
            Capability.VALIDATION_HARNESS,
            Capability.CALIBRATED_PARAMS,
            Capability.SCENARIO_TEMPLATES,
            Capability.BULK_POPULATION,
        }
    ),
}


def capabilities_for(tier: AccessTier) -> frozenset[Capability]:
    """Return the set of capabilities granted to an access tier."""
    return _CAPABILITIES[tier]


# ---------------------------------------------------------------------------
# 2. ScenarioGate — ethics review before runs
# ---------------------------------------------------------------------------


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class GateDecision:
    decision: Decision
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"decision": self.decision.value, "reasons": list(self.reasons)}


# Prohibited patterns (paper §21.4). Each entry: (name, compiled regex).
# Matched case-insensitively against a normalized JSON dump of the scenario.
_PROHIBITED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(pattern, re.IGNORECASE | re.DOTALL))
    for name, pattern in [
        (
            "disinformation_campaign_optimization",
            r"(disinformation|misinformation|propaganda|astroturf).{0,80}"
            r"(optimis|campaign|amplif|maximi[sz]e|engineer)",
        ),
        (
            "platform_integrity_evasion",
            r"(evade|bypass|circumvent|defeat|avoid).{0,80}"
            r"(platform.{0,20}(integrity|moderation|detection|policy)|trust.{0,20}and.{0,20}safety|anti.?abuse)",
        ),
        (
            "targeted_harassment",
            r"(harass|dox|stalk|intimidate|target).{0,80}"
            r"(identif|individual|person|group|community|ethnic|religious).{0,40}"
            r"(by.{0,20}(name|handle|address|location)|identit)",
        ),
        (
            "deceptive_synthetic_media",
            r"(deepfake|synthetic.{0,20}(video|audio|image|media)|fake.{0,20}(video|audio|photo)).{0,80}"
            r"(deceiv|mislead|impersonat|fraud|undisclosed|without.{0,20}disclos)",
        ),
    ]
)

# Escalation triggers (require human ethics review, not outright denial).
_ESCALATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(pattern, re.IGNORECASE | re.DOTALL))
    for name, pattern in [
        (
            "public_health_misinfo",
            r"(vaccine|vaccin|public.{0,10}health|pandemic|epidemic|disease|"
            r"medical.{0,10}(misinformation|misinfo)|anti.?vax).{0,80}"
            r"(misinform|false|disinform|rumou?r|doubt|hesitancy)",
        ),
        (
            "offensive_capability_primary",
            r"primary[_\s-]?purpose.{0,40}(offensive|weapon|attack|exploit)|"
            r"(offensive|weaponiz|exploit).{0,40}(primary|main).{0,20}(purpose|goal|objective)",
        ),
    ]
)

_REAL_POLITICAL_EVENT_RE = re.compile(
    r"(election|vote|ballot|referendum|inaugurat|protest|riot|coup|assassinat|"
    r"impeach|summit|debate)",
    re.IGNORECASE,
)


def _flatten_text(scenario: dict) -> str:
    """Normalize a scenario dict into searchable lowercase text."""
    return json.dumps(scenario, sort_keys=True, default=str).lower()


def _within_days(date_value: Any, days: int, now: datetime) -> bool:
    """Best-effort check whether a scenario date is within `days` of now."""
    if not date_value:
        return False
    try:
        if isinstance(date_value, datetime):
            dt = date_value if date_value.tzinfo else date_value.replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(date_value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return abs((now - dt).days) < days
    except (ValueError, TypeError):
        return False


def _scenario_dates(scenario: dict) -> Iterable[Any]:
    """Yield plausible date fields from a scenario (several common keys)."""
    for key in ("date", "event_date", "scheduled_date", "run_date", "timestamp"):
        if key in scenario:
            yield scenario[key]
    for key in ("event", "scenario", "context"):
        sub = scenario.get(key)
        if isinstance(sub, dict):
            for k in ("date", "event_date", "scheduled_date"):
                if k in sub:
                    yield sub[k]


class ScenarioGate:
    """Ethics review gate run before any simulation.

    Usage:
        gate = ScenarioGate()
        decision = gate.review_scenario(scenario_dict)
        if decision.decision is Decision.DENY:
            ...
    """

    RECENT_EVENT_WINDOW_DAYS = 30

    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime.now(timezone.utc)

    def review_scenario(self, scenario: dict) -> GateDecision:
        text = _flatten_text(scenario)

        # Hard denials first.
        deny_reasons = [
            f"prohibited_pattern:{name}"
            for name, rx in _PROHIBITED_PATTERNS
            if rx.search(text)
        ]
        if deny_reasons:
            return GateDecision(Decision.DENY, tuple(deny_reasons))

        # Escalation triggers.
        escalate_reasons: list[str] = []
        escalate_reasons += [
            f"escalation:{name}"
            for name, rx in _ESCALATION_PATTERNS
            if rx.search(text)
        ]

        # Real political events < 30 days away (or recently past).
        recent = any(_within_days(d, self.RECENT_EVENT_WINDOW_DAYS, self._now) for d in _scenario_dates(scenario))
        if recent and _REAL_POLITICAL_EVENT_RE.search(text):
            escalate_reasons.append(
                f"escalation:real_political_event_within_{self.RECENT_EVENT_WINDOW_DAYS}d"
            )

        if escalate_reasons:
            return GateDecision(Decision.ESCALATE, tuple(escalate_reasons))
        return GateDecision(Decision.ALLOW)


# ---------------------------------------------------------------------------
# 3. AuditLedger — append-only hash-chained JSONL log
# ---------------------------------------------------------------------------

_GENESIS_HASH = "0" * 64


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditRecord:
    seq: int
    timestamp: str
    actor: str
    action: str
    params_hash: str
    output_hash: str
    prev_hash: str
    record_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "params_hash": self.params_hash,
            "output_hash": self.output_hash,
            "prev_hash": self.prev_hash,
        }

    def compute_hash(self) -> str:
        return _sha256(_canonical(self.payload()))


class AuditLedger:
    """Append-only, hash-chained audit log persisted as JSONL.

    Each record links to the previous via ``prev_hash``; ``verify()``
    recomputes the chain and detects tampering or gaps.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records = self._load()

    # -- internals ---------------------------------------------------------

    def _load(self) -> list[AuditRecord]:
        records: list[AuditRecord] = []
        if not self.path.exists():
            return records
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(AuditRecord(**json.loads(line)))
        return records

    def _persist(self, rec: AuditRecord) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(_canonical(asdict(rec)) + "\n")

    # -- public API --------------------------------------------------------

    @property
    def head_hash(self) -> str:
        return self._records[-1].record_hash if self._records else _GENESIS_HASH

    @property
    def length(self) -> int:
        return len(self._records)

    def records(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)

    def append(
        self,
        actor: str,
        action: str,
        params: Any = None,
        output: Any = None,
        timestamp: datetime | None = None,
    ) -> AuditRecord:
        """Append a new record to the chain and persist it."""
        prev = self.head_hash
        payload_core = {
            "seq": len(self._records) + 1,
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "actor": actor,
            "action": action,
            "params_hash": _sha256(_canonical(params)),
            "output_hash": _sha256(_canonical(output)),
            "prev_hash": prev,
        }
        rec = AuditRecord(record_hash=_sha256(_canonical(payload_core)), **payload_core)
        self._records.append(rec)
        self._persist(rec)
        return rec

    def verify(self) -> tuple[bool, str | None]:
        """Verify chain integrity. Returns (ok, error_message)."""
        prev = _GENESIS_HASH
        for i, rec in enumerate(self._records):
            if rec.seq != i + 1:
                return False, f"seq gap at index {i}: expected {i + 1}, got {rec.seq}"
            if rec.prev_hash != prev:
                return False, f"prev_hash mismatch at seq {rec.seq}"
            if rec.record_hash != rec.compute_hash():
                return False, f"record_hash mismatch at seq {rec.seq}"
            prev = rec.record_hash
        return True, None


# ---------------------------------------------------------------------------
# 4. ProvenanceMarker — C2PA-compatible artifact metadata
# ---------------------------------------------------------------------------

HUMAN_LABEL = "AI-GENERATED SIMULATION OUTPUT — NOT REAL EVENTS OR PEOPLE"


@dataclass
class ProvenanceMarker:
    """C2PA-compatible provenance metadata attached to exported artifacts."""

    content_type: str = "application/json"
    synthetic: bool = True
    generator: str = f"mirofish/{_VER}"
    run_manifest_ref: str = ""
    watermark_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def c2pa_manifest(self) -> dict[str, Any]:
        """Render as a minimal C2PA-style manifest assertion."""
        return {
            "c2pa_version": "1.0",
            "assertions": [
                {
                    "label": "c2pa.actions",
                    "data": {
                        "actions": [
                            {
                                "action": "c2pa.created",
                                "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
                            }
                        ]
                    },
                },
                {
                    "label": "mirofish.provenance",
                    "data": self.to_dict(),
                },
            ],
            "human_label": HUMAN_LABEL,
        }


def mark_artifact(obj: dict, marker: ProvenanceMarker | None = None) -> dict:
    """Attach a provenance marker (and human-visible label) to an artifact dict.

    Mutates and returns ``obj`` for convenience; the marker is stored under
    ``obj["_provenance"]`` and the label under ``obj["_label"]``.
    """
    m = marker or ProvenanceMarker()
    obj["_provenance"] = m.to_dict()
    obj["_label"] = HUMAN_LABEL
    return obj


# ---------------------------------------------------------------------------
# 5. DataProvenance — per-run registry of data sources with legality tags
# ---------------------------------------------------------------------------


class SourceLegality(str, Enum):
    PUBLIC_FIREHOSE = "public_firehose"
    RESEARCH_API = "research_api"
    OPT_IN = "opt_in"
    AGGREGATE_ONLY = "aggregate_only"
    PROPRIETARY_BLOCKED = "proprietary_blocked"


# Sources that must never enter a run.
_PROHIBITED_SOURCES: frozenset[str] = frozenset(
    {
        SourceLegality.PROPRIETARY_BLOCKED.value,
        "private_dms",            # private direct messages
        "credential_stuffing",
        "non_consensual_scrape",
        "purchased_pii",
        "leaked_dataset",
    }
)


class ProhibitedSourceError(PermissionError):
    """Raised when a prohibited data source is registered or asserted."""


@dataclass
class DataSource:
    name: str
    legality: str
    description: str = ""
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DataProvenance:
    """Per-run registry of data sources; enforces legality tags."""

    def __init__(self, run_id: str = "") -> None:
        self.run_id = run_id
        self._sources: dict[str, DataSource] = {}

    def register(self, name: str, legality: str | SourceLegality, description: str = "") -> DataSource:
        """Register a source. Raises ProhibitedSourceError on blocked sources."""
        leg = legality.value if isinstance(legality, SourceLegality) else str(legality)
        self.assert_legal(leg)
        src = DataSource(name=name, legality=leg, description=description)
        self._sources[name] = src
        return src

    def assert_legal(self, source: str | SourceLegality) -> None:
        """Raise ProhibitedSourceError if the source tag is prohibited."""
        tag = source.value if isinstance(source, SourceLegality) else str(source)
        if tag in _PROHIBITED_SOURCES:
            raise ProhibitedSourceError(
                f"prohibited data source '{tag}': private/personal data may not be used"
            )

    def sources(self) -> tuple[DataSource, ...]:
        return tuple(self._sources.values())

    def manifest(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "sources": [s.to_dict() for s in self._sources.values()],
        }

    def to_dict(self) -> dict[str, Any]:
        return self.manifest()
