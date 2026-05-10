"""
WHY: Recovery checks must be deterministic and descriptive before any operational repair exists.
INV: This module does not mutate governance policy, enforcement, runtime budgets, or audit authority.
SEC: Ambiguous recovery states fail closed instead of inventing reservations, consumes, capabilities, or incident states.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

FORWARD_INCIDENT_STATES = {"open": 0, "acknowledged": 1, "resolved": 2}
FINAL_RESERVATION_STATES = {"consumed", "released"}
REFERENCE_ONLY_CONTEXT_TYPES = {"replay_context", "explain_snapshot", "archive_record", "recovery_snapshot"}


@dataclass(frozen=True)
class RecoveryDecision:
    decision: str
    reason: str
    reservation_id: str | None = None
    effect: str = "descriptive_only"

    def to_dict(self) -> dict:
        return asdict(self)


def recover_interrupted_reservation(reservation: Mapping[str, object]) -> RecoveryDecision:
    rid = str(reservation.get("reservation_id") or "")
    if not rid:
        return RecoveryDecision("stop", "RECOVERY_RESERVATION_ID_REQUIRED")
    state = reservation.get("state")
    consumed = bool(reservation.get("consumed", False))
    released = bool(reservation.get("released", False))
    if consumed and released:
        return RecoveryDecision("stop", "RECOVERY_RESERVATION_CONFLICT", rid)
    if state == "reserved" and not consumed and not released:
        return RecoveryDecision("continue", "RECOVERY_RELEASE_INTERRUPTED_RESERVATION", rid, "release_reservation")
    if state == "consumed" and consumed and not released:
        return RecoveryDecision("continue", "RECOVERY_CONSUME_ALREADY_FINAL", rid)
    if state == "released" and released and not consumed:
        return RecoveryDecision("continue", "RECOVERY_RELEASE_ALREADY_FINAL", rid)
    return RecoveryDecision("stop", "RECOVERY_UNKNOWN_RESERVATION_STATE", rid)


def apply_consume_once(consumed_reservation_ids: Iterable[str], reservation_id: str) -> RecoveryDecision:
    if not reservation_id:
        return RecoveryDecision("stop", "RECOVERY_RESERVATION_ID_REQUIRED")
    if reservation_id in set(consumed_reservation_ids):
        return RecoveryDecision("stop", "RECOVERY_DUPLICATE_CONSUME_BLOCKED", reservation_id)
    return RecoveryDecision("continue", "RECOVERY_CONSUME_ACCEPTED_ONCE", reservation_id, "consume_once")


def recover_attempt_once(completed_recovery_ids: Iterable[str], recovery_id: str) -> RecoveryDecision:
    """Classify a recovery attempt idempotently without performing repair.

    INV: Duplicate recovery attempts are observable terminal descriptions, not retries with new authority.
    """
    if not recovery_id:
        return RecoveryDecision("stop", "RECOVERY_ATTEMPT_ID_REQUIRED")
    if recovery_id in set(completed_recovery_ids):
        return RecoveryDecision("continue", "RECOVERY_ATTEMPT_ALREADY_FINAL", recovery_id)
    return RecoveryDecision("continue", "RECOVERY_ATTEMPT_ACCEPTED_ONCE", recovery_id, "record_recovery_attempt")


def validate_reservation_recovery_collision(reservation: Mapping[str, object], audit_events: Sequence[Mapping[str, object]]) -> RecoveryDecision:
    """Ensure reservation state and audit-derived finality do not conflict.

    SEC: Event history wins over ambiguous local state; conflicts fail closed instead of being repaired.
    """
    rid = str(reservation.get("reservation_id") or "")
    if not rid:
        return RecoveryDecision("stop", "RECOVERY_RESERVATION_ID_REQUIRED")
    local_decision = recover_interrupted_reservation(reservation)
    finalities: set[str] = set()
    for event in audit_events:
        if str(event.get("reservation_id") or "") != rid:
            continue
        event_type = str(event.get("event_type") or "")
        if event_type in {"reservation_consumed", "consume"}:
            finalities.add("consumed")
        if event_type in {"reservation_released", "release"}:
            finalities.add("released")
    if len(finalities) > 1:
        return RecoveryDecision("stop", "RECOVERY_RESERVATION_AUDIT_FINALITY_CONFLICT", rid)
    if finalities and str(reservation.get("state") or "") == "reserved":
        return RecoveryDecision("stop", "RECOVERY_RESERVATION_LOCAL_AUDIT_CONFLICT", rid)
    return local_decision


def classify_partial_recovery_state(snapshot: Mapping[str, object]) -> RecoveryDecision:
    """Fail closed for incomplete recovery snapshots.

    INV: Partial recovery is visible only; it is never promoted into executable runtime input.
    """
    snapshot_id = str(snapshot.get("snapshot_id") or snapshot.get("reservation_id") or "") or None
    required = ("audit_complete", "reservation_complete", "ledger_complete", "incident_complete")
    missing = [name for name in required if name not in snapshot]
    if missing:
        return RecoveryDecision("stop", "RECOVERY_PARTIAL_STATE_REQUIRED_FIELD_MISSING", snapshot_id)
    if not all(bool(snapshot.get(name)) for name in required):
        return RecoveryDecision("stop", "RECOVERY_PARTIAL_STATE_FAIL_CLOSED", snapshot_id)
    return RecoveryDecision("continue", "RECOVERY_SNAPSHOT_COMPLETE_DESCRIPTIVE", snapshot_id)


def validate_append_only_audit(events: Sequence[Mapping[str, object]]) -> RecoveryDecision:
    expected = 1
    seen_ids: set[str] = set()
    for event in events:
        event_id = str(event.get("event_id") or "")
        seq = event.get("sequence")
        if not event_id:
            return RecoveryDecision("stop", "RECOVERY_AUDIT_EVENT_ID_REQUIRED")
        if event_id in seen_ids:
            return RecoveryDecision("stop", "RECOVERY_AUDIT_DUPLICATE_EVENT_ID")
        seen_ids.add(event_id)
        if seq != expected:
            return RecoveryDecision("stop", "RECOVERY_AUDIT_SEQUENCE_GAP")
        expected += 1
    return RecoveryDecision("continue", "RECOVERY_AUDIT_APPEND_ONLY_SEQUENCE_OK")


def incident_transition(current_state: str, target_state: str) -> RecoveryDecision:
    if current_state not in FORWARD_INCIDENT_STATES or target_state not in FORWARD_INCIDENT_STATES:
        return RecoveryDecision("stop", "RECOVERY_INCIDENT_UNKNOWN_STATE")
    if FORWARD_INCIDENT_STATES[target_state] < FORWARD_INCIDENT_STATES[current_state]:
        return RecoveryDecision("stop", "RECOVERY_INCIDENT_STATE_REGRESSION_BLOCKED")
    if FORWARD_INCIDENT_STATES[target_state] == FORWARD_INCIDENT_STATES[current_state]:
        return RecoveryDecision("continue", "RECOVERY_INCIDENT_STATE_IDEMPOTENT")
    return RecoveryDecision("continue", "RECOVERY_INCIDENT_FORWARD_ONLY_TRANSITION")


def deterministic_replay_signature(records: Sequence[Mapping[str, object]]) -> tuple[tuple[int, str, str, str], ...]:
    """Return a stable replay signature independent of input iteration order.

    WHY: Explicit sequence numbers are preferred; missing sequence values are sorted after sequenced records.
    """
    def seq(value: object) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 2**31 - 1

    return tuple(
        sorted(
            (
                seq(r.get("sequence")),
                str(r.get("task_id") or ""),
                str(r.get("stage") or ""),
                str(r.get("normalized_reason_code") or r.get("reason_code") or ""),
            )
            for r in records
        )
    )


def validate_reference_only_object(obj: Mapping[str, object]) -> RecoveryDecision:
    context_type = str(obj.get("context_type") or "")
    if context_type not in REFERENCE_ONLY_CONTEXT_TYPES:
        return RecoveryDecision("stop", "REPLAY_REFERENCE_UNKNOWN_CONTEXT_TYPE")
    if bool(obj.get("executable")):
        return RecoveryDecision("stop", "REPLAY_REFERENCE_EXECUTABLE_BLOCKED")
    if bool(obj.get("governance_influence")):
        return RecoveryDecision("stop", "REPLAY_REFERENCE_GOVERNANCE_INFLUENCE_BLOCKED")
    if bool(obj.get("rehydrate_runtime")):
        return RecoveryDecision("stop", "REPLAY_REFERENCE_RUNTIME_REHYDRATION_BLOCKED")
    if obj.get("capability_token") or obj.get("new_capability"):
        return RecoveryDecision("stop", "REPLAY_REFERENCE_CAPABILITY_MATERIAL_BLOCKED")
    return RecoveryDecision("continue", "REPLAY_REFERENCE_ONLY_OBJECT_OK")
