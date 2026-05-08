"""
WHY: Runtime Guard tests verify loop/cost/time boundaries before Governance work happens.
INV: stop decisions must fail closed and must not require Governance evaluation.
"""
import os, sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection, seed_rules, ensure_runtime_schema
from src import runtime_guard
import src.event_logger as event_logger


def fresh_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "governance.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()
    conn = get_connection()
    ensure_runtime_schema(conn)
    with conn:
        seed_rules(conn)
    return conn


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_a_within_budget():
    conn = fresh_db()
    runtime_guard.create_budget(conn, task_id="RT-A", max_steps=3, max_cost_units=10)
    d = runtime_guard.evaluate_before_step(
        conn, task_id="RT-A", actor_id="agent-a", action_type="read_files", target="README.md", cost_units=1
    )
    assert_true(d.decision == "continue", f"expected continue, got {d}")
    assert_true(d.remaining_steps == 2, "remaining steps should decrement")
    conn.close()


def test_b_max_steps_exceeded():
    conn = fresh_db()
    runtime_guard.create_budget(conn, task_id="RT-B", max_steps=1, max_cost_units=10)
    d1 = runtime_guard.evaluate_before_step(conn, task_id="RT-B", actor_id="a", action_type="read", target="x")
    d2 = runtime_guard.evaluate_before_step(conn, task_id="RT-B", actor_id="a", action_type="read", target="y")
    assert_true(d1.decision == "continue", "first step should continue")
    assert_true(d2.decision == "stop", "second step should stop on max_steps")
    conn.close()


def test_c_max_runtime_exceeded():
    conn = fresh_db()
    runtime_guard.create_budget(conn, task_id="RT-C", max_runtime_seconds=1)
    old = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    with conn:
        conn.execute("UPDATE runtime_budgets SET created_at = ? WHERE task_id = ?", (old, "RT-C"))
    d = runtime_guard.evaluate_before_step(conn, task_id="RT-C", actor_id="a", action_type="read", target="x")
    assert_true(d.decision == "stop", "expired runtime should stop")
    conn.close()


def test_d_max_cost_exceeded():
    conn = fresh_db()
    runtime_guard.create_budget(conn, task_id="RT-D", max_steps=10, max_cost_units=3)
    d1 = runtime_guard.evaluate_before_step(conn, task_id="RT-D", actor_id="a", action_type="model_call", target="x", cost_units=2)
    d2 = runtime_guard.evaluate_before_step(conn, task_id="RT-D", actor_id="a", action_type="model_call", target="y", cost_units=2)
    assert_true(d1.decision == "continue", "first cost should continue")
    assert_true(d2.decision == "stop", "cost overflow should stop")
    conn.close()


def test_e_repeated_action_loop():
    conn = fresh_db()
    runtime_guard.create_budget(conn, task_id="RT-E", max_steps=10, max_cost_units=20, repeated_action_limit=2)
    d1 = runtime_guard.evaluate_before_step(conn, task_id="RT-E", actor_id="a", action_type="message", target="b")
    d2 = runtime_guard.evaluate_before_step(conn, task_id="RT-E", actor_id="a", action_type="message", target="b")
    d3 = runtime_guard.evaluate_before_step(conn, task_id="RT-E", actor_id="a", action_type="message", target="b")
    assert_true(d1.decision == "continue", "first repeated action should continue")
    assert_true(d2.decision == "continue", "second repeated action should continue")
    assert_true(d3.decision == "stop", "third repeated action should stop when limit=2")
    conn.close()


def test_f_stop_prevents_governance_call():
    conn = fresh_db()
    runtime_guard.create_budget(conn, task_id="RT-F", max_steps=0, max_cost_units=10)
    before_events = event_logger.count_events(conn)
    d = runtime_guard.evaluate_before_step(conn, task_id="RT-F", actor_id="a", action_type="read_files", target="README.md")
    after_events = event_logger.count_events(conn)
    assert_true(d.decision == "stop", "runtime stop expected before governance")
    assert_true(before_events == after_events, "no governance event should be created by Runtime Guard stop")
    conn.close()


def main():
    tests = [
        ("A within budget", test_a_within_budget),
        ("B max steps exceeded", test_b_max_steps_exceeded),
        ("C max runtime exceeded", test_c_max_runtime_exceeded),
        ("D max cost exceeded", test_d_max_cost_exceeded),
        ("E repeated action loop", test_e_repeated_action_loop),
        ("F stop prevents governance call", test_f_stop_prevents_governance_call),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {type(e).__name__}: {e}")
            failed += 1

    print("\nRUNTIME GUARD TEST REPORT")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
