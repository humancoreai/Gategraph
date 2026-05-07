"""GateGraph Governance Historical Replay (v0.8.45). Reconstructs archived records only."""
from __future__ import annotations
import hashlib, json
from typing import Any, Dict, Iterable, Mapping
from src.governance_archive import read_archive_records
from src.governance_drift_compare import assert_descriptive_drift_payload
def _hash(payload: Any) -> str: return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
def _sort_key(record: Mapping[str, Any]) -> tuple[str, int, str]: return (str(record.get("timestamp", "")), int(record.get("archive_sequence", 0) or 0), str(record.get("record_id", "")))
def build_historical_replay(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    timeline = []
    for index, record in enumerate(sorted([dict(r) for r in records], key=_sort_key), start=1):
        payload = record.get("payload", {}); payload_hash = record.get("payload_hash")
        timeline.append({"replay_index": index, "timestamp": record.get("timestamp"), "record_id": record.get("record_id"), "record_kind": record.get("record_kind"), "payload_hash": payload_hash, "payload_hash_verified": payload_hash == _hash(payload), "payload": payload})
    replay = {"replay_mode": "historical_archive_reconstruction", "record_count": len(timeline), "timeline": timeline}
    replay["replay_id"] = _hash(replay)
    if not assert_descriptive_drift_payload(replay): raise ValueError("non-descriptive replay payload detected")
    return replay
def replay_archive(archive_path: str) -> Dict[str, Any]: return build_historical_replay(read_archive_records(archive_path))
