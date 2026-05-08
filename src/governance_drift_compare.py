"""
GateGraph Governance Drift Comparison (v0.8.44)

Compares two descriptive snapshots without assigning meaning to differences.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping

DIMENSIONS = (
    "reason_distribution",
    "guard_distribution",
    "queue_distribution",
    "workflow_distribution",
)

FORBIDDEN_DRIFT_FIELDS = {
    "severity",
    "risk_level",
    "requires_attention",
    "recommended_action",
    "recommendation",
    "priority",
    "score",
    "root_cause",
    "cause",
    "likely_cause",
    "trigger",
    "alert",
}

FORBIDDEN_DRIFT_TERMS = {
    "critical",
    "dangerous",
    "problematic",
    "anomaly",
    "anomalous",
    "unstable",
    "suspicious",
    "urgent",
    "bad",
    "worse",
    "best",
}


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _entry_ratio(distribution: Mapping[str, Any], key: str) -> float:
    value = distribution.get(key, {})
    if isinstance(value, Mapping):
        return float(value.get("ratio", 0.0) or 0.0)
    return float(value or 0.0)


def assert_descriptive_drift_payload(payload: Any) -> bool:
    """Return True when a drift payload contains only descriptive schema language."""
    def walk(value: Any, *, parent_key: str | None = None) -> bool:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                key_text = str(key).lower()
                if key_text in FORBIDDEN_DRIFT_FIELDS or key_text in FORBIDDEN_DRIFT_TERMS:
                    return False
                if not walk(nested, parent_key=key_text):
                    return False
        elif isinstance(value, list):
            for item in value:
                if not walk(item, parent_key=parent_key):
                    return False
        elif isinstance(value, str):
            if parent_key in {"reason_code", "guard", "queue_type", "workflow_type", "key"}:
                return True
            text = value.lower()
            if text in FORBIDDEN_DRIFT_FIELDS or text in FORBIDDEN_DRIFT_TERMS:
                return False
        return True

    return walk(payload)


def compare_governance_snapshots(
    snapshot_a: Mapping[str, Any],
    snapshot_b: Mapping[str, Any],
    *,
    comparison_label: str | None = None,
) -> Dict[str, Any]:
    """Compare two snapshots using ratios only and stable key ordering."""
    changes: List[Dict[str, Any]] = []
    for dimension in DIMENSIONS:
        dist_a = snapshot_a.get(dimension, {}) or {}
        dist_b = snapshot_b.get(dimension, {}) or {}
        keys = sorted(set(dist_a.keys()) | set(dist_b.keys()))
        for key in keys:
            before = _entry_ratio(dist_a, key)
            after = _entry_ratio(dist_b, key)
            changes.append(
                {
                    "dimension": dimension,
                    "key": str(key),
                    "before": before,
                    "after": after,
                    "delta": after - before,
                    "presence": "both" if key in dist_a and key in dist_b else ("snapshot_a_only" if key in dist_a else "snapshot_b_only"),
                }
            )

    core: Dict[str, Any] = {
        "comparison_mode": "descriptive_snapshot_comparison",
        "snapshot_a": snapshot_a.get("snapshot_id"),
        "snapshot_b": snapshot_b.get("snapshot_id"),
        "distribution_changes": changes,
    }
    if comparison_label is not None:
        core["comparison_label"] = str(comparison_label)
    result = dict(core)
    result["comparison_id"] = _canonical_hash(core)
    if not assert_descriptive_drift_payload(result):
        raise ValueError("non-descriptive drift payload field detected")
    return result
