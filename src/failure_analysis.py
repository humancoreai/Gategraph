"""
GateGraph Failure Analysis / Postmortem Layer (v0.8.41)

Read-only, descriptive analysis helpers for operator-facing postmortem views.

INV:
- No Governance, Enforcement, Runtime, Budget or Audit mutation.
- No root-cause claims.
- No ranking/scoring/priority semantics.
- No ML, heuristic weighting or recommendation output.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


_INTERPRETATION_TERMS = (
    "root_cause",
    "root cause",
    "recommendation",
    "recommended",
    "priority",
    "important",
    "criticality",
    "severity_rank",
    "score",
    "rank",
    "top",
)


def _safe_get(event: Mapping[str, Any], key: str, default: Any = None) -> Any:
    return event.get(key, default) if isinstance(event, Mapping) else default


def _normalized_reason(event: Mapping[str, Any]) -> Mapping[str, Any]:
    value = _safe_get(event, "normalized_reason", {})
    return value if isinstance(value, Mapping) else {}


def reason_code(event: Mapping[str, Any]) -> str:
    reason = _normalized_reason(event)
    code = reason.get("code")
    if code:
        return str(code)
    raw = _safe_get(event, "reason")
    return str(raw) if raw else "UNSPECIFIED_REASON"


def guard_name(event: Mapping[str, Any]) -> str:
    guard = _safe_get(event, "guard") or _safe_get(event, "stage") or _safe_get(event, "triggering_guard")
    return str(guard) if guard else "UNSPECIFIED_GUARD"


def decision_value(event: Mapping[str, Any]) -> str:
    decision = _safe_get(event, "decision") or _safe_get(event, "status")
    return str(decision) if decision else "UNSPECIFIED_DECISION"


def task_id(event: Mapping[str, Any]) -> str:
    value = _safe_get(event, "task_id")
    return str(value) if value else "UNSPECIFIED_TASK"


def timestamp_value(event: Mapping[str, Any]) -> Optional[str]:
    value = _safe_get(event, "timestamp") or _safe_get(event, "created_at") or _safe_get(event, "generated_at")
    return str(value) if value else None


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _time_bucket(value: Optional[str], bucket: str = "hour") -> str:
    parsed = _parse_timestamp(value)
    if parsed is None:
        return "UNSPECIFIED_TIME"

    if bucket == "day":
        return parsed.strftime("%Y-%m-%d")
    if bucket == "minute":
        return parsed.strftime("%Y-%m-%dT%H:%MZ")
    return parsed.strftime("%Y-%m-%dT%HZ")


def _counter_to_plain(counter: Counter) -> Dict[str, int]:
    # INV: alphabetic key order only; no frequency ranking semantics.
    return {str(key): int(counter[key]) for key in sorted(counter.keys(), key=lambda item: str(item))}


def count_by_reason(events: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    return _counter_to_plain(Counter(reason_code(event) for event in events))


def count_by_guard(events: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    return _counter_to_plain(Counter(guard_name(event) for event in events))


def count_by_guard_and_reason(events: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    pairs = Counter(f"{guard_name(event)}|{reason_code(event)}" for event in events)
    return _counter_to_plain(pairs)


def time_distribution(events: Iterable[Mapping[str, Any]], bucket: str = "hour") -> Dict[str, int]:
    buckets = Counter(_time_bucket(timestamp_value(event), bucket=bucket) for event in events)
    return _counter_to_plain(buckets)


def pattern_detection(events: Iterable[Mapping[str, Any]], bucket: str = "hour") -> Dict[str, Any]:
    event_list = list(events)
    return {
        "case_count": len(event_list),
        "reason_code_counts": count_by_reason(event_list),
        "guard_counts": count_by_guard(event_list),
        "guard_reason_counts": count_by_guard_and_reason(event_list),
        "time_distribution": time_distribution(event_list, bucket=bucket),
        "analysis_mode": "descriptive_only",
    }


def compare_decisions(events: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    event_list = list(events)
    groups: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for event in event_list:
        groups[decision_value(event)].append(event)

    return {
        "case_count": len(event_list),
        "decision_groups": {
            decision: {
                "case_count": len(group),
                "reason_code_counts": count_by_reason(group),
                "guard_counts": count_by_guard(group),
            }
            for decision, group in sorted(groups.items())
        },
        "analysis_mode": "descriptive_only",
    }


def compare_guards(events: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    event_list = list(events)
    groups: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for event in event_list:
        groups[guard_name(event)].append(event)

    return {
        "case_count": len(event_list),
        "guard_groups": {
            guard: {
                "case_count": len(group),
                "decision_counts": _counter_to_plain(Counter(decision_value(item) for item in group)),
                "reason_code_counts": count_by_reason(group),
            }
            for guard, group in sorted(groups.items())
        },
        "analysis_mode": "descriptive_only",
    }


def decision_sequences(events: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[task_id(event)].append(event)

    sequences = Counter()
    for _, group in grouped.items():
        ordered = sorted(group, key=lambda item: timestamp_value(item) or "")
        sequence = " -> ".join(decision_value(item) for item in ordered)
        sequences[sequence or "UNSPECIFIED_SEQUENCE"] += 1

    return _counter_to_plain(sequences)


def failure_clusters(events: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    event_list = list(events)
    grouped: Dict[Tuple[str, str, str], List[Mapping[str, Any]]] = defaultdict(list)

    for event in event_list:
        grouped[(reason_code(event), guard_name(event), decision_value(event))].append(event)

    clusters = []
    for (reason, guard, decision), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])):
        clusters.append({
            "reason_code": reason,
            "guard": guard,
            "decision": decision,
            "case_count": len(group),
            "grouping_basis": ["normalized_reason.code", "guard", "decision"],
        })

    return {
        "case_count": len(event_list),
        "clusters": clusters,
        "analysis_mode": "descriptive_grouping_only",
    }


def postmortem_view(
    events: Iterable[Mapping[str, Any]],
    *,
    guard: Optional[str] = None,
    reason: Optional[str] = None,
    decision: Optional[str] = None,
    bucket: str = "hour",
) -> Dict[str, Any]:
    event_list = list(events)

    filtered = [
        event
        for event in event_list
        if (guard is None or guard_name(event) == guard)
        and (reason is None or reason_code(event) == reason)
        and (decision is None or decision_value(event) == decision)
    ]

    return {
        "filters": {
            "guard": guard,
            "reason": reason,
            "decision": decision,
        },
        "case_count": len(filtered),
        "reason_code_counts": count_by_reason(filtered),
        "guard_counts": count_by_guard(filtered),
        "decision_sequence_counts": decision_sequences(filtered),
        "time_distribution": time_distribution(filtered, bucket=bucket),
        "analysis_mode": "descriptive_only",
    }


def timeline_correlation(events: Iterable[Mapping[str, Any]], bucket: str = "hour") -> Dict[str, Any]:
    event_list = list(events)
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)

    for event in event_list:
        grouped[_time_bucket(timestamp_value(event), bucket=bucket)].append(event)

    buckets = {}
    for bucket_key, group in sorted(grouped.items()):
        cost_values = []
        runtime_values = []

        for event in group:
            cost = _safe_get(event, "cost") or _safe_get(event, "cost_units")
            runtime = _safe_get(event, "runtime_seconds")

            if isinstance(cost, (int, float)):
                cost_values.append(cost)
            if isinstance(runtime, (int, float)):
                runtime_values.append(runtime)

        buckets[bucket_key] = {
            "case_count": len(group),
            "reason_code_counts": count_by_reason(group),
            "guard_counts": count_by_guard(group),
            "cost_values": cost_values,
            "runtime_seconds_values": runtime_values,
        }

    return {
        "case_count": len(event_list),
        "time_buckets": buckets,
        "analysis_mode": "descriptive_correlation_view_only",
    }


def assert_no_interpretation_labels(payload: Any) -> bool:
    """Return True when output keys avoid interpretation / ranking language.

    INV: Uses tokenized key checks, not substring checks.
    Example: "stop" must not be rejected just because it contains "top".
    """
    blocked_terms = set(_INTERPRETATION_TERMS)

    def key_tokens(key: Any) -> set:
        key_text = str(key).lower()
        return {token for token in key_text.replace("-", "_").split("_") if token}

    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                tokens = key_tokens(key)
                key_text = str(key).lower()
                if key_text in blocked_terms or tokens.intersection(blocked_terms):
                    return False
                if not walk(nested):
                    return False
        elif isinstance(value, list):
            for item in value:
                if not walk(item):
                    return False
        return True

    return walk(payload)


__all__ = [
    "count_by_reason",
    "count_by_guard",
    "count_by_guard_and_reason",
    "time_distribution",
    "pattern_detection",
    "compare_decisions",
    "compare_guards",
    "decision_sequences",
    "failure_clusters",
    "postmortem_view",
    "timeline_correlation",
    "assert_no_interpretation_labels",
]
