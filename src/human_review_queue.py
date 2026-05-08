"""
GateGraph Human Review Queue (v0.8.43)

Read-only operator-facing queue references for human review work.

INV:
- No Governance, Enforcement, Runtime, Budget or Audit mutation.
- No automatic action, escalation, policy tuning or rule update.
- No priority, ranking, scoring, severity or recommendation semantics.
- Queue order is append order only; it has no evaluation meaning.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_QUEUE_LOG = PROJECT_ROOT / "operator_logs" / "human_review_queue.jsonl"
DEFAULT_REVIEW_ACTIVITY_LOG = PROJECT_ROOT / "operator_logs" / "human_review_activity.jsonl"

_BLOCKED_QUEUE_TERMS = {
    "priority",
    "prioritized",
    "rank",
    "ranking",
    "score",
    "scoring",
    "severity",
    "urgent",
    "importance",
    "best",
    "recommendation",
    "recommended",
    "root_cause",
    "root cause",
    "decision",
    "approve",
    "reject",
}

# External references may contain domain-specific strings. Queue semantics are
# protected by checking GateGraph-authored fields, not opaque operator comments.
_COMMENT_FIELDS = {"operator_comment", "human_note"}
_REFERENCE_VALUE_FIELDS = {
    "source_id",
    "task_id",
    "incident_id",
    "pattern_id",
    "reason_code",
    "guard",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _token_set(text: Any) -> set[str]:
    normalized = str(text).lower().replace("-", "_").replace(" ", "_")
    return {part for part in normalized.split("_") if part}


def assert_no_queue_prioritization_labels(payload: Any) -> bool:
    """Return True when queue-owned labels avoid hidden evaluation language.

    INV: This guards against the queue becoming a silent triage system. Opaque
    comments and external identifiers are not interpreted by this checker.
    """
    blocked_tokens = {token for term in _BLOCKED_QUEUE_TERMS for token in _token_set(term)}

    def blocked(value: Any) -> bool:
        text = str(value).lower()
        if text in _BLOCKED_QUEUE_TERMS:
            return True
        return bool(_token_set(text).intersection(blocked_tokens))

    def walk(value: Any, *, parent_key: Optional[str] = None) -> bool:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                key_text = str(key)
                if blocked(key_text):
                    return False
                if key_text in _COMMENT_FIELDS:
                    continue
                if key_text in _REFERENCE_VALUE_FIELDS and not isinstance(nested, Mapping):
                    continue
                if not walk(nested, parent_key=key_text):
                    return False
        elif isinstance(value, list):
            for item in value:
                if not walk(item, parent_key=parent_key):
                    return False
        elif isinstance(value, str):
            if parent_key not in _REFERENCE_VALUE_FIELDS and blocked(value):
                return False
        return True

    return walk(payload)


def _event_id(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def append_review_item(
    *,
    source_type: str,
    source_id: str,
    task_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    pattern_id: Optional[str] = None,
    reason_code: Optional[str] = None,
    guard: Optional[str] = None,
    playbook_ids: Optional[Sequence[str]] = None,
    operator_comment: Optional[str] = None,
    queue_log_path: Path | str = DEFAULT_REVIEW_QUEUE_LOG,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a human-review reference item.

    INV: Append-only documentation. No queue item can alter system behavior.
    EDGE: File order is the only queue order and has no evaluation meaning.
    """
    item = {
        "created_at": timestamp or _utc_now(),
        "source_type": str(source_type),
        "source_id": str(source_id),
        "task_id": str(task_id) if task_id is not None else None,
        "incident_id": str(incident_id) if incident_id is not None else None,
        "pattern_id": str(pattern_id) if pattern_id is not None else None,
        "reason_code": str(reason_code) if reason_code is not None else None,
        "guard": str(guard) if guard is not None else None,
        "playbook_ids": _as_list(playbook_ids),
        "operator_comment": str(operator_comment) if operator_comment is not None else None,
        "queue_mode": "human_review_reference_only",
        "order_semantics": "append_order_only",
        "effect": "documentation_only",
    }
    if not assert_no_queue_prioritization_labels(item):
        raise ValueError("prioritization or decision label detected in review item")
    item["review_item_id"] = _event_id(item)

    path = Path(queue_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True) + "\n")
    return item


def read_review_items(queue_log_path: Path | str = DEFAULT_REVIEW_QUEUE_LOG) -> List[Dict[str, Any]]:
    """Read queue items in append order only.

    INV: No sorting, grouping, scoring or filtering is applied here.
    """
    path = Path(queue_log_path)
    if not path.exists():
        return []
    items: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def filter_review_items_reference_only(
    *,
    items: Iterable[Mapping[str, Any]],
    task_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    pattern_id: Optional[str] = None,
    playbook_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return matching items while preserving original append order.

    INV: Filtering is reference matching only, never triage.
    """
    result_items: List[Dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        if task_id is not None and item.get("task_id") != str(task_id):
            continue
        if incident_id is not None and item.get("incident_id") != str(incident_id):
            continue
        if pattern_id is not None and item.get("pattern_id") != str(pattern_id):
            continue
        if playbook_id is not None and str(playbook_id) not in _as_list(item.get("playbook_ids")):
            continue
        result_items.append(item)
    output = {
        "items": result_items,
        "filter_mode": "reference_match_only",
        "order_semantics": "input_append_order_preserved",
    }
    if not assert_no_queue_prioritization_labels(output):
        raise ValueError("prioritization or decision label detected in filtered queue")
    return output


def append_review_activity(
    *,
    review_item_id: str,
    observed_steps: Optional[Sequence[str]] = None,
    linked_playbook_ids: Optional[Sequence[str]] = None,
    human_note: Optional[str] = None,
    activity_log_path: Path | str = DEFAULT_REVIEW_ACTIVITY_LOG,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Append human review activity documentation without outcome semantics."""
    activity = {
        "timestamp": timestamp or _utc_now(),
        "review_item_id": str(review_item_id),
        "observed_steps": _as_list(observed_steps),
        "linked_playbook_ids": _as_list(linked_playbook_ids),
        "human_note": str(human_note) if human_note is not None else None,
        "activity_mode": "documentation_only",
        "effect": "documentation_only",
    }
    if not assert_no_queue_prioritization_labels(activity):
        raise ValueError("prioritization or decision label detected in review activity")
    activity["activity_id"] = _event_id(activity)

    path = Path(activity_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(activity, sort_keys=True) + "\n")
    return activity


def read_review_activity(activity_log_path: Path | str = DEFAULT_REVIEW_ACTIVITY_LOG) -> List[Dict[str, Any]]:
    path = Path(activity_log_path)
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def human_review_queue_snapshot(
    *,
    queue_log_path: Path | str = DEFAULT_REVIEW_QUEUE_LOG,
    activity_log_path: Path | str = DEFAULT_REVIEW_ACTIVITY_LOG,
    task_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    pattern_id: Optional[str] = None,
    playbook_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    items = read_review_items(queue_log_path)
    filtered = filter_review_items_reference_only(
        items=items,
        task_id=task_id,
        incident_id=incident_id,
        pattern_id=pattern_id,
        playbook_id=playbook_id,
    )
    item_ids = {item.get("review_item_id") for item in filtered["items"]}
    activities = [event for event in read_review_activity(activity_log_path) if event.get("review_item_id") in item_ids]
    snapshot_base = {
        "timestamp": timestamp or _utc_now(),
        "filters": {
            "task_id": task_id,
            "incident_id": incident_id,
            "pattern_id": pattern_id,
            "playbook_id": playbook_id,
        },
        "review_items": filtered["items"],
        "review_activity": activities,
        "snapshot_mode": "human_review_reference_view_only",
        "order_semantics": "append_order_only",
    }
    if not assert_no_queue_prioritization_labels(snapshot_base):
        raise ValueError("prioritization or decision label detected in review snapshot")
    snapshot_base["snapshot_id"] = _event_id(snapshot_base)
    return snapshot_base


__all__ = [
    "append_review_activity",
    "append_review_item",
    "assert_no_queue_prioritization_labels",
    "filter_review_items_reference_only",
    "human_review_queue_snapshot",
    "read_review_activity",
    "read_review_items",
]
