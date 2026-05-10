"""
WHY: v0.8 evidence proves cross-task/session/global budget stops without changing core governance semantics.
INV: Session Budget Guard never grants capabilities; it can only stop before fresh per-task runtime work.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence, collect_session_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_session_budget_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    ensure_runtime_schema(conn)
    ensure_pattern_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    with conn:
        seed_rules(conn)
    return conn, db_path


def close_conn(conn, db_path: Path) -> None:
    conn.close()
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


def run_allowed_runtime_step(conn, *, task_id: str, actor_id: str, cost_units: int) -> None:
    runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=100, repeated_action_limit=10)
    decision = runtime_guard.evaluate_before_step(
        conn,
        task_id=task_id,
        actor_id=actor_id,
        action_type="model_call",
        target=task_id,
        cost_units=cost_units,
    )
    assert decision.decision == "continue", decision


def scenario_cross_task_cascade_stopped_by_session_budget() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SES-CASCADE"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=30, max_session_tasks=20, max_agent_cost_units=100)
        decisions = []
        for idx in range(1, 21):
            task_id = f"V08-CASCADE-{idx:02d}"
            projected = 4
            sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=task_id, actor_id="agent-cascade", projected_cost_units=projected)
            decisions.append(sd)
            if sd.decision == "stop":
                break
            run_allowed_runtime_step(conn, task_id=task_id, actor_id="agent-cascade", cost_units=projected)

        evidence = collect_session_evidence(conn, session_id)
        final = decisions[-1]
        passed = final.decision == "stop" and "max_session_cost_units" in final.reason and len(evidence["session_task_links"]) == 7
        return EvidenceScenarioResult(
            test_name="cross_task_cascade_stopped_by_session_budget",
            description="Cross-task cost cascade must stop once cumulative session budget is exceeded.",
            expected={"final_decision": "stop", "reason_contains": "max_session_cost_units", "linked_tasks_before_stop": 7},
            actual={"final_decision": final.decision, "final_reason": final.reason, "linked_tasks": len(evidence["session_task_links"])},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Session budget did not stop cross-task cascade as expected."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_parallel_multi_agent_stopped_by_session_budget() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SES-PARALLEL"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=24, max_session_tasks=50, max_agent_cost_units=100)
        decisions = []
        stopped = None
        for agent_idx in range(1, 4):
            for task_idx in range(1, 6):
                task_id = f"V08-PAR-A{agent_idx}-T{task_idx}"
                projected = 3
                sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=task_id, actor_id=f"agent-{agent_idx}", projected_cost_units=projected)
                decisions.append(sd)
                if sd.decision == "stop":
                    stopped = sd
                    break
                run_allowed_runtime_step(conn, task_id=task_id, actor_id=f"agent-{agent_idx}", cost_units=projected)
            if stopped:
                break

        evidence = collect_session_evidence(conn, session_id)
        passed = stopped is not None and stopped.decision == "stop" and "max_session_cost_units" in stopped.reason and len(evidence["session_task_links"]) == 8
        return EvidenceScenarioResult(
            test_name="parallel_multi_agent_stopped_by_session_budget",
            description="Multi-agent aggregate cost must stop at the session budget.",
            expected={"final_decision": "stop", "reason_contains": "max_session_cost_units", "linked_tasks_before_stop": 8},
            actual={"final_decision": stopped.decision if stopped else None, "final_reason": stopped.reason if stopped else None, "linked_tasks": len(evidence["session_task_links"])},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Session budget did not stop aggregate multi-agent drift."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_session_reset_continuity_stopped() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SES-RESET-CONTINUITY"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=10, max_session_tasks=10, max_agent_cost_units=100)

        d1 = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id="V08-RESET-1", actor_id="agent-reset", projected_cost_units=9)
        if d1.decision == "continue":
            run_allowed_runtime_step(conn, task_id="V08-RESET-1", actor_id="agent-reset", cost_units=9)

        d2 = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id="V08-RESET-2", actor_id="agent-reset", projected_cost_units=9)

        evidence = collect_session_evidence(conn, session_id)
        passed = d1.decision == "continue" and d2.decision == "stop" and "max_session_cost_units" in d2.reason and len(evidence["session_task_links"]) == 1
        return EvidenceScenarioResult(
            test_name="session_reset_continuity_stopped",
            description="Fresh task/runtime budget must not bypass cumulative session budget continuity.",
            expected={"first_decision": "continue", "second_decision": "stop", "reason_contains": "max_session_cost_units"},
            actual={"first_decision": d1.decision, "second_decision": d2.decision, "second_reason": d2.reason, "linked_tasks": len(evidence["session_task_links"])},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Session reset continuity gap remains open."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_micro_task_flood_stopped_by_session_budget() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SES-MICRO-FLOOD"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=25, max_session_tasks=200, max_agent_cost_units=100)
        stopped = None
        for idx in range(1, 101):
            task_id = f"V08-MICRO-{idx:03d}"
            sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=task_id, actor_id="agent-flood", projected_cost_units=1)
            if sd.decision == "stop":
                stopped = sd
                break
            run_allowed_runtime_step(conn, task_id=task_id, actor_id="agent-flood", cost_units=1)

        evidence = collect_session_evidence(conn, session_id)
        passed = stopped is not None and stopped.decision == "stop" and "max_session_cost_units" in stopped.reason and len(evidence["session_task_links"]) == 25
        return EvidenceScenarioResult(
            test_name="micro_task_flood_stopped_by_session_budget",
            description="Micro-task flood must stop once cumulative session budget is exceeded.",
            expected={"final_decision": "stop", "reason_contains": "max_session_cost_units", "linked_tasks_before_stop": 25},
            actual={"final_decision": stopped.decision if stopped else None, "final_reason": stopped.reason if stopped else None, "linked_tasks": len(evidence["session_task_links"])},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Micro-task flood was not stopped by session budget."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_agent_budget_stops_single_agent_drift() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SES-AGENT-LIMIT"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100, max_session_tasks=50, max_agent_cost_units=10)
        decisions = []
        for idx in range(1, 6):
            task_id = f"V08-AGENT-LIMIT-{idx}"
            sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=task_id, actor_id="agent-heavy", projected_cost_units=3)
            decisions.append(sd)
            if sd.decision == "stop":
                break
            run_allowed_runtime_step(conn, task_id=task_id, actor_id="agent-heavy", cost_units=3)

        evidence = collect_session_evidence(conn, session_id)
        final = decisions[-1]
        passed = final.decision == "stop" and "max_agent_cost_units" in final.reason and len(evidence["session_task_links"]) == 3
        return EvidenceScenarioResult(
            test_name="agent_budget_stops_single_agent_drift",
            description="Agent-level cumulative budget must stop one expensive actor even if session budget remains available.",
            expected={"final_decision": "stop", "reason_contains": "max_agent_cost_units", "linked_tasks_before_stop": 3},
            actual={"final_decision": final.decision, "final_reason": final.reason, "linked_tasks": len(evidence["session_task_links"])},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Agent-level budget did not stop per-agent drift."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_missing_session_budget_fail_closed() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SES-MISSING"
    try:
        decision = session_budget_guard.evaluate_before_task(
            conn,
            session_id=session_id,
            task_id="V08-MISSING-BUDGET",
            actor_id="agent-a",
            projected_cost_units=1,
        )
        evidence = collect_session_evidence(conn, session_id)
        passed = decision.decision == "stop" and "no session budget" in decision.reason and len(evidence["session_budget_decisions"]) == 1
        return EvidenceScenarioResult(
            test_name="missing_session_budget_fail_closed",
            description="Explicit session-budget evaluation must fail closed if no session budget exists.",
            expected={"decision": "stop", "reason_contains": "no session budget"},
            actual={"decision": decision.decision, "reason": decision.reason},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Missing session budget did not fail closed."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("session_budget_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_cross_task_cascade_stopped_by_session_budget,
        scenario_parallel_multi_agent_stopped_by_session_budget,
        scenario_session_reset_continuity_stopped,
        scenario_micro_task_flood_stopped_by_session_budget,
        scenario_agent_budget_stops_single_agent_drift,
        scenario_missing_session_budget_fail_closed,
    ]

    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")

    log.finish()
    out = log.write(LOG_DIR)
    print("\nSESSION BUDGET EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
