"""GateGraph Governance Archive (v0.8.45). Append-only historical storage; no decision feedback."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping
from src.governance_drift_compare import assert_descriptive_drift_payload
try:
    from src.version import current_schema_version
except Exception:
    def current_schema_version() -> str: return "0.8.45"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_LOG = PROJECT_ROOT / "operator_logs" / "governance_archive.jsonl"
ALLOWED_RECORD_KINDS = {"governance_snapshot","drift_comparison","drift_event","workflow_snapshot","queue_correlation","audit_event","operator_workflow_event","human_review_queue_event"}
def _utc_now() -> str: return datetime.now(timezone.utc).isoformat()
def _canonical(payload: Any) -> str: return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
def _sha256(payload: Any) -> str: return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
def read_archive_records(archive_path: Path | str = DEFAULT_ARCHIVE_LOG) -> List[Dict[str, Any]]:
    path = Path(archive_path)
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
def create_archive_record(record_kind: str, payload: Mapping[str, Any], *, timestamp: str | None = None, source_ref: str | None = None) -> Dict[str, Any]:
    kind = str(record_kind)
    if kind not in ALLOWED_RECORD_KINDS: raise ValueError(f"unsupported archive record kind: {kind}")
    payload_copy = json.loads(json.dumps(payload, sort_keys=True, default=str))
    if not assert_descriptive_drift_payload(payload_copy): raise ValueError("non-descriptive archive payload detected")
    core: Dict[str, Any] = {"archive_schema_version": current_schema_version(), "archive_mode": "historical_record_archive", "record_kind": kind, "timestamp": timestamp or _utc_now(), "payload_hash": _sha256(payload_copy), "payload": payload_copy}
    if source_ref is not None: core["source_ref"] = str(source_ref)
    record = dict(core); record["record_id"] = _sha256(core); return record
def append_archive_records(records: Iterable[Mapping[str, Any]], *, archive_path: Path | str = DEFAULT_ARCHIVE_LOG) -> List[Dict[str, Any]]:
    path = Path(archive_path); path.parent.mkdir(parents=True, exist_ok=True)
    sequence = len(read_archive_records(path)) + 1; written: List[Dict[str, Any]] = []
    with path.open("a", encoding="utf-8") as handle:
        for offset, record in enumerate(records):
            envelope = json.loads(json.dumps(record, sort_keys=True, default=str)); envelope["archive_sequence"] = sequence + offset
            if not assert_descriptive_drift_payload(envelope): raise ValueError("non-descriptive archive record detected")
            handle.write(json.dumps(envelope, sort_keys=True) + "\n"); written.append(envelope)
    return written
def archive_payloads(payloads: Iterable[Mapping[str, Any]], *, record_kind: str, archive_path: Path | str = DEFAULT_ARCHIVE_LOG, timestamp: str | None = None, source_ref: str | None = None) -> List[Dict[str, Any]]:
    return append_archive_records((create_archive_record(record_kind, p, timestamp=timestamp, source_ref=source_ref) for p in payloads), archive_path=archive_path)
