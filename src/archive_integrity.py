"""GateGraph Archive Integrity / Replay Consistency (v0.8.46).

Checks archived envelopes and replay reconstruction without executing governance logic.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping

from src.governance_replay import build_historical_replay
from src.governance_drift_compare import assert_descriptive_drift_payload


def _canonical_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _sort_key(record: Mapping[str, Any]) -> tuple[str, int, str]:
    return (str(record.get("timestamp", "")), int(record.get("archive_sequence", 0) or 0), str(record.get("record_id", "")))


def _record_core(record: Mapping[str, Any]) -> Dict[str, Any]:
    copy = dict(record)
    copy.pop("archive_sequence", None)
    copy.pop("record_id", None)
    return copy


def verify_archive_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Describe envelope/hash observations for one archive record."""
    payload = record.get("payload", {})
    payload_hash = record.get("payload_hash")
    record_id = record.get("record_id")
    observed = {
        "record_id": record_id,
        "record_kind": record.get("record_kind"),
        "archive_sequence": record.get("archive_sequence"),
        "payload_hash_observed": payload_hash == _canonical_hash(payload),
        "record_id_observed": record_id == _canonical_hash(_record_core(record)),
        "descriptive_payload_observed": assert_descriptive_drift_payload(payload),
    }
    if not assert_descriptive_drift_payload(observed):
        raise ValueError("non-descriptive archive integrity payload detected")
    return observed


def verify_archive_sequence(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    materialized = sorted([dict(r) for r in records], key=_sort_key)
    sequences: List[int] = []
    for record in materialized:
        try:
            sequences.append(int(record.get("archive_sequence", 0) or 0))
        except (TypeError, ValueError):
            sequences.append(0)
    expected = list(range(1, len(materialized) + 1))
    observed = {
        "record_count": len(materialized),
        "archive_sequences": sequences,
        "expected_archive_sequences": expected,
        "archive_sequence_observed": sequences == expected,
    }
    if not assert_descriptive_drift_payload(observed):
        raise ValueError("non-descriptive archive sequence payload detected")
    return observed


def verify_replay_consistency(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    materialized = [dict(r) for r in records]
    replay_forward = build_historical_replay(materialized)
    replay_reverse = build_historical_replay(list(reversed(materialized)))
    observed = {
        "replay_mode": "historical_archive_reconstruction_consistency",
        "record_count": len(materialized),
        "replay_id_forward": replay_forward.get("replay_id"),
        "replay_id_reverse": replay_reverse.get("replay_id"),
        "replay_order_observed": replay_forward == replay_reverse,
        "payload_hashes_observed": all(item.get("payload_hash_verified") is True for item in replay_forward.get("timeline", [])),
    }
    if not assert_descriptive_drift_payload(observed):
        raise ValueError("non-descriptive replay consistency payload detected")
    return observed


def build_archive_integrity_report(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    materialized = sorted([dict(r) for r in records], key=_sort_key)
    report = {
        "archive_integrity_mode": "descriptive_archive_integrity_report",
        "record_count": len(materialized),
        "sequence_observation": verify_archive_sequence(materialized),
        "record_observations": [verify_archive_record(r) for r in materialized],
        "replay_observation": verify_replay_consistency(materialized),
        "schema_versions_observed": sorted({str(r.get("archive_schema_version")) for r in materialized}),
    }
    report["archive_integrity_report_id"] = _canonical_hash(report)
    if not assert_descriptive_drift_payload(report):
        raise ValueError("non-descriptive archive integrity report detected")
    return report
