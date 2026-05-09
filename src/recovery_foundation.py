"""
WHY: Recovery checks must be deterministic and descriptive before any operational repair exists.
INV: This module does not mutate governance policy, enforcement, runtime budgets, or audit authority.
SEC: Ambiguous recovery states fail closed instead of inventing reservations, consumes, or incident states.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence
FORWARD_INCIDENT_STATES = {"open": 0, "acknowledged": 1, "resolved": 2}
@dataclass(frozen=True)
class RecoveryDecision:
    decision: str
    reason: str
    reservation_id: str | None = None
    effect: str = "descriptive_only"
    def to_dict(self) -> dict: return asdict(self)
def recover_interrupted_reservation(reservation: Mapping[str, object]) -> RecoveryDecision:
    rid = str(reservation.get("reservation_id") or "")
    if not rid: return RecoveryDecision("stop", "RECOVERY_RESERVATION_ID_REQUIRED")
    state = reservation.get("state")
    consumed = bool(reservation.get("consumed", False)); released = bool(reservation.get("released", False))
    if consumed and released: return RecoveryDecision("stop", "RECOVERY_RESERVATION_CONFLICT", rid)
    if state == "reserved" and not consumed and not released: return RecoveryDecision("continue", "RECOVERY_RELEASE_INTERRUPTED_RESERVATION", rid, "release_reservation")
    if state == "consumed" and consumed and not released: return RecoveryDecision("continue", "RECOVERY_CONSUME_ALREADY_FINAL", rid)
    if state == "released" and released and not consumed: return RecoveryDecision("continue", "RECOVERY_RELEASE_ALREADY_FINAL", rid)
    return RecoveryDecision("stop", "RECOVERY_UNKNOWN_RESERVATION_STATE", rid)
def apply_consume_once(consumed_reservation_ids: Iterable[str], reservation_id: str) -> RecoveryDecision:
    if not reservation_id: return RecoveryDecision("stop", "RECOVERY_RESERVATION_ID_REQUIRED")
    if reservation_id in set(consumed_reservation_ids): return RecoveryDecision("stop", "RECOVERY_DUPLICATE_CONSUME_BLOCKED", reservation_id)
    return RecoveryDecision("continue", "RECOVERY_CONSUME_ACCEPTED_ONCE", reservation_id, "consume_once")
def validate_append_only_audit(events: Sequence[Mapping[str, object]]) -> RecoveryDecision:
    expected = 1; seen_ids: set[str] = set()
    for event in events:
        event_id = str(event.get("event_id") or ""); seq = event.get("sequence")
        if not event_id: return RecoveryDecision("stop", "RECOVERY_AUDIT_EVENT_ID_REQUIRED")
        if event_id in seen_ids: return RecoveryDecision("stop", "RECOVERY_AUDIT_DUPLICATE_EVENT_ID")
        seen_ids.add(event_id)
        if seq != expected: return RecoveryDecision("stop", "RECOVERY_AUDIT_SEQUENCE_GAP")
        expected += 1
    return RecoveryDecision("continue", "RECOVERY_AUDIT_APPEND_ONLY_SEQUENCE_OK")
def incident_transition(current_state: str, target_state: str) -> RecoveryDecision:
    if current_state not in FORWARD_INCIDENT_STATES or target_state not in FORWARD_INCIDENT_STATES: return RecoveryDecision("stop", "RECOVERY_INCIDENT_UNKNOWN_STATE")
    if FORWARD_INCIDENT_STATES[target_state] < FORWARD_INCIDENT_STATES[current_state]: return RecoveryDecision("stop", "RECOVERY_INCIDENT_STATE_REGRESSION_BLOCKED")
    if FORWARD_INCIDENT_STATES[target_state] == FORWARD_INCIDENT_STATES[current_state]: return RecoveryDecision("continue", "RECOVERY_INCIDENT_STATE_IDEMPOTENT")
    return RecoveryDecision("continue", "RECOVERY_INCIDENT_FORWARD_ONLY_TRANSITION")
def deterministic_replay_signature(records: Sequence[Mapping[str, object]]) -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted((str(r.get("task_id") or ""), str(r.get("stage") or ""), str(r.get("normalized_reason_code") or r.get("reason_code") or "")) for r in records))
