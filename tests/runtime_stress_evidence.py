"""
WHY: Runtime/cost/loop proof runner turns DB state into auditable JSON evidence.
INV: production core modules are only called through their public APIs; this runner does not weaken them.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src.governance import evaluate_task
from src.enforcement import enforce
from src import runtime_guard, pattern_engine, event_logger
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence, collect_global_evidence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_evidence_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    ensure_runtime_schema(conn)
    ensure_pattern_schema(conn)
    with conn:
        seed_rules(conn)
    return conn, db_path


def close_conn(conn, db_path: Path) -> None:
    conn.close()
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


def has_runtime_stop(evidence, allowed_fragments) -> bool:
    stops = [d for d in evidence["runtime_decisions"] if d["decision"] == "stop"]
    return any(any(fragment in d["reason"] for fragment in allowed_fragments) for d in stops)


def scenario_agent_pingpong_loop() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-PINGPONG"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=20, repeated_action_limit=2)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b")
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b")
        d3 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b")
        evidence = collect_task_evidence(conn, task_id)
        passed = d1.decision == "continue" and d2.decision == "continue" and d3.decision == "stop" and has_runtime_stop(evidence, ["repeated_action_limit"])
        return EvidenceScenarioResult(
            test_name="agent_pingpong_loop",
            description="Repeated agent delegation with identical signature must be stopped by Runtime Guard.",
            expected={"final_runtime_decision": "stop", "stop_reason_contains": "repeated_action_limit", "audit_required": True},
            actual={"decisions": [d1.decision, d2.decision, d3.decision], "final_reason": d3.reason},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Runtime repeated-action loop evidence missing or final decision was not stop."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_cost_limit() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-COST"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=3)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="analysis-a", cost_units=2)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="analysis-b", cost_units=2)
        evidence = collect_task_evidence(conn, task_id)
        passed = d1.decision == "continue" and d2.decision == "stop" and (has_runtime_stop(evidence, ["max_cost_units", "projected_cost_violation"]) or "projected_cost_violation" in d2.reason)
        return EvidenceScenarioResult(
            test_name="many_allowed_micro_actions_cost_limit",
            description="Individually plausible model/tool steps must stop once cumulative budget is exceeded.",
            expected={"final_runtime_decision": "stop", "stop_reason_contains": "max_cost_units|projected_cost_violation", "audit_required": True},
            actual={"decisions": [d1.decision, d2.decision], "final_reason": d2.reason},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Cost-limit evidence missing or final decision was not stop."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_valid_token_but_runtime_exceeded() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-TOKEN-RUNTIME"
    try:
        gov = evaluate_task(
            conn,
            task_id=task_id,
            task_type="agent_operation",
            requested_capabilities=["read_files"],
            input_source="local",
            data_sensitivity="internal",
            secrets_involved=False,
        )
        runtime_guard.create_budget(conn, task_id=task_id, max_runtime_seconds=1)
        old = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        with conn:
            conn.execute("UPDATE runtime_budgets SET created_at = ? WHERE task_id = ?", (old, task_id))
        rt = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="read_files", target="README.md")

        # SEC: runtime stop means enforcement/action is intentionally not called after this point.
        evidence = collect_task_evidence(conn, task_id)
        token_present = gov.token is not None
        passed = token_present and rt.decision == "stop" and has_runtime_stop(evidence, ["max_runtime_seconds"])
        return EvidenceScenarioResult(
            test_name="valid_token_but_runtime_exceeded",
            description="A valid capability token must not override an exhausted Runtime Guard budget.",
            expected={"token_present": True, "runtime_decision": "stop", "action_after_stop": False, "audit_required": True},
            actual={"token_present": token_present, "runtime_decision": rt.decision, "runtime_reason": rt.reason, "action_after_stop": False},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Could not prove that runtime exhaustion overrides token permission."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_no_token_enforcement_rejection() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-NO-TOKEN"
    try:
        # Need a task row for the FK-backed audit event.
        evaluate_task(
            conn,
            task_id=task_id,
            task_type="agent_operation",
            requested_capabilities=["read_files"],
            input_source="local",
            data_sensitivity="internal",
            secrets_involved=False,
        )
        enf = enforce(conn, None, "read_files", task_id, "COR-STRESS-NO-TOKEN")
        evidence = collect_task_evidence(conn, task_id)
        rejection_events = [e for e in evidence["events"] if e["type"] == "enforcement_rejection"]
        passed = not enf.allowed and bool(rejection_events) and "no capability token" in enf.reason
        return EvidenceScenarioResult(
            test_name="no_action_without_token",
            description="Enforcement must reject actions without a capability token and write audit evidence.",
            expected={"allowed": False, "event_type": "enforcement_rejection", "audit_required": True},
            actual={"allowed": enf.allowed, "reason": enf.reason, "rejection_event_id": enf.rejection_event_id},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["No-token rejection was not auditable."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def add_rejection(conn, idx: int, capability: str = "write_files", reason: str = "no capability token provided"):
    task_id = f"STRESS-PATTERN-{idx}"
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES (?, 'file_operation', '["write_files"]', 'local', 'internal', 0, datetime('now'))
            """,
            (task_id,),
        )
    event_logger.log_event(
        conn,
        event_id=f"STRESS-PAT-EVT-{idx}",
        idempotency_key=f"stress-pattern:{idx}",
        correlation_id=f"STRESS-PAT-COR-{idx}",
        causation_id=None,
        event_type="enforcement_rejection",
        task_id=task_id,
        actor_component="enforcement_layer",
        input_data={"requested_capability": capability},
        evaluation={"check": "capability_token_validation"},
        decision={"status": "block", "reason": reason},
    )


def scenario_pattern_engine_proposal_only() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        for i in range(1, 5):
            add_rejection(conn, i)
        before_rules = pattern_engine.active_rule_count(conn)
        result = pattern_engine.analyze_rejections(conn, min_events=3, confidence_threshold=0.75)
        after_rules = pattern_engine.active_rule_count(conn)
        global_evidence = collect_global_evidence(conn)
        proposals = global_evidence["proposals"]
        passed = result.proposals_created == 1 and before_rules == after_rules and proposals and all(p["status"] == "pending_review" for p in proposals)
        return EvidenceScenarioResult(
            test_name="pattern_engine_proposal_only",
            description="Pattern Engine may create proposals from repeated rejections but must not mutate rules.",
            expected={"proposal_created": True, "rules_changed": False, "proposal_status": "pending_review"},
            actual={"proposals_created": result.proposals_created, "rules_before": before_rules, "rules_after": after_rules, "proposal_statuses": [p["status"] for p in proposals]},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Pattern Engine proposal-only invariant not proven."],
            evidence=global_evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_repeated_same_decision_evidence() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-SAME-DECISION"
    try:
        first = evaluate_task(
            conn,
            task_id=task_id,
            task_type="agent_operation",
            requested_capabilities=["read_files"],
            input_source="local",
            idempotency_key="stress:same-decision",
        )
        second = evaluate_task(
            conn,
            task_id=task_id,
            task_type="agent_operation",
            requested_capabilities=["read_files"],
            input_source="local",
            idempotency_key="stress:same-decision",
        )
        evidence = collect_task_evidence(conn, task_id)
        event_count = len([e for e in evidence["events"] if e["type"] == "governance_decision"])
        passed = first.was_duplicate is False and second.was_duplicate is True and event_count == 1
        severity = "info" if passed else "medium"
        notes = [] if passed else ["Repeated same decision did not produce clean idempotent audit evidence."]
        if passed:
            notes.append("Current behavior deduplicates governance audit events; it does not implement semantic no-progress stopping.")
        return EvidenceScenarioResult(
            test_name="repeated_same_decision_evidence",
            description="Repeated identical governance evaluation must not corrupt audit evidence.",
            expected={"second_was_duplicate": True, "governance_event_count": 1},
            actual={"first_was_duplicate": first.was_duplicate, "second_was_duplicate": second.was_duplicate, "governance_event_count": event_count},
            passed=passed,
            severity=severity,
            notes=notes,
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)



def scenario_multi_agent_alternating_loop_max_steps() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-MULTI-AGENT-ALT"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=4, max_cost_units=20, repeated_action_limit=10)
        decisions = []
        for idx in range(6):
            actor = "agent-a" if idx % 2 == 0 else "agent-b"
            target = "agent-b" if actor == "agent-a" else "agent-a"
            decision = runtime_guard.evaluate_before_step(
                conn,
                task_id=task_id,
                actor_id=actor,
                action_type="delegate",
                target=target,
            )
            decisions.append(decision)
            if decision.decision == "stop":
                break
        evidence = collect_task_evidence(conn, task_id)
        final = decisions[-1]
        passed = final.decision == "stop" and has_runtime_stop(evidence, ["max_steps"])
        return EvidenceScenarioResult(
            test_name="multi_agent_alternating_loop_max_steps",
            description="Alternating multi-agent delegation with changing signatures must still stop at the task step budget.",
            expected={"final_runtime_decision": "stop", "stop_reason_contains": "max_steps", "audit_required": True},
            actual={"decisions": [d.decision for d in decisions], "final_reason": final.reason, "steps_recorded": len(evidence["runtime_steps"])},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Alternating multi-agent loop was not stopped by max_steps evidence."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_missing_runtime_budget_fail_closed() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-NO-RUNTIME-BUDGET"
    try:
        decision = runtime_guard.evaluate_before_step(
            conn,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            target="analysis",
        )
        evidence = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and has_runtime_stop(evidence, ["no runtime budget"])
        return EvidenceScenarioResult(
            test_name="missing_runtime_budget_fail_closed",
            description="Runtime Guard must fail closed when no runtime budget exists for a task.",
            expected={"runtime_decision": "stop", "stop_reason_contains": "no runtime budget", "audit_required": True},
            actual={"runtime_decision": decision.decision, "runtime_reason": decision.reason},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Missing runtime budget did not produce auditable fail-closed evidence."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_budget_boundary_exact_cost_allowed_then_stop() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    task_id = "STRESS-BUDGET-BOUNDARY"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=4)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="a", cost_units=2)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="b", cost_units=2)
        d3 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="c", cost_units=1)
        evidence = collect_task_evidence(conn, task_id)
        passed = [d1.decision, d2.decision, d3.decision] == ["continue", "continue", "stop"] and (has_runtime_stop(evidence, ["max_cost_units", "projected_cost_violation"]) or "projected_cost_violation" in d3.reason)
        return EvidenceScenarioResult(
            test_name="budget_boundary_exact_cost_allowed_then_stop",
            description="Exact budget consumption is allowed; the first step beyond budget must stop with evidence.",
            expected={"decisions": ["continue", "continue", "stop"], "stop_reason_contains": "max_cost_units|projected_cost_violation"},
            actual={"decisions": [d1.decision, d2.decision, d3.decision], "final_reason": d3.reason},
            passed=passed,
            severity="info" if passed else "medium",
            notes=[] if passed else ["Cost boundary behavior is not proven cleanly."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_cross_task_cost_is_not_session_budget() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        task_ids = ["STRESS-CROSS-TASK-A", "STRESS-CROSS-TASK-B"]
        finals = []
        evidences = {}
        for task_id in task_ids:
            runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=3)
            d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target=f"{task_id}-1", cost_units=2)
            d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target=f"{task_id}-2", cost_units=2)
            finals.append(d2)
            evidences[task_id] = collect_task_evidence(conn, task_id)
        passed = all(d.decision == "stop" and ("max_cost_units" in d.reason or "projected_cost_violation" in d.reason) for d in finals)
        return EvidenceScenarioResult(
            test_name="cross_task_cost_is_per_task_not_session_budget",
            description="Documents current scope: cost budget is enforced per task; no global/session budget is implemented in core runtime.",
            expected={"per_task_cost_stop": True, "session_budget_present": False},
            actual={"final_decisions": [d.decision for d in finals], "final_reasons": [d.reason for d in finals], "session_budget_present": False},
            passed=passed,
            severity="medium",
            notes=[
                "Evidence confirms per-task cost control.",
                "Known remaining gap: there is no cumulative session/global budget across multiple tasks in current core scope.",
            ],
            evidence={"tasks": evidences},
        )
    finally:
        close_conn(conn, db_path)




def _sum_runtime_cost(evidence: dict) -> int:
    return sum(int(step.get("cost_units") or 0) for step in evidence.get("runtime_steps", []))


def scenario_cross_task_cascade_drift_visible() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        task_evidence = {}
        total_cost = 0
        stop_count = 0

        for idx in range(1, 21):
            task_id = f"STRESS-CASCADE-{idx:02d}"
            runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=10)
            decision = runtime_guard.evaluate_before_step(
                conn,
                task_id=task_id,
                actor_id="agent-cascade",
                action_type="model_call",
                target=f"analysis-{idx}",
                cost_units=4,
            )
            ev = collect_task_evidence(conn, task_id)
            task_evidence[task_id] = ev
            total_cost += _sum_runtime_cost(ev)
            if decision.decision == "stop":
                stop_count += 1

        passed = stop_count == 0 and total_cost == 80
        return EvidenceScenarioResult(
            test_name="cross_task_cascade_drift_visible",
            description="Twenty individually allowed tasks accumulate cost without a session/global budget stop.",
            expected={"tasks": 20, "per_task_stops": 0, "total_cost_units": 80, "session_budget_present": False},
            actual={"tasks": len(task_evidence), "per_task_stops": stop_count, "total_cost_units": total_cost, "session_budget_present": False},
            passed=passed,
            severity="medium",
            notes=[
                "This is an evidence finding, not a core bug: per-task budgets work, but cumulative cross-task drift is not blocked.",
                "Use this as the proof basis before adding session/global budgets.",
            ],
            evidence={"tasks": task_evidence, "aggregate": {"total_cost_units": total_cost, "per_task_stops": stop_count}},
        )
    finally:
        close_conn(conn, db_path)


def scenario_parallel_multi_agent_drift_visible() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        task_evidence = {}
        total_cost = 0
        stop_count = 0

        for agent_idx in range(1, 4):
            for task_idx in range(1, 6):
                task_id = f"STRESS-PARALLEL-A{agent_idx}-T{task_idx}"
                runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=9, repeated_action_limit=10)
                decision = runtime_guard.evaluate_before_step(
                    conn,
                    task_id=task_id,
                    actor_id=f"agent-{agent_idx}",
                    action_type="model_call",
                    target=f"parallel-analysis-{task_idx}",
                    cost_units=3,
                )
                ev = collect_task_evidence(conn, task_id)
                task_evidence[task_id] = ev
                total_cost += _sum_runtime_cost(ev)
                if decision.decision == "stop":
                    stop_count += 1

        passed = stop_count == 0 and total_cost == 45
        return EvidenceScenarioResult(
            test_name="parallel_multi_agent_drift_visible",
            description="Three agents can each stay under per-task budgets while aggregate session cost rises.",
            expected={"agents": 3, "tasks": 15, "per_task_stops": 0, "total_cost_units": 45, "agent_global_budget_present": False},
            actual={"agents": 3, "tasks": len(task_evidence), "per_task_stops": stop_count, "total_cost_units": total_cost, "agent_global_budget_present": False},
            passed=passed,
            severity="medium",
            notes=[
                "Evidence confirms missing aggregate budget across agents.",
                "Core invariants remain intact; the gap is economic/runtime aggregation, not token enforcement.",
            ],
            evidence={"tasks": task_evidence, "aggregate": {"total_cost_units": total_cost, "per_task_stops": stop_count}},
        )
    finally:
        close_conn(conn, db_path)


def scenario_session_reset_budget_bypass_visible() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        first_task = "STRESS-SESSION-RESET-1"
        second_task = "STRESS-SESSION-RESET-2"
        evidences = {}

        runtime_guard.create_budget(conn, task_id=first_task, max_steps=5, max_cost_units=10, repeated_action_limit=10)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=first_task, actor_id="agent-reset", action_type="model_call", target="part-1", cost_units=9)
        evidences[first_task] = collect_task_evidence(conn, first_task)

        # Simulates a new task/session continuing the same logical work with a fresh per-task budget.
        runtime_guard.create_budget(conn, task_id=second_task, max_steps=5, max_cost_units=10, repeated_action_limit=10)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=second_task, actor_id="agent-reset", action_type="model_call", target="part-2", cost_units=9)
        evidences[second_task] = collect_task_evidence(conn, second_task)

        total_cost = sum(_sum_runtime_cost(ev) for ev in evidences.values())
        passed = d1.decision == "continue" and d2.decision == "continue" and total_cost == 18
        return EvidenceScenarioResult(
            test_name="session_reset_budget_bypass_visible",
            description="A logical continuation can receive a fresh per-task budget after task/session reset.",
            expected={"first_decision": "continue", "second_decision": "continue", "total_cost_units": 18, "session_continuity_budget_present": False},
            actual={"first_decision": d1.decision, "second_decision": d2.decision, "total_cost_units": total_cost, "session_continuity_budget_present": False},
            passed=passed,
            severity="high",
            notes=[
                "This documents the strongest current cost-control gap: per-task reset can bypass cumulative intent/session cost limits.",
                "No core invariant is violated; missing concept is logical session/global budget continuity.",
            ],
            evidence={"tasks": evidences, "aggregate": {"total_cost_units": total_cost}},
        )
    finally:
        close_conn(conn, db_path)


def scenario_micro_task_flood_drift_visible() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        task_evidence = {}
        total_cost = 0
        stop_count = 0

        for idx in range(1, 101):
            task_id = f"STRESS-MICRO-FLOOD-{idx:03d}"
            runtime_guard.create_budget(conn, task_id=task_id, max_steps=2, max_cost_units=2, repeated_action_limit=10)
            decision = runtime_guard.evaluate_before_step(
                conn,
                task_id=task_id,
                actor_id="agent-flood",
                action_type="micro_model_call",
                target=f"redundant-check-{idx}",
                cost_units=1,
            )
            ev = collect_task_evidence(conn, task_id)
            task_evidence[task_id] = ev
            total_cost += _sum_runtime_cost(ev)
            if decision.decision == "stop":
                stop_count += 1

        passed = stop_count == 0 and total_cost == 100
        return EvidenceScenarioResult(
            test_name="micro_task_flood_drift_visible",
            description="One hundred individually valid micro-tasks create aggregate cost without a global stop.",
            expected={"tasks": 100, "per_task_stops": 0, "total_cost_units": 100, "global_flood_guard_present": False},
            actual={"tasks": len(task_evidence), "per_task_stops": stop_count, "total_cost_units": total_cost, "global_flood_guard_present": False},
            passed=passed,
            severity="high",
            notes=[
                "Evidence confirms that micro-task flooding is visible in logs but not blocked by current per-task runtime budgets.",
                "This finding should drive the next controlled design step: session/global budget policy, not Pattern Engine automation.",
            ],
            evidence={"tasks": task_evidence, "aggregate": {"total_cost_units": total_cost, "per_task_stops": stop_count}},
        )
    finally:
        close_conn(conn, db_path)

def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("runtime_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_agent_pingpong_loop,
        scenario_cost_limit,
        scenario_valid_token_but_runtime_exceeded,
        scenario_no_token_enforcement_rejection,
        scenario_pattern_engine_proposal_only,
        scenario_repeated_same_decision_evidence,
        scenario_multi_agent_alternating_loop_max_steps,
        scenario_missing_runtime_budget_fail_closed,
        scenario_budget_boundary_exact_cost_allowed_then_stop,
        scenario_cross_task_cost_is_not_session_budget,
        scenario_cross_task_cascade_drift_visible,
        scenario_parallel_multi_agent_drift_visible,
        scenario_session_reset_budget_bypass_visible,
        scenario_micro_task_flood_drift_visible,
    ]

    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")

    log.finish()
    out = log.write(LOG_DIR)
    print("\nRUNTIME / AUDIT EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    os._exit(main())
