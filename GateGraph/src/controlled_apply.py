"""
WHY: Controlled Apply is a narrow bridge from reviewed proposals to deterministic changes.
INV: no apply can run without an approved proposal, two distinct human gates, valid signature, TTL, and scope validation.
SEC: initial scope is intentionally tiny: rule changes may only make an existing rule stricter.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Mapping, Optional, Tuple

from src import event_logger

APPLY_SCHEMA_VERSION = "0.8.22"
DEFAULT_APPLY_TTL_SECONDS = 600
_ENV_APPLY_KEYRING_JSON = "GATEGRAPH_APPLY_KEYRING_JSON"
_ENV_APPLY_ACTIVE_KEY_ID = "GATEGRAPH_APPLY_ACTIVE_KEY_ID"
DEFAULT_APPLY_KEY_ID = "local-apply-dev-v1"
_DEV_APPLY_KEYRING = {
    # SEC: development-only deterministic key for evidence tests; production must provide env keyring.
    DEFAULT_APPLY_KEY_ID: "gategraph-local-dev-controlled-apply-secret-v1",
}

REVIEW_DECISION_APPROVE = "approved_for_controlled_apply"
REVIEW_DECISION_REJECT = "rejected"
ALLOWED_REVIEW_DECISIONS = {REVIEW_DECISION_APPROVE, REVIEW_DECISION_REJECT}
ALLOWED_CHANGE_TYPES = {"rule_update"}
_RULE_FIELD_ORDER = {
    "risk_threshold": ["low", "medium", "high", "critical"],
    "severity": ["low", "medium", "high", "critical"],
    "decision": ["allow", "warn", "require_review", "require_approval", "block"],
}
ALLOWED_RULE_UPDATE_FIELDS = set(_RULE_FIELD_ORDER) | {"priority", "rationale"}


@dataclass(frozen=True)
class ControlledApplyReview:
    review_id: str
    proposal_id: str
    reviewer_id: str
    decision: str
    rationale: str
    created_at: str


@dataclass(frozen=True)
class ApplyArtifact:
    artifact_id: str
    proposal_id: str
    change_type: str
    change_json: str
    artifact_hash: str
    signing_key_id: str
    signature: str
    expires_at: str
    created_at: str
    status: str


class ControlledApplyError(ValueError):
    pass


def ensure_controlled_apply_schema(conn: sqlite3.Connection) -> None:
    """Additive schema only; does not alter existing governance/enforcement tables."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS controlled_apply_reviews (
            review_id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            decision TEXT NOT NULL CHECK (decision IN ('approved_for_controlled_apply','rejected')),
            rationale TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
        );

        CREATE INDEX IF NOT EXISTS idx_controlled_apply_reviews_proposal
            ON controlled_apply_reviews(proposal_id);

        CREATE TABLE IF NOT EXISTS controlled_apply_artifacts (
            artifact_id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            change_type TEXT NOT NULL,
            change_json TEXT NOT NULL,
            before_json TEXT NOT NULL,
            artifact_hash TEXT NOT NULL UNIQUE,
            signing_key_id TEXT NOT NULL,
            signature TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('active','executed','expired','rejected')),
            executed_at TEXT,
            FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
        );

        CREATE INDEX IF NOT EXISTS idx_controlled_apply_artifacts_proposal
            ON controlled_apply_artifacts(proposal_id);
        """
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _load_apply_keyring() -> Dict[str, bytes]:
    raw = os.environ.get(_ENV_APPLY_KEYRING_JSON)
    if raw:
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict) or not parsed:
                return {}
            return {str(k): str(v).encode("utf-8") for k, v in parsed.items() if str(k).strip() and str(v)}
        except Exception:
            return {}
    return {kid: secret.encode("utf-8") for kid, secret in _DEV_APPLY_KEYRING.items()}


def _active_apply_key_id() -> str:
    return os.environ.get(_ENV_APPLY_ACTIVE_KEY_ID, DEFAULT_APPLY_KEY_ID)


def _sign_artifact(canonical_payload: str, signing_key_id: str, keyring: Optional[Mapping[str, bytes]] = None) -> str:
    secret = (keyring or _load_apply_keyring()).get(signing_key_id)
    if secret is None:
        raise ControlledApplyError(f"unknown apply signing key: {signing_key_id}")
    return hmac.new(secret, canonical_payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _parse_change(change: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(change, Mapping):
        raise ControlledApplyError("change must be an object")
    change_type = str(change.get("change_type", "")).strip()
    if change_type not in ALLOWED_CHANGE_TYPES:
        raise ControlledApplyError(f"unsupported controlled apply change_type: {change_type}")
    return dict(change)


def _rank(field: str, value: str) -> int:
    values = _RULE_FIELD_ORDER[field]
    if value not in values:
        raise ControlledApplyError(f"invalid {field}: {value}")
    return values.index(value)


def _validate_rule_update(conn: sqlite3.Connection, change: Mapping[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    rule_id = str(change.get("rule_id", "")).strip()
    updates = change.get("updates")
    if not rule_id:
        raise ControlledApplyError("rule_id is required")
    if not isinstance(updates, Mapping) or not updates:
        raise ControlledApplyError("updates object is required")

    unknown_fields = set(updates) - ALLOWED_RULE_UPDATE_FIELDS
    if unknown_fields:
        raise ControlledApplyError(f"unsupported rule update fields: {sorted(unknown_fields)}")

    row = conn.execute(
        "SELECT rule_id, risk_threshold, severity, decision, priority, rationale, active FROM rules WHERE rule_id = ?",
        (rule_id,),
    ).fetchone()
    if row is None:
        raise ControlledApplyError(f"rule not found: {rule_id}")
    if int(row["active"]) != 1:
        raise ControlledApplyError(f"rule is inactive: {rule_id}")

    before = {k: row[k] for k in ["rule_id", "risk_threshold", "severity", "decision", "priority", "rationale", "active"]}
    normalized_updates: Dict[str, Any] = {}

    for field in ("risk_threshold", "severity", "decision"):
        if field in updates:
            new_value = str(updates[field]).strip()
            if _rank(field, new_value) < _rank(field, str(row[field])):
                raise ControlledApplyError(f"rule update would loosen {field}")
            normalized_updates[field] = new_value

    if "priority" in updates:
        try:
            new_priority = int(updates["priority"])
        except Exception as exc:
            raise ControlledApplyError("priority must be an integer") from exc
        if new_priority < int(row["priority"]):
            raise ControlledApplyError("rule update would lower priority")
        normalized_updates["priority"] = new_priority

    if "rationale" in updates:
        rationale = str(updates["rationale"]).strip()
        if not rationale:
            raise ControlledApplyError("rationale update must not be empty")
        normalized_updates["rationale"] = rationale

    if not normalized_updates:
        raise ControlledApplyError("no effective supported updates supplied")

    after = dict(before)
    after.update(normalized_updates)
    return rule_id, before, normalized_updates, after


def validate_change(conn: sqlite3.Connection, change: Mapping[str, Any]) -> Dict[str, Any]:
    """Dry-run validation. Returns deterministic before/after data; performs no mutation."""
    parsed = _parse_change(change)
    if parsed["change_type"] == "rule_update":
        rule_id, before, updates, after = _validate_rule_update(conn, parsed)
        return {
            "valid": True,
            "change_type": "rule_update",
            "target_id": rule_id,
            "updates": updates,
            "before": before,
            "after": after,
        }
    raise ControlledApplyError("unreachable change type")


def record_human_gate(
    conn: sqlite3.Connection,
    *,
    proposal_id: str,
    reviewer_id: str,
    decision: str,
    rationale: str,
) -> ControlledApplyReview:
    ensure_controlled_apply_schema(conn)
    if decision not in ALLOWED_REVIEW_DECISIONS:
        raise ControlledApplyError(f"unsupported controlled apply decision: {decision}")
    if not reviewer_id.strip():
        raise ControlledApplyError("reviewer_id is required")
    if not rationale.strip():
        raise ControlledApplyError("rationale is required")

    proposal = conn.execute("SELECT proposal_id, status FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    if proposal is None:
        raise ControlledApplyError(f"proposal not found: {proposal_id}")
    if proposal["status"] != "approved_for_manual_action":
        raise ControlledApplyError("proposal must first be approved_for_manual_action")

    prior = conn.execute(
        "SELECT reviewer_id, decision FROM controlled_apply_reviews WHERE proposal_id = ? ORDER BY created_at ASC",
        (proposal_id,),
    ).fetchall()
    if any(r["reviewer_id"] == reviewer_id for r in prior):
        raise ControlledApplyError("same reviewer cannot review controlled apply twice")
    if any(r["decision"] == REVIEW_DECISION_REJECT for r in prior):
        raise ControlledApplyError("controlled apply was already rejected")
    approvals = [r for r in prior if r["decision"] == REVIEW_DECISION_APPROVE]
    if decision == REVIEW_DECISION_APPROVE and len(approvals) >= 2:
        raise ControlledApplyError("controlled apply already has two approvals")

    review = ControlledApplyReview(
        review_id=f"CAR-{uuid.uuid4().hex[:12].upper()}",
        proposal_id=proposal_id,
        reviewer_id=reviewer_id,
        decision=decision,
        rationale=rationale,
        created_at=_now().isoformat(),
    )
    with conn:
        conn.execute(
            """
            INSERT INTO controlled_apply_reviews
              (review_id, proposal_id, reviewer_id, decision, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (review.review_id, review.proposal_id, review.reviewer_id, review.decision, review.rationale, review.created_at),
        )
        _audit_controlled_apply(conn, proposal_id, "controlled_apply_approved" if decision == REVIEW_DECISION_APPROVE else "controlled_apply_rejected", {"review_id": review.review_id, "reviewer_id": reviewer_id, "decision": decision})
    return review


def create_apply_artifact(
    conn: sqlite3.Connection,
    *,
    proposal_id: str,
    change: Mapping[str, Any],
    ttl_seconds: int = DEFAULT_APPLY_TTL_SECONDS,
) -> ApplyArtifact:
    ensure_controlled_apply_schema(conn)
    if ttl_seconds <= 0 or ttl_seconds > 3600:
        raise ControlledApplyError("ttl_seconds must be between 1 and 3600")

    approvals = conn.execute(
        """
        SELECT DISTINCT reviewer_id FROM controlled_apply_reviews
        WHERE proposal_id = ? AND decision = 'approved_for_controlled_apply'
        """,
        (proposal_id,),
    ).fetchall()
    if len(approvals) < 2:
        raise ControlledApplyError("two distinct controlled apply approvals are required")

    dry_run = validate_change(conn, change)
    canonical_change = _canonical_json({"change_type": dry_run["change_type"], "target_id": dry_run["target_id"], "updates": dry_run["updates"]})
    now = _now()
    expires_at = now + timedelta(seconds=ttl_seconds)
    artifact_id = f"CAA-{uuid.uuid4().hex[:12].upper()}"
    canonical_payload = _canonical_json(
        {
            "artifact_id": artifact_id,
            "proposal_id": proposal_id,
            "schema_version": APPLY_SCHEMA_VERSION,
            "change_json": canonical_change,
            "expires_at": expires_at.isoformat(),
        }
    )
    artifact_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    signing_key_id = _active_apply_key_id()
    signature = _sign_artifact(canonical_payload, signing_key_id)
    artifact = ApplyArtifact(
        artifact_id=artifact_id,
        proposal_id=proposal_id,
        change_type=dry_run["change_type"],
        change_json=canonical_change,
        artifact_hash=artifact_hash,
        signing_key_id=signing_key_id,
        signature=signature,
        expires_at=expires_at.isoformat(),
        created_at=now.isoformat(),
        status="active",
    )
    with conn:
        conn.execute(
            """
            INSERT INTO controlled_apply_artifacts
              (artifact_id, proposal_id, schema_version, change_type, change_json, before_json,
               artifact_hash, signing_key_id, signature, expires_at, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                artifact.artifact_id, artifact.proposal_id, APPLY_SCHEMA_VERSION, artifact.change_type,
                artifact.change_json, _canonical_json(dry_run["before"]), artifact.artifact_hash,
                artifact.signing_key_id, artifact.signature, artifact.expires_at, artifact.created_at,
            ),
        )
        _audit_controlled_apply(conn, proposal_id, "controlled_apply_requested", {"artifact_id": artifact.artifact_id, "change_type": artifact.change_type, "dry_run": dry_run})
    return artifact


def execute_apply_artifact(conn: sqlite3.Connection, *, artifact_id: str) -> Dict[str, Any]:
    ensure_controlled_apply_schema(conn)
    row = conn.execute("SELECT * FROM controlled_apply_artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone()
    if row is None:
        raise ControlledApplyError(f"artifact not found: {artifact_id}")
    if row["status"] != "active":
        raise ControlledApplyError(f"artifact is not active: {row['status']}")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if _now() >= expires_at:
        with conn:
            conn.execute("UPDATE controlled_apply_artifacts SET status = 'expired' WHERE artifact_id = ?", (artifact_id,))
        raise ControlledApplyError("artifact expired")

    canonical_payload = _canonical_json(
        {
            "artifact_id": row["artifact_id"],
            "proposal_id": row["proposal_id"],
            "schema_version": row["schema_version"],
            "change_json": row["change_json"],
            "expires_at": row["expires_at"],
        }
    )
    expected_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    expected_sig = _sign_artifact(canonical_payload, row["signing_key_id"])
    if not hmac.compare_digest(expected_hash, row["artifact_hash"]):
        raise ControlledApplyError("artifact hash mismatch")
    if not hmac.compare_digest(expected_sig, row["signature"]):
        raise ControlledApplyError("artifact signature invalid")

    change = json.loads(row["change_json"])
    dry_run = validate_change(conn, {"change_type": change["change_type"], "rule_id": change["target_id"], "updates": change["updates"]})
    if _canonical_json(dry_run["before"]) != row["before_json"]:
        raise ControlledApplyError("target state changed since artifact creation")

    with conn:
        if dry_run["change_type"] == "rule_update":
            assignments = ", ".join(f"{field} = ?" for field in dry_run["updates"])
            values = list(dry_run["updates"].values()) + [dry_run["target_id"]]
            conn.execute(f"UPDATE rules SET {assignments} WHERE rule_id = ?", values)
        conn.execute(
            "UPDATE controlled_apply_artifacts SET status = 'executed', executed_at = ? WHERE artifact_id = ?",
            (_now().isoformat(), artifact_id),
        )
        _audit_controlled_apply(conn, row["proposal_id"], "controlled_apply_executed", {"artifact_id": artifact_id, "change_type": dry_run["change_type"], "before": dry_run["before"], "after": dry_run["after"]})
    return {"executed": True, "artifact_id": artifact_id, "change_type": dry_run["change_type"], "target_id": dry_run["target_id"]}


def _audit_controlled_apply(conn: sqlite3.Connection, proposal_id: str, event_type: str, details: Mapping[str, Any]) -> None:
    """Best-effort deterministic audit via existing append-only event logger."""
    task_id = f"CA-{proposal_id}"
    now = _now().isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO tasks
          (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
        VALUES (?, 'controlled_apply', '["write_files"]', 'human_gate', 'internal', 0, ?)
        """,
        (task_id, now),
    )
    event_logger.log_event(
        conn,
        event_id=f"EVT-CA-{uuid.uuid4().hex[:10].upper()}",
        idempotency_key=f"ca:{event_type}:{proposal_id}:{hashlib.sha256(_canonical_json(details).encode('utf-8')).hexdigest()[:16]}",
        correlation_id=f"COR-CA-{proposal_id}",
        causation_id=proposal_id,
        event_type=event_type,
        task_id=task_id,
        actor_component="controlled_apply",
        input_data={"proposal_id": proposal_id, "details": dict(details)},
        evaluation={"schema_version": APPLY_SCHEMA_VERSION},
        decision={"status": "recorded", "reason": event_type},
    )
