"""
SEC: this is the only gate between a decision and an actual action — it must never be bypassed.
INV: no action executes without a valid, non-expired, non-revoked, task-bound token.
WHY: separating decision logic from enforcement prevents accidental permission escalation.
"""

import sqlite3
import uuid
from dataclasses import dataclass
from typing import Optional

from src.capability_token import CapabilityToken, verify_signature, load_trusted_keyring, is_trusted_signing_key, token_audit_ref
from src import event_logger


@dataclass(frozen=True)
class EnforcementResult:
    allowed: bool
    reason: str
    rejection_event_id: Optional[str]


def enforce(conn: sqlite3.Connection, token: Optional[CapabilityToken], requested_capability: str, task_id: str, correlation_id: str) -> EnforcementResult:
    if token is None:
        return _reject(conn, task_id, correlation_id, "no capability token provided", requested_capability)

    # SEC: cross-task token reuse is capability leakage.
    if token.task_id != task_id:
        return _reject(conn, task_id, correlation_id, f"token {token.token_id} is bound to task {token.task_id}, not {task_id}", requested_capability)

    if token.is_expired():
        return _reject(conn, task_id, correlation_id, f"token {token.token_id} expired at {token.expires_at.isoformat()}", requested_capability)

    # SEC: load trust material once per enforcement decision to avoid split-brain keyring reads.
    try:
        keyring = load_trusted_keyring()
    except RuntimeError as exc:
        return _reject(conn, task_id, correlation_id, str(exc), requested_capability)

    if not is_trusted_signing_key(token.signing_key_id, keyring):
        return _reject(conn, task_id, correlation_id, f"capability token unknown signing key: {token.signing_key_id}", requested_capability)

    # SEC: BEGIN IMMEDIATE narrows the local SQLite revocation race within the single-node scope.
    # EDGE: callers may already hold a fixture/runtime transaction; do not start a nested one.
    owns_tx = not conn.in_transaction
    try:
        if owns_tx:
            conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM capability_tokens WHERE token_id = ?", (token.token_id,)).fetchone()

        reason: Optional[str] = None
        if row is None:
            reason = f"capability token not found: {token.token_id}"
        elif int(row["revoked"]):
            reason = f"capability token revoked: {token.token_id}"
        elif row["decision_id"] != token.decision_id or row["task_id"] != token.task_id or row["expires_at"] != token.expires_at.isoformat():
            reason = f"capability token claim mismatch: {token.token_id}"
        elif row["signing_key_id"] != token.signing_key_id:
            reason = f"capability token claim mismatch: {token.token_id}"
        elif row["budget_scope_id"] != token.budget_scope_id or row["budget_reservation_id"] != token.budget_reservation_id:
            reason = f"capability token budget claim mismatch: {token.token_id}"
        else:
            persisted_max_cost = row["max_cost_for_action"]
            if persisted_max_cost is not None and token.max_cost_for_action != int(persisted_max_cost):
                reason = f"capability token budget claim mismatch: {token.token_id}"
            elif row["escalation_state"] != token.escalation_state:
                reason = f"capability token escalation claim mismatch: {token.token_id}"

        if reason:
            if owns_tx:
                conn.rollback()
            return _reject(conn, task_id, correlation_id, reason, requested_capability)

        try:
            import json
            persisted_caps = row["capabilities"]
            if json.dumps(token.capabilities, sort_keys=True) != json.dumps(json.loads(persisted_caps), sort_keys=True):
                if owns_tx:
                    conn.rollback()
                return _reject(conn, task_id, correlation_id, f"capability token claim mismatch: {token.token_id}", requested_capability)
            if not verify_signature(token, row["signature"], keyring=keyring):
                if owns_tx:
                    conn.rollback()
                return _reject(conn, task_id, correlation_id, f"capability token invalid signature: {token.token_id}", requested_capability)
        except Exception:
            if owns_tx:
                conn.rollback()
            return _reject(conn, task_id, correlation_id, f"capability token invalid signature: {token.token_id}", requested_capability)

        if not token.allows(requested_capability):
            if owns_tx:
                conn.rollback()
            return _reject(conn, task_id, correlation_id, f"capability '{requested_capability}' not granted in token {token.token_id}", requested_capability)

        record = event_logger.log_event(
            conn,
            event_id=f"EVT-ENF-{uuid.uuid4().hex[:12].upper()}",
            idempotency_key=f"enforcement-allowed:{correlation_id}:{task_id}:{requested_capability}:{token.token_id}",
            correlation_id=correlation_id,
            causation_id=None,
            event_type="enforcement_allowed",
            task_id=task_id,
            actor_component="enforcement",
            input_data={"requested_capability": requested_capability, "token_ref": token_audit_ref(token)},
            evaluation={"token_audit_redaction": "raw_token_signature_and_authorization_material_omitted"},
            decision={"status": "allow", "reason": "capability granted"},
        )
        if owns_tx:
            conn.commit()
        return EnforcementResult(True, "capability granted", None)
    except sqlite3.Error as exc:
        try:
            if owns_tx:
                conn.rollback()
        except sqlite3.Error:
            pass
        return _reject(conn, task_id, correlation_id, f"capability token validation failed closed: {exc.__class__.__name__}", requested_capability)

def _reject(conn: sqlite3.Connection, task_id: str, correlation_id: str, reason: str, cap: str) -> EnforcementResult:
    rejection_event_id = f"EVT-REJ-{uuid.uuid4().hex[:10].upper()}"
    idempotency_key = f"reject:{task_id}:{cap}:{reason[:40]}"
    with conn:
        record = event_logger.log_event(
            conn,
            event_id=rejection_event_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            causation_id=None,
            event_type="enforcement_rejection",
            task_id=task_id,
            actor_component="enforcement_layer",
            input_data={"requested_capability": cap},
            evaluation={"check": "capability_token_validation"},
            decision={"status": "block", "reason": reason},
        )
    return EnforcementResult(False, reason, record.event_id)
