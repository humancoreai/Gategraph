"""
WHY: Reason normalization gives stable explain codes without changing guard decisions.
INV: raw reasons remain preserved; normalized fields are additive evidence/reporting metadata only.
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
from src.reason_normalizer import normalize_reason
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_session_evidence, collect_task_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_reason_norm_", suffix=".db", delete=False)
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


def scenario_normalizes_known_reasons() -> EvidenceScenarioResult:
    cases = [
        ("enforcement", "no capability token provided", "ENF_NO_TOKEN"),
        ("session_budget", "max_session_cost_units exceeded: 32 > 30", "SES_COST_LIMIT"),
        ("session_budget", "max_agent_cost_units exceeded: 12 > 10", "SES_AGENT_COST_LIMIT"),
        ("runtime_guard", "max_steps exceeded: 4 >= 4", "RT_STEP_LIMIT"),
        ("runtime_guard", "max_cost_units exceeded: 5 > 4", "RT_COST_LIMIT"),
        ("runtime_guard", "repeated_action_limit exceeded for signature 'x'", "RT_REPEATED_ACTION"),
        ("action_ready", "all guards passed", "OK_ACTION_READY"),
    ]
    actual = []
    for stage, reason, expected_code in cases:
        nr = normalize_reason(stage, reason)
        actual.append({"stage": stage, "reason": reason, "code": nr.code, "expected_code": expected_code, "raw_preserved": nr.raw_reason == reason})
    passed = all(row["code"] == row["expected_code"] and row["raw_preserved"] for row in actual)
    return EvidenceScenarioResult(
        test_name="normalizes_known_reasons",
        description="Known raw reasons map to stable codes while preserving raw text.",
        expected={"all_known_codes_match": True, "raw_reason_preserved": True},
        actual={"cases": actual},
        passed=passed,
        severity="info" if passed else "high",
        notes=[] if passed else ["At least one known reason failed to normalize deterministically."],
        evidence={"normalized_cases": actual},
    )


def scenario_unknown_reason_falls_back_safely() -> EvidenceScenarioResult:
    raw = "some new guard condition not classified yet"
    nr = normalize_reason("runtime_guard", raw)
    passed = nr.code == "RUNTIME_GUARD_UNCLASSIFIED" and nr.category == "unclassified" and nr.raw_reason == raw
    return EvidenceScenarioResult(
        test_name="unknown_reason_falls_back_safely",
        description="Unknown reasons must preserve raw text and use unclassified fallback instead of failing.",
        expected={"code": "RUNTIME_GUARD_UNCLASSIFIED", "category": "unclassified", "raw_preserved": True},
        actual={"code": nr.code, "category": nr.category, "raw_reason": nr.raw_reason},
        passed=passed,
        severity="info" if passed else "medium",
        notes=[] if passed else ["Unknown reason fallback is not safe/stable."],
        evidence={"normalized_reason": nr.__dict__},
    )


def scenario_orchestrator_outputs_normalized_enforcement_stop() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "RN-ENF"
    task_id = "RN-ENF-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id)
        runtime_guard.create_budget(conn, task_id=task_id)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=False,
            enforcement_reason="no capability token provided",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
        )
        passed = decision.decision == "stop" and decision.normalized_reason["code"] == "ENF_NO_TOKEN"
        return EvidenceScenarioResult(
            test_name="orchestrator_outputs_normalized_enforcement_stop",
            description="Orchestrator must attach normalized reason for Enforcement stops.",
            expected={"decision": "stop", "normalized_code": "ENF_NO_TOKEN"},
            actual={"decision": decision.decision, "stage": decision.stage, "normalized_reason": decision.normalized_reason},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Normalized Enforcement reason missing or wrong."],
            evidence={"pipeline_decision": decision.__dict__},
        )
    finally:
        close_conn(conn, db_path)


def scenario_orchestrator_outputs_normalized_session_stop() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "RN-SESSION"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=1, max_session_tasks=10, max_agent_cost_units=10)
        prior_task = "RN-SESSION-PRIOR"
        runtime_guard.create_budget(conn, task_id=prior_task)
        sd = session_budget_guard.evaluate_before_task(conn, session_id=session_id, task_id=prior_task, actor_id="agent-a", projected_cost_units=1)
        assert sd.decision == "continue"
        rd = runtime_guard.evaluate_before_step(conn, task_id=prior_task, actor_id="agent-a", action_type="model_call", cost_units=1)
        assert rd.decision == "continue"

        task_id = "RN-SESSION-STOP"
        runtime_guard.create_budget(conn, task_id=task_id)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            projected_cost_units=1,
        )
        evidence = collect_session_evidence(conn, session_id)
        passed = decision.decision == "stop" and decision.normalized_reason["code"] == "SES_COST_LIMIT"
        return EvidenceScenarioResult(
            test_name="orchestrator_outputs_normalized_session_stop",
            description="Orchestrator must attach normalized reason for Session Budget stops.",
            expected={"decision": "stop", "normalized_code": "SES_COST_LIMIT"},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "normalized_reason": decision.normalized_reason},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Normalized Session reason missing or wrong."],
            evidence={"pipeline_decision": decision.__dict__, "session": evidence},
        )
    finally:
        close_conn(conn, db_path)


def scenario_orchestrator_outputs_normalized_runtime_stop() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "RN-RUNTIME"
    task_id = "RN-RUNTIME-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=0)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            projected_cost_units=1,
        )
        evidence = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and decision.normalized_reason["code"] == "RT_STEP_LIMIT"
        return EvidenceScenarioResult(
            test_name="orchestrator_outputs_normalized_runtime_stop",
            description="Orchestrator must attach normalized reason for Runtime Guard stops.",
            expected={"decision": "stop", "normalized_code": "RT_STEP_LIMIT"},
            actual={"decision": decision.decision, "stage": decision.stage, "reason": decision.reason, "normalized_reason": decision.normalized_reason},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Normalized Runtime reason missing or wrong."],
            evidence={"pipeline_decision": decision.__dict__, "task": evidence},
        )
    finally:
        close_conn(conn, db_path)


def scenario_orchestrator_outputs_normalized_action_ready() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "RN-OK"
    task_id = "RN-OK-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=100)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id=session_id,
            task_id=task_id,
            actor_id="agent-a",
            action_type="model_call",
            projected_cost_units=1,
        )
        passed = decision.decision == "continue" and decision.normalized_reason["code"] == "OK_ACTION_READY"
        return EvidenceScenarioResult(
            test_name="orchestrator_outputs_normalized_action_ready",
            description="Successful pipeline pass must also have stable OK explain code.",
            expected={"decision": "continue", "normalized_code": "OK_ACTION_READY"},
            actual={"decision": decision.decision, "stage": decision.stage, "normalized_reason": decision.normalized_reason},
            passed=passed,
            severity="info" if passed else "medium",
            notes=[] if passed else ["Normalized action-ready reason missing or wrong."],
            evidence={"pipeline_decision": decision.__dict__},
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("reason_normalization_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_normalizes_known_reasons,
        scenario_unknown_reason_falls_back_safely,
        scenario_orchestrator_outputs_normalized_enforcement_stop,
        scenario_orchestrator_outputs_normalized_session_stop,
        scenario_orchestrator_outputs_normalized_runtime_stop,
        scenario_orchestrator_outputs_normalized_action_ready,
    ]

    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")

    log.finish()
    out = log.write(LOG_DIR)
    print("\nREASON NORMALIZATION EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    os._exit(main())
