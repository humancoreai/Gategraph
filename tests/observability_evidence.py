"""
WHY: Evidence for v0.8.39 Observability / Explainability.
INV: Observability reconstructs existing runtime evidence only; it never changes decisions or records steps.
SEC: stop attribution and normalized reasons must be explicit for operator trust.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import observability, runtime_guard
from src.database import ensure_runtime_schema, get_connection, init_db, seed_rules


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_observability_", suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()
    init_db(Path(db_path))
    conn = get_connection(Path(db_path))
    seed_rules(conn)
    ensure_runtime_schema(conn)
    return conn, db_path


def close_conn(conn, db_path: str) -> None:
    conn.close()
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


def scenario_trace_cost_stop():
    conn, db_path = fresh_conn()
    task_id = "OBS-COST-STOP"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=4, max_cost_units=5, repeated_action_limit=4)
        d1 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="read", target="a", cost_units=3)
        d2 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="write", target="b", cost_units=3)
        trace = observability.reconstruct_decision_trace(conn, task_id)
        snapshot = observability.build_explain_snapshot(conn, task_id)
        timeline = observability.build_cost_timeline(conn, task_id)
        ok = (
            d1.decision == "continue"
            and d2.decision == "stop"
            and trace["guard_sequence"] == list(observability.GUARD_SEQUENCE)
            and trace["final"]["triggering_guard"] == "runtime_cost_guard"
            and trace["final"]["normalized_reason"]["code"] == "RT_PROJECTED_COST_LIMIT"
            and snapshot["final_decision"] == "stop"
            and snapshot["metrics"]["cost"] == 3
            and len(timeline) == 2
            and timeline[-1]["decision"] == "stop"
        )
        return ok, {"trace_final": trace["final"], "snapshot": snapshot, "timeline": timeline}
    finally:
        close_conn(conn, db_path)


def scenario_loop_aggregation():
    conn, db_path = fresh_conn()
    task_id = "OBS-LOOP-STOP"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=20, repeated_action_limit=2)
        runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b", cost_units=1)
        runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b", cost_units=1)
        d3 = runtime_guard.evaluate_before_step(conn, task_id=task_id, actor_id="agent-a", action_type="delegate", target="agent-b", cost_units=1)
        agg = observability.build_observability_aggregation(conn)
        ok = (
            d3.decision == "stop"
            and agg["loop_detection_count"] == 1
            and agg["stop_reason_distribution"].get("RT_LOOP_DETECTED") == 1
            and agg["guard_distribution"].get("runtime_cost_guard", 0) >= 1
        )
        return ok, {"decision": d3.decision, "reason": d3.reason, "aggregation": agg}
    finally:
        close_conn(conn, db_path)


def main() -> int:
    scenarios = [
        ("trace_cost_stop", scenario_trace_cost_stop),
        ("loop_aggregation", scenario_loop_aggregation),
    ]
    failed = 0
    for name, fn in scenarios:
        ok, actual = fn()
        print(f"{'✓' if ok else '✗'} {name}: {actual}")
        failed += 0 if ok else 1
    summary = {"passed": len(scenarios) - failed, "failed": failed}
    print(f"Summary: {summary}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
