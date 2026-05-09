"""
WHY: Phase F proves deterministic guard order without changing Governance/Enforcement/Runtime semantics.
INV: one authoritative stop stage is expected for each pipeline decision.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard, guard_orchestrator
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_session_evidence, collect_task_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_orchestration_", suffix=".db", delete=False)
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


def runtime_decision_count(evidence: dict) -> int:
    return len(evidence.get("runtime_decisions", []))


def scenario_enforcement_blocks_before_budget_guards() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "ORCH-ENFORCEMENT-FIRST"
    task_id = "ORCH-ENFORCEMENT-BLOCK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100, max_session_tasks=10, max_agent_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=50)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=False,
            enforcement_reason="no capability token provided",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            target="x",
            projected_cost_units=1,
        )
        session_ev = collect_session_evidence(conn, session_id)
        task_ev = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and decision.stage == "enforcement" and len(session_ev["session_budget_decisions"]) == 0 and runtime_decision_count(task_ev) == 0
        return EvidenceScenarioResult(
            test_name="enforcement_blocks_before_budget_guards",
            description="If Enforcement blocks, Session/Runtime guards must not spend or create misleading stop reasons.",
            expected={"stage": "enforcement", "session_decisions": 0, "runtime_decisions": 0},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "session_decisions": len(session_ev["session_budget_decisions"]), "runtime_decisions": runtime_decision_count(task_ev)},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Guard pipeline did not prioritize Enforcement block cleanly."],
            evidence={"session": session_ev, "task": task_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_session_stops_before_runtime_guard() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "ORCH-SESSION-FIRST"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=5, max_session_tasks=10, max_agent_cost_units=100)

        # Consume session budget with an already linked task.
        prior_task = "ORCH-SESSION-PRIOR"
        runtime_guard.create_budget(conn, task_id=prior_task, max_steps=5, max_cost_units=100)
        sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=prior_task, actor_id="agent-a", projected_cost_units=5)
        assert sd.decision == "continue"
        rd = runtime_guard.evaluate_before_step(conn, task_id=prior_task, actor_id="agent-a", action_type="model_call", target="prior", cost_units=5)
        assert rd.decision == "continue"

        task_id = "ORCH-SESSION-STOP"
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=100)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            target="next",
            projected_cost_units=1,
        )

        session_ev = collect_session_evidence(conn, session_id)
        task_ev = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and decision.stage == "session_budget" and "max_session_cost_units" in decision.reason and runtime_decision_count(task_ev) == 0
        return EvidenceScenarioResult(
            test_name="session_stops_before_runtime_guard",
            description="Exhausted session budget must stop before per-task Runtime Guard is evaluated.",
            expected={"stage": "session_budget", "runtime_decisions_for_stopped_task": 0},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "runtime_decisions_for_stopped_task": runtime_decision_count(task_ev)},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Runtime Guard ran after a session stop or stop stage was wrong."],
            evidence={"session": session_ev, "task": task_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_runtime_stops_when_session_allows() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "ORCH-RUNTIME-STOP"
    task_id = "ORCH-RUNTIME-STOP-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100, max_session_tasks=10, max_agent_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=0, max_cost_units=100)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            target="x",
            projected_cost_units=1,
        )
        session_ev = collect_session_evidence(conn, session_id)
        task_ev = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and decision.stage == "runtime_guard" and "max_steps" in decision.reason and len(session_ev["session_task_links"]) == 1 and runtime_decision_count(task_ev) == 1
        return EvidenceScenarioResult(
            test_name="runtime_stops_when_session_allows",
            description="Runtime Guard must stop when session budget allows but per-task budget is exhausted.",
            expected={"stage": "runtime_guard", "session_link_created": True, "runtime_decisions": 1},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "session_links": len(session_ev["session_task_links"]), "runtime_decisions": runtime_decision_count(task_ev)},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Runtime stop not correctly represented after session allow."],
            evidence={"session": session_ev, "task": task_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_both_session_and_runtime_would_stop_session_priority() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "ORCH-BOTH-STOP"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=1, max_session_tasks=10, max_agent_cost_units=100)

        prior_task = "ORCH-BOTH-PRIOR"
        runtime_guard.create_budget(conn, task_id=prior_task, max_steps=5, max_cost_units=100)
        sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=prior_task, actor_id="agent-a", projected_cost_units=1)
        assert sd.decision == "continue"
        rd = runtime_guard.evaluate_before_step(conn, task_id=prior_task, actor_id="agent-a", action_type="model_call", target="prior", cost_units=1)
        assert rd.decision == "continue"

        task_id = "ORCH-BOTH-NEW"
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=0, max_cost_units=100)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            target="new",
            projected_cost_units=1,
        )

        session_ev = collect_session_evidence(conn, session_id)
        task_ev = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and decision.stage == "session_budget" and "max_session_cost_units" in decision.reason and runtime_decision_count(task_ev) == 0
        return EvidenceScenarioResult(
            test_name="both_session_and_runtime_would_stop_session_priority",
            description="When both would stop, Session Budget has deterministic priority and Runtime Guard is not evaluated.",
            expected={"stage": "session_budget", "runtime_decisions_for_new_task": 0},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "runtime_decisions_for_new_task": runtime_decision_count(task_ev)},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Stop priority is not deterministic or Runtime Guard ran unnecessarily."],
            evidence={"session": session_ev, "task": task_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_all_guards_pass_action_ready() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "ORCH-ALL-PASS"
    task_id = "ORCH-ALL-PASS-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100, max_session_tasks=10, max_agent_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=100)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            target="x",
            projected_cost_units=3,
        )
        session_ev = collect_session_evidence(conn, session_id)
        task_ev = collect_task_evidence(conn, task_id)
        passed = decision.decision == "continue" and decision.stage == "action_ready" and len(session_ev["session_task_links"]) == 1 and runtime_decision_count(task_ev) == 1
        return EvidenceScenarioResult(
            test_name="all_guards_pass_action_ready",
            description="Only if Enforcement, Session Budget and Runtime Guard all pass may action become ready.",
            expected={"decision": "continue", "stage": "action_ready"},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "session_links": len(session_ev["session_task_links"]), "runtime_decisions": runtime_decision_count(task_ev)},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Pipeline did not reach action_ready cleanly."],
            evidence={"session": session_ev, "task": task_ev},
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("guard_orchestration_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_enforcement_blocks_before_budget_guards,
        scenario_session_stops_before_runtime_guard,
        scenario_runtime_stops_when_session_allows,
        scenario_both_session_and_runtime_would_stop_session_priority,
        scenario_all_guards_pass_action_ready,
    ]

    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")

    log.finish()
    out = log.write(LOG_DIR)
    print("\nGUARD ORCHESTRATION EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    os._exit(main())
