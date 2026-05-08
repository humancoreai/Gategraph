"""
GateGraph Governance Drift Log (v0.8.44)

Append-only record of observed distribution changes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping

from src.governance_drift_compare import assert_descriptive_drift_payload

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRIFT_LOG = PROJECT_ROOT / "operator_logs" / "governance_drift_events.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_drift_events(
    comparison: Mapping[str, Any],
    *,
    drift_log_path: Path | str = DEFAULT_DRIFT_LOG,
    timestamp: str | None = None,
) -> List[Dict[str, Any]]:
    """Append one descriptive event per distribution change."""
    if not assert_descriptive_drift_payload(comparison):
        raise ValueError("non-descriptive drift comparison payload detected")

    path = Path(drift_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    events: List[Dict[str, Any]] = []
    existing_count = 0
    if path.exists():
        existing_count = len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])

    with path.open("a", encoding="utf-8") as handle:
        for offset, change in enumerate(comparison.get("distribution_changes", []), start=1):
            event = {
                "event_id": f"drift-event-{existing_count + offset:012d}",
                "timestamp": timestamp or _utc_now(),
                "event_mode": "descriptive_change_record",
                "comparison_id": comparison.get("comparison_id"),
                "observed_change": dict(change),
            }
            if not assert_descriptive_drift_payload(event):
                raise ValueError("non-descriptive drift event payload detected")
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            events.append(event)
    return events


def read_drift_events(drift_log_path: Path | str = DEFAULT_DRIFT_LOG) -> List[Dict[str, Any]]:
    path = Path(drift_log_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
