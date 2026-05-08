"""Queue drift correlation view: descriptive co-occurrence counts only."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping


def queue_drift_correlation(events: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    matrix: Dict[str, Dict[str, int]] = {}
    total = 0
    for event in events:
        queue_type = event.get("queue_type") or event.get("queue") or event.get("queue_mode")
        reason_code = event.get("reason_code") or event.get("reason") or event.get("normalized_reason")
        if queue_type is None or reason_code is None:
            continue
        total += 1
        q = str(queue_type)
        r = str(reason_code)
        matrix.setdefault(q, {})[r] = matrix.setdefault(q, {}).get(r, 0) + 1
    return {
        "correlation_mode": "descriptive_cooccurrence_only",
        "event_count": total,
        "queue_reason_cooccurrence": {q: dict(sorted(values.items())) for q, values in sorted(matrix.items())},
    }
