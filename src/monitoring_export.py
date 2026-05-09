"""
WHY: Monitoring export provides one read-only operational view for humans or external tooling.
INV: Export observes state only; it never repairs, acknowledges, resolves, allows, or blocks.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "0.8.30"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _copy_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy_value(v) for v in value]
    return value


def build_monitoring_export(*, budget_snapshot: Any, incidents: list[Any], alerts: list[Any], aggregated_alerts: list[dict[str, Any]]) -> dict[str, Any]:
    budget_copy = _copy_value(budget_snapshot)
    incidents_copy = [_copy_value(incident) for incident in incidents]
    alerts_copy = [_copy_value(alert) for alert in alerts]
    aggregated_copy = [_copy_value(alert) for alert in aggregated_alerts]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "budget_snapshot": budget_copy,
        "incidents": incidents_copy,
        "alerts": alerts_copy,
        "aggregated_alerts": aggregated_copy,
        "summary": {
            "incident_count": len(incidents_copy),
            "open_incidents": sum(1 for incident in incidents_copy if incident.get("state") == "open"),
            "alert_count": len(alerts_copy),
            "critical_alerts": sum(1 for alert in alerts_copy if alert.get("severity") == "critical"),
            "aggregated_alert_count": len(aggregated_copy),
        },
    }
