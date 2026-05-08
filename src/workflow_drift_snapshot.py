"""Workflow drift snapshot: descriptive workflow distribution only."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from src.governance_drift_snapshot import create_governance_baseline_snapshot


def create_workflow_drift_snapshot(events: Iterable[Mapping[str, Any]], *, timestamp: str | None = None) -> Dict[str, Any]:
    snapshot = create_governance_baseline_snapshot(events, timestamp=timestamp)
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "timestamp": snapshot["timestamp"],
        "schema_version": snapshot["schema_version"],
        "snapshot_mode": "workflow_distribution_snapshot",
        "workflow_distribution": snapshot["workflow_distribution"],
    }
