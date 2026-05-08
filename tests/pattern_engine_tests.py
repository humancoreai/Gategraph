"""
WHY: Pattern Engine tests prove advisory learning without autonomous rule mutation.
INV: Pattern Engine creates proposals only; active rules must remain unchanged.
"""
import os, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import reset_db, get_connection, seed_rules, ensure_pattern_schema
from src import pattern_engine, event_logger


def fresh_db():
    reset_db()
    conn = get_connection()
    ensure_pattern_schema(conn)
    with conn:
        seed_rules(conn)
    return conn


def add_rejection(conn, idx, capability="write_files", reason="no capability token provided"):
    task_id = f"PAT-TASK-{idx}"
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
        event_id=f"PAT-EVT-{idx}",
        idempotency_key=f"pat:{idx}",
        correlation_id=f"PAT-COR-{idx}",
        causation_id=None,
        event_type="enforcement_rejection",
        task_id=task_id,
        actor_component="enforcement_layer",
        input_data={"requested_capability": capability},
        evaluation={"check": "capability_token_validation"},
        decision={"status": "block", "reason": reason},
    )


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_a_no_proposal_with_little_data():
    conn = fresh_db()
    try:
        add_rejection(conn, 1)
        add_rejection(conn, 2)
        before_rules = pattern_engine.active_rule_count(conn)
        result = pattern_engine.analyze_rejections(conn, min_events=3)
        after_rules = pattern_engine.active_rule_count(conn)
        assert_true(result.proposals_created == 0, "should not create proposal below min_events")
        assert_true(before_rules == after_rules, "rules must not change")
    finally:
        conn.close()


def test_b_proposal_for_repeated_rejections():
    conn = fresh_db()
    try:
        for i in range(1, 5):
            add_rejection(conn, i, capability="write_files", reason="no capability token provided")
        before_rules = pattern_engine.active_rule_count(conn)
        result = pattern_engine.analyze_rejections(conn, min_events=3, confidence_threshold=0.75)
        after_rules = pattern_engine.active_rule_count(conn)
        assert_true(result.proposals_created == 1, f"expected 1 proposal, got {result.proposals_created}")
        assert_true(pattern_engine.count_proposals(conn) == 1, "proposal should be persisted")
        assert_true(result.proposals[0].status == "pending_review", "proposal must require review")
        assert_true(result.proposals[0].confidence >= 0.75, "confidence should meet threshold")
        assert_true(before_rules == after_rules, "rules must not change")
    finally:
        conn.close()


def test_c_no_proposal_when_confidence_low():
    conn = fresh_db()
    try:
        add_rejection(conn, 1, capability="write_files", reason="no capability token provided")
        add_rejection(conn, 2, capability="delete_files", reason="no capability token provided")
        add_rejection(conn, 3, capability="api_call", reason="no capability token provided")
        add_rejection(conn, 4, capability="read_files", reason="token revoked")
        result = pattern_engine.analyze_rejections(conn, min_events=1, confidence_threshold=0.75)
        assert_true(result.proposals_created == 0, "distributed patterns should not pass high confidence threshold")
    finally:
        conn.close()


def main():
    tests = [
        ("A no proposal with little data", test_a_no_proposal_with_little_data),
        ("B proposal for repeated rejections", test_b_proposal_for_repeated_rejections),
        ("C no proposal when confidence low", test_c_no_proposal_when_confidence_low),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {type(e).__name__}: {e}")
            failed += 1
    print("\nPATTERN ENGINE TEST REPORT")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
