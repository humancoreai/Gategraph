"""
WHY: Evidence for v0.8.38 Runtime Cost Governance / Kill Conditions.
INV: Tests prove earlier fail-closed runtime stops without changing the API contract or core decisions.
SEC: projected cost, projected steps, deterministic loop signals, and degraded-mode throttling must stop before another step is recorded.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence
from src.database import ensure_pattern_schema, ensure_runtime_schema, get_connection, init_db, seed_rules
from src import runtime_guard
from src.reason_normalizer import normalize_as_dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_runtime_cost_governance_", suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()
    init_db(Path(db_path))
    conn = get_connection(Path(db_path))
    seed_rules(conn); ensure_runtime_schema(conn); ensure_pattern_schema(conn)
    return conn, db_path


def close_conn(conn, db_path: str) -> None:
    conn.close()
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


def result(name, desc, expected, actual, passed, evidence=None):
    return EvidenceScenarioResult(
        name,
        desc,
        expected,
        actual,
        passed,
        "info" if passed else "critical",
        [] if passed else [f"{name} failed"],
        evidence or {},
    )


def scenario_projected_cost_stops_before_step():
    conn, db_path = fresh_conn(); task_id = "RCG-PROJECTED-COST"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=5)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="a", cost_units=8)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="b", cost_units=3)
        ev = collect_task_evidence(conn, task_id)
        norm = normalize_as_dict("runtime_guard", d2.reason)
        passed = d1.decision == "continue" and d2.decision == "stop" and norm["code"] == "RT_PROJECTED_COST_LIMIT" and len(ev["runtime_steps"]) == 1
        return result("projected_cost_stops_before_step", "Projected per-task cost overrun stops before recording another runtime step.", {"second_code": "RT_PROJECTED_COST_LIMIT", "runtime_steps": 1}, {"decisions": [d1.decision, d2.decision], "reason": d2.reason, "code": norm["code"], "runtime_steps": len(ev["runtime_steps"])}, passed, ev)
    finally:
        close_conn(conn, db_path)


def scenario_projected_step_stops_before_step():
    conn, db_path = fresh_conn(); task_id = "RCG-PROJECTED-STEPS"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=1, max_cost_units=10, repeated_action_limit=5)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="tool", target="a", cost_units=1)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="tool", target="b", cost_units=1)
        ev = collect_task_evidence(conn, task_id)
        norm = normalize_as_dict("runtime_guard", d2.reason)
        passed = d1.decision == "continue" and d2.decision == "stop" and norm["code"] in {"RT_PROJECTED_STEP_LIMIT", "RT_STEP_LIMIT"} and len(ev["runtime_steps"]) == 1
        return result("projected_step_stops_before_step", "Projected step overrun stops before recording another runtime step.", {"second_code": "RT_PROJECTED_STEP_LIMIT|RT_STEP_LIMIT", "runtime_steps": 1}, {"decisions": [d1.decision, d2.decision], "reason": d2.reason, "code": norm["code"], "runtime_steps": len(ev["runtime_steps"])}, passed, ev)
    finally:
        close_conn(conn, db_path)


def scenario_loop_kill_condition_normalized():
    conn, db_path = fresh_conn(); task_id = "RCG-LOOP-KILL"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=20, repeated_action_limit=2)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b", cost_units=1)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b", cost_units=1)
        d3 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b", cost_units=1)
        ev = collect_task_evidence(conn, task_id)
        norm = normalize_as_dict("runtime_guard", d3.reason)
        passed = [d1.decision, d2.decision, d3.decision] == ["continue", "continue", "stop"] and norm["code"] == "RT_LOOP_DETECTED" and len(ev["runtime_steps"]) == 2
        return result("loop_kill_condition_normalized", "Repeated structural action reaches deterministic loop kill condition and normalizes to a stable reason code.", {"third_code": "RT_LOOP_DETECTED", "runtime_steps": 2}, {"decisions": [d1.decision, d2.decision, d3.decision], "reason": d3.reason, "code": norm["code"], "runtime_steps": len(ev["runtime_steps"])}, passed, ev)
    finally:
        close_conn(conn, db_path)


def scenario_degraded_projection_throttles_high_cost():
    conn, db_path = fresh_conn(); task_id = "RCG-DEGRADED-THROTTLE"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=20, max_cost_units=10, repeated_action_limit=10)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="a", cost_units=7)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="b", cost_units=2)
        ev = collect_task_evidence(conn, task_id)
        norm = normalize_as_dict("runtime_guard", d2.reason)
        passed = d1.decision == "continue" and d2.decision == "stop" and d2.escalation_state == "degraded" and norm["code"] == "RT_PROJECTED_COST_THROTTLED" and len(ev["runtime_steps"]) == 1
        return result("degraded_projection_throttles_high_cost", "Above the 70% runtime threshold, projected high-cost follow-up work is killed before execution.", {"second_code": "RT_PROJECTED_COST_THROTTLED", "state": "degraded", "runtime_steps": 1}, {"decisions": [d1.decision, d2.decision], "state": d2.escalation_state, "max_cost_for_action": d2.max_cost_for_action, "reason": d2.reason, "code": norm["code"], "runtime_steps": len(ev["runtime_steps"])}, passed, ev)
    finally:
        close_conn(conn, db_path)


def scenario_normal_task_not_false_positive():
    conn, db_path = fresh_conn(); task_id = "RCG-NORMAL-NO-FALSE-POSITIVE"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=20, repeated_action_limit=5)
        decisions = [
            runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="read", target=f"file-{i}", cost_units=1)
            for i in range(3)
        ]
        ev = collect_task_evidence(conn, task_id)
        passed = all(d.decision == "continue" for d in decisions) and len(ev["runtime_steps"]) == 3
        return result("normal_task_not_false_positive", "Distinct low-cost steps remain allowed; the new guard must not create broad false positives.", {"decisions": ["continue", "continue", "continue"], "runtime_steps": 3}, {"decisions": [d.decision for d in decisions], "runtime_steps": len(ev["runtime_steps"])}, passed, ev)
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("runtime_cost_governance_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_projected_cost_stops_before_step,
        scenario_projected_step_stops_before_step,
        scenario_loop_kill_condition_normalized,
        scenario_degraded_projection_throttles_high_cost,
        scenario_normal_task_not_false_positive,
    ]
    for scenario in scenarios:
        r = scenario(); log.add(r)
        print(f"{'✓' if r.passed else '✗'} {r.test_name}: {r.actual}")
    log.finish()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / f"{run_id}.json"
    out = log.write(LOG_DIR)
    print("\nRUNTIME COST GOVERNANCE EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
