"""
GateGraph Governance Drift Snapshot (v0.8.44)

Descriptive historical aggregation for governance structures.

INV:
- Read-only aggregation only.
- No policy, rule, guard, queue, runtime or decision mutation.
- No evaluation labels, score fields, recommendations or automatic reactions.
- Change visibility is descriptive; variation is not interpreted as a problem.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping

try:
    from src.version import current_schema_version
except Exception:  # pragma: no cover
    def current_schema_version() -> str:
        return "0.8.44"

DIMENSIONS = (
    "reason_distribution",
    "guard_distribution",
    "queue_distribution",
    "workflow_distribution",
)

_EVENT_FIELD_MAP = {
    "reason_distribution": ("reason_code", "reason", "normalized_reason"),
    "guard_distribution": ("guard", "guard_name", "guard_id"),
    "queue_distribution": ("queue_type", "queue", "review_queue", "queue_mode"),
    "workflow_distribution": ("workflow_type", "workflow", "workflow_id", "workflow_mode"),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _value_from_event(event: Mapping[str, Any], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        value = event.get(field)
        if value is not None and str(value) != "":
            return str(value)
    return None


def _ratio_distribution(counts: Mapping[str, int]) -> Dict[str, Dict[str, float | int]]:
    total = sum(int(value) for value in counts.values())
    result: Dict[str, Dict[str, float | int]] = {}
    for key in sorted(counts):
        count = int(counts[key])
        result[str(key)] = {"count": count, "ratio": (count / total if total else 0.0)}
    return result


def create_governance_baseline_snapshot(
    events: Iterable[Mapping[str, Any]],
    *,
    timestamp: str | None = None,
    snapshot_label: str | None = None,
) -> Dict[str, Any]:
    """Create a deterministic descriptive baseline snapshot from event-like mappings."""
    counters: Dict[str, Dict[str, int]] = {dimension: {} for dimension in DIMENSIONS}
    event_count = 0

    for event in events:
        event_count += 1
        for dimension, fields in _EVENT_FIELD_MAP.items():
            value = _value_from_event(event, fields)
            if value is None:
                continue
            counters[dimension][value] = counters[dimension].get(value, 0) + 1

    snapshot_core: Dict[str, Any] = {
        "timestamp": timestamp or _utc_now(),
        "schema_version": current_schema_version(),
        "snapshot_mode": "descriptive_distribution_snapshot",
        "event_count": event_count,
        "reason_distribution": _ratio_distribution(counters["reason_distribution"]),
        "guard_distribution": _ratio_distribution(counters["guard_distribution"]),
        "queue_distribution": _ratio_distribution(counters["queue_distribution"]),
        "workflow_distribution": _ratio_distribution(counters["workflow_distribution"]),
    }
    if snapshot_label is not None:
        snapshot_core["snapshot_label"] = str(snapshot_label)

    snapshot = dict(snapshot_core)
    snapshot["snapshot_id"] = _canonical_hash(snapshot_core)
    return snapshot
