"""
WHY: governance.py is the single entry point for all task evaluation.
INV: caller never touches Risk Engine, Rule Engine, or Event Logger directly.
SEC: all side effects are funneled through this module to ensure audit completeness.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src import risk_engine, rule_engine, event_logger, capability_token as cap_module, budget_ledger
from src.runtime_path_assertions import TrustedEntryContext, assert_trusted_entry_context
from src.capability_token import CapabilityToken

ALL_KNOWN_CAPABILITIES = ["read_files", "write_files", "delete_files", "api_call"]


@dataclass(frozen=True)
class GovernanceResult:
    task_id: str
    correlation_id: str
    risk_level: str
    risk_reason: str
    final_decision: str
    selected_rule_id: Optional[str]
    matched_rule_ids: List[str]
    conflict_resolved: bool
    token: Optional[CapabilityToken]
    budget_scope_id: Optional[str]
    budget_reservation_id: Optional[str]
    escalation_state: Optional[str]
    event_id: str
    decision_id: str
    was_duplicate: bool


def evaluate_task(
    conn: sqlite3.Connection,
    *,
    task_id: str,
    task_type: str,
    requested_capabilities: List[str],
    input_source: str,
    data_sensitivity: str = "internal",
    secrets_involved: bool = False,
    idempotency_key: Optional[str] = None,
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
    token_ttl: int = 300,
    actor_id: str = "default_actor",
    projected_cost_units: int = 1,
    system_budget_units: int = 100,
    actor_budget_units: int = 1000000,
    trusted_entry_context: TrustedEntryContext | dict | None = None,
) -> GovernanceResult:
    entry_context = assert_trusted_entry_context(trusted_entry_context)
    correlation_id = correlation_id or f"COR-{uuid.uuid4().hex[:12].upper()}"
    idempotency_key = idempotency_key or f"task:{task_id}:eval"
    event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"
    decision_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    caps_for_storage = requested_capabilities if requested_capabilities else ["__empty__"]
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, task_type, json.dumps(caps_for_storage), input_source, data_sensitivity, 1 if secrets_involved else 0, now),
        )

    risk = risk_engine.classify(requested_capabilities, input_source, data_sensitivity, secrets_involved)
    rule_result = rule_engine.evaluate(conn, caps_for_storage, risk.risk_level)

    # SEC: require_review is analysis-only; it may allow reads but never side effects.
    final_caps: Dict[str, bool] = {}
    for cap in ALL_KNOWN_CAPABILITIES:
        if cap not in requested_capabilities:
            final_caps[cap] = False
        elif rule_result.final_decision in ("allow", "warn"):
            final_caps[cap] = True
        elif rule_result.final_decision == "require_review":
            final_caps[cap] = cap == "read_files"
        else:
            final_caps[cap] = False

    matched_rule_ids = [r.rule_id for r in rule_result.matched_rules]
    selected_rationale = next((r.rationale for r in rule_result.matched_rules if r.rule_id == rule_result.selected_rule_id), None)

    with conn:
        event_record = event_logger.log_event(
            conn,
            event_id=event_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            causation_id=causation_id,
            event_type="governance_decision",
            task_id=task_id,
            actor_component="rule_engine",
            input_data={
                "task_type": task_type,
                "requested_capabilities": requested_capabilities,
                "input_source": input_source,
                "data_sensitivity": data_sensitivity,
                "secrets_involved": secrets_involved,
                "trusted_entry_context": entry_context.as_audit_dict(),
            },
            evaluation={
                "risk_level": risk.risk_level,
                "risk_reason": risk.reason,
                "matched_rules": matched_rule_ids,
                "selected_rule": rule_result.selected_rule_id,
                "conflict_resolved": rule_result.conflict_resolved,
            },
            decision={
                "status": rule_result.final_decision,
                "reason": selected_rationale or "no matching rule — fail-closed",
                "final_capabilities": final_caps,
            },
        )

    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id, task_id, event_record.event_id, rule_result.final_decision,
                json.dumps(final_caps), selected_rationale or risk.reason, json.dumps(matched_rule_ids), now,
            ),
        )
        event_logger.log_relation(conn, task_id, "task", "generated", event_record.event_id, "event")
        for rule_id in matched_rule_ids:
            event_logger.log_relation(conn, event_record.event_id, "event", "matched", rule_id, "rule")
        event_logger.log_relation(conn, event_record.event_id, "event", "produced", decision_id, "decision")

    token: Optional[CapabilityToken] = None
    budget_scope_id: Optional[str] = None
    budget_reservation_id: Optional[str] = None
    escalation_state: Optional[str] = None
    if any(final_caps.values()):
        with conn:
            # INV: budget authority sits in Governance; downstream layers only receive signed constraints.
            budget_ledger.ensure_budget_schema(conn)
            system_scope = budget_ledger.ensure_scope(
                conn, scope_id="system:default", scope_type="system", allocated_units=system_budget_units
            )
            actor_scope = budget_ledger.ensure_scope(
                conn, scope_id=f"actor:{actor_id}", scope_type="actor", allocated_units=actor_budget_units, parent_scope_id=system_scope.scope_id
            )
            reservation = budget_ledger.reserve_budget(
                conn,
                scope_id=actor_scope.scope_id,
                amount_units=projected_cost_units,
                idempotency_key=f"budget:{idempotency_key}",
                ttl_seconds=token_ttl,
            )
            refreshed_scope = budget_ledger.get_scope(conn, actor_scope.scope_id)
            budget_scope_id = actor_scope.scope_id
            budget_reservation_id = reservation.reservation_id
            escalation_state = refreshed_scope.state if refreshed_scope else "blocked"
            token = cap_module.issue_token(
                conn,
                decision_id,
                task_id,
                final_caps,
                token_ttl,
                budget_scope_id=budget_scope_id,
                budget_reservation_id=budget_reservation_id,
                max_cost_for_action=projected_cost_units,
                escalation_state=escalation_state,
            )

    return GovernanceResult(
        task_id, correlation_id, risk.risk_level, risk.reason, rule_result.final_decision,
        rule_result.selected_rule_id, matched_rule_ids, rule_result.conflict_resolved,
        token, budget_scope_id, budget_reservation_id, escalation_state, event_record.event_id, decision_id, event_record.was_duplicate,
    )
