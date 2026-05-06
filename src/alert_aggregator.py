"""
WHY: Alert aggregation reduces operational noise without adding a control path.
INV: Aggregation is deterministic, read-only, and preserves the highest severity seen.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _to_dict(alert: Any) -> dict[str, Any]:
    if is_dataclass(alert):
        return asdict(alert)
    return dict(alert)


def _max_severity(current: str, candidate: str) -> str:
    return current if SEVERITY_ORDER.get(current, -1) >= SEVERITY_ORDER.get(candidate, -1) else candidate


def aggregate_alerts(alerts: list[Any]) -> list[dict[str, Any]]:
    """Group alerts by exact operational cause.

    INV:
    - No mutation of input objects.
    - No fuzzy matching or heuristic merging.
    - Highest severity is preserved.
    """
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}

    for raw_alert in alerts:
        alert = _to_dict(raw_alert)
        key = (str(alert["reason_code"]), str(alert["trigger_type"]), str(alert["trigger_ref"]))
        created_at = str(alert["created_at"])
        severity = str(alert["severity"])

        if key not in buckets:
            buckets[key] = {
                "reason_code": key[0],
                "trigger_type": key[1],
                "trigger_ref": key[2],
                "severity": severity,
                "count": 1,
                "first_seen": created_at,
                "last_seen": created_at,
            }
            continue

        bucket = buckets[key]
        bucket["count"] += 1
        bucket["severity"] = _max_severity(str(bucket["severity"]), severity)
        if created_at < bucket["first_seen"]:
            bucket["first_seen"] = created_at
        if created_at > bucket["last_seen"]:
            bucket["last_seen"] = created_at

    return sorted(
        buckets.values(),
        key=lambda item: (-SEVERITY_ORDER.get(str(item["severity"]), -1), item["reason_code"], item["trigger_type"], item["trigger_ref"]),
    )
