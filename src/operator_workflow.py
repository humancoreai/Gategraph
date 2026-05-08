"""
GateGraph Operator Workflow / Playbook Layer (v0.8.42)

Read-only operator-facing workflow helpers for linking detected patterns to
static playbook definitions and documenting human workflow steps.

INV:
- No Governance, Enforcement, Runtime, Budget or Audit mutation.
- No automatic action, escalation, policy tuning or rule update.
- No ranking, scoring, priority or recommendation semantics.
- Workflow logs are operator documentation only and do not affect decisions.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

_BLOCKED_LABEL_TERMS = {
    "root_cause",
    "root cause",
    "recommendation",
    "recommended",
    "priority",
    "prioritized",
    "rank",
    "ranking",
    "score",
    "scoring",
    "severity",
    "best",
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAYBOOK_DIR = PROJECT_ROOT / "playbooks"
DEFAULT_WORKFLOW_LOG = PROJECT_ROOT / "operator_logs" / "workflow_events.jsonl"


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


def assert_no_workflow_interpretation_labels(payload: Any) -> bool:
    """Return True when keys and string values avoid interpretation language.

    INV: This checker protects the workflow layer from quietly becoming a
    recommendation layer. It intentionally checks strings as well as keys.
    """
    blocked_tokens = {_token for term in _BLOCKED_LABEL_TERMS for _token in _token_set(term)}

    def blocked(value: Any) -> bool:
        text = str(value).lower()
        if text in _BLOCKED_LABEL_TERMS:
            return True
        tokens = _token_set(text)
        return bool(tokens.intersection(blocked_tokens))

    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if blocked(key):
                    return False
                if not walk(nested):
                    return False
        elif isinstance(value, list):
            for item in value:
                if not walk(item):
                    return False
        elif isinstance(value, str):
            if blocked(value):
                return False
        return True

    return walk(payload)


def normalize_playbook(raw: Mapping[str, Any], *, source: Optional[str] = None) -> Dict[str, Any]:
    trigger = raw.get("trigger", {}) if isinstance(raw.get("trigger", {}), Mapping) else {}
    playbook = {
        "playbook_id": str(raw.get("playbook_id", "")),
        "version": str(raw.get("version", "1.0")),
        "trigger": {
            "reason_codes": sorted(set(_as_list(trigger.get("reason_codes") or trigger.get("reason_code")))),
            "guards": sorted(set(_as_list(trigger.get("guards") or trigger.get("guard")))),
        },
        "steps": _as_list(raw.get("steps")),
        "notes": str(raw.get("notes", "")),
    }
    if source:
        playbook["source"] = source
    if not playbook["playbook_id"]:
        raise ValueError("playbook_id is required")
    if not assert_no_workflow_interpretation_labels(playbook):
        raise ValueError(f"interpretation label detected in {playbook['playbook_id']}")
    return playbook


def load_playbooks(playbook_dir: Path | str = DEFAULT_PLAYBOOK_DIR) -> List[Dict[str, Any]]:
    directory = Path(playbook_dir)
    playbooks: List[Dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        playbooks.append(normalize_playbook(raw, source=str(path.relative_to(PROJECT_ROOT))))
    return playbooks


def match_playbooks(
    *,
    reason_code: Optional[str] = None,
    guard: Optional[str] = None,
    playbooks: Optional[Iterable[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Return all descriptive playbook links matching reason and/or guard.

    INV: Alphabetic playbook_id order only; no match ranking, score or selection.
    """
    loaded = [normalize_playbook(item) for item in (playbooks if playbooks is not None else load_playbooks())]
    matches: List[Dict[str, Any]] = []
    for playbook in loaded:
        trigger = playbook["trigger"]
        reason_match = reason_code is not None and str(reason_code) in trigger["reason_codes"]
        guard_match = guard is not None and str(guard) in trigger["guards"]
        if reason_match or guard_match:
            basis = []
            if reason_match:
                basis.append("reason_code")
            if guard_match:
                basis.append("guard")
            matches.append({
                "playbook_id": playbook["playbook_id"],
                "matched_on": basis,
            })

    result = {
        "query": {"reason_code": reason_code, "guard": guard},
        "matches": sorted(matches, key=lambda item: item["playbook_id"]),
        "match_mode": "descriptive_mapping_only",
    }
    if not assert_no_workflow_interpretation_labels(result):
        raise ValueError("interpretation label detected in match output")
    return result


def append_workflow_event(
    *,
    playbook_id: str,
    task_id: Optional[str] = None,
    filter_ref: Optional[Mapping[str, Any]] = None,
    steps_observed: Optional[Sequence[str]] = None,
    operator_comment: Optional[str] = None,
    log_path: Path | str = DEFAULT_WORKFLOW_LOG,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Append an operator documentation event to a JSONL log.

    INV: This function writes only to the operator workflow log path provided.
    It never calls or mutates Governance, Enforcement, Runtime, Budget or Audit.
    """
    event = {
        "timestamp": timestamp or _utc_now(),
        "playbook_id": str(playbook_id),
        "task_id": str(task_id) if task_id is not None else None,
        "filter": dict(filter_ref or {}),
        "steps_observed": _as_list(steps_observed),
        "operator_comment": str(operator_comment) if operator_comment is not None else None,
        "effect": "documentation_only",
    }
    canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
    event["event_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    if not assert_no_workflow_interpretation_labels({k: v for k, v in event.items() if k != "operator_comment"}):
        raise ValueError("interpretation label detected in workflow event")

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def read_workflow_events(log_path: Path | str = DEFAULT_WORKFLOW_LOG) -> List[Dict[str, Any]]:
    path = Path(log_path)
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def link_incident_playbooks(
    *,
    incident_id: str,
    pattern_id: Optional[str] = None,
    reason_code: Optional[str] = None,
    guard: Optional[str] = None,
    playbooks: Optional[Iterable[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    matched = match_playbooks(reason_code=reason_code, guard=guard, playbooks=playbooks)
    result = {
        "incident_id": str(incident_id),
        "pattern_id": str(pattern_id) if pattern_id is not None else None,
        "reason_code": reason_code,
        "guard": guard,
        "linked_playbooks": [item["playbook_id"] for item in matched["matches"]],
        "link_mode": "reference_only",
    }
    if not assert_no_workflow_interpretation_labels(result):
        raise ValueError("interpretation label detected in incident link")
    return result


def workflow_snapshot(
    *,
    pattern_id: Optional[str] = None,
    reason_code: Optional[str] = None,
    guard: Optional[str] = None,
    task_id: Optional[str] = None,
    log_path: Path | str = DEFAULT_WORKFLOW_LOG,
    playbooks: Optional[Iterable[Mapping[str, Any]]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    matched = match_playbooks(reason_code=reason_code, guard=guard, playbooks=playbooks)
    events = read_workflow_events(log_path)
    if task_id is not None:
        events = [event for event in events if event.get("task_id") == str(task_id)]
    playbook_ids = [item["playbook_id"] for item in matched["matches"]]
    snapshot_base = {
        "timestamp": timestamp or _utc_now(),
        "pattern_id": str(pattern_id) if pattern_id is not None else None,
        "reason_code": reason_code,
        "guard": guard,
        "task_id": str(task_id) if task_id is not None else None,
        "playbook_ids": playbook_ids,
        "workflow_events": events,
        "snapshot_mode": "reproducible_reference_view_only",
    }
    canonical = json.dumps(snapshot_base, sort_keys=True, separators=(",", ":"))
    snapshot_base["snapshot_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if not assert_no_workflow_interpretation_labels({k: v for k, v in snapshot_base.items() if k != "workflow_events"}):
        raise ValueError("interpretation label detected in workflow snapshot")
    return snapshot_base


__all__ = [
    "append_workflow_event",
    "assert_no_workflow_interpretation_labels",
    "link_incident_playbooks",
    "load_playbooks",
    "match_playbooks",
    "normalize_playbook",
    "read_workflow_events",
    "workflow_snapshot",
]
