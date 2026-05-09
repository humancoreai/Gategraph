"""
WHY: Evidence that Pattern Engine triage improves reviewer ordering without granting autonomy.
INV: Priority/score are advisory metadata only; rules, policies, budgets, secrets, and tokens remain unchanged.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import reset_db, get_connection, seed_rules, ensure_pattern_schema
from src import event_logger, pattern_engine


def fresh_db():
    reset_db()
    conn = get_connection()
    ensure_pattern_schema(conn)
    with conn:
        seed_rules(conn)
    return conn


def add_external_api_block(conn, idx, *, stage="http_policy", reason="http endpoint not allowlisted: evil.example/v1", capability="api_call"):
    task_id = f"PPS-TASK-{idx}"
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES (?, 'api_operation', '["api_call"]', 'local', 'internal', 0, datetime('now'))
            """,
            (task_id,),
        )
    if stage == "http_policy":
        evaluation = {
            "pipeline_stage": "action_ready",
            "pipeline_decision": "continue",
            "pipeline_reason": "all guards passed",
            "http_policy": {"allowed": False, "reason": reason, "policy_id": None},
            "secret_resolution": {"required": False},
        }
    else:
        evaluation = {
            "pipeline_stage": "action_ready",
            "pipeline_decision": "continue",
            "pipeline_reason": "all guards passed",
            "http_policy": {"allowed": True, "reason": "http policy allowed", "policy_id": "POL-1"},
            "secret_resolution": {"allowed": False, "reason": reason, "secret_ref_id": "SEC-MISSING"},
        }
    event_logger.log_event(
        conn,
        event_id=f"PPS-EVT-{idx}",
        idempotency_key=f"pps:{idx}",
        correlation_id=f"PPS-COR-{idx}",
        causation_id=None,
        event_type="external_api_call",
        task_id=task_id,
        actor_component="external_api_adapter",
        input_data={"requested_capability": capability, "endpoint": "https://evil.example/v1", "method": "POST"},
        evaluation=evaluation,
        decision={"status": "blocked", "response_summary": reason},
    )


def add_enforcement_rejection(conn, idx, *, reason="capability token invalid signature: TOK-X", capability="api_call"):
    task_id = f"PPS-ENF-TASK-{idx}"
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES (?, 'api_operation', '["api_call"]', 'local', 'internal', 0, datetime('now'))
            """,
            (task_id,),
        )
    event_logger.log_event(
        conn,
        event_id=f"PPS-ENF-EVT-{idx}",
        idempotency_key=f"pps-enf:{idx}",
        correlation_id=f"PPS-ENF-COR-{idx}",
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


def test_a_critical_signature_gets_p0_priority():
    conn = fresh_db()
    try:
        for i in range(1, 6):
            add_enforcement_rejection(conn, i, reason="capability token invalid signature: TOK-X")
        before_rules = pattern_engine.active_rule_count(conn)
        result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.6)
        after_rules = pattern_engine.active_rule_count(conn)
        assert_true(result.proposals_created == 1, f"expected 1 proposal, got {result.proposals_created}")
        proposal = result.proposals[0]
        assert_true(proposal.priority == "P0", f"expected P0, got {proposal.priority}")
        assert_true(proposal.score >= 85.0, f"expected high score, got {proposal.score}")
        assert_true("severity=critical" in proposal.score_basis, "score basis should preserve critical context")
        assert_true(before_rules == after_rules, "scoring must not mutate rules")
    finally:
        conn.close()


def test_b_http_policy_pattern_gets_review_priority_without_allowlist_change():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_external_api_block(conn, i, stage="http_policy")
        result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        proposal = result.proposals[0]
        assert_true(proposal.priority in {"P1", "P2"}, f"expected review priority, got {proposal.priority}")
        assert_true(proposal.score > 0, "proposal should carry non-zero score")
        assert_true("do not widen allowlists automatically" in proposal.proposed_change, "must not auto-widen allowlists")
    finally:
        conn.close()


def test_c_more_support_increases_score_for_same_pattern():
    conn_low = fresh_db()
    try:
        for i in range(1, 4):
            add_external_api_block(conn_low, i, stage="secret_provider", reason="secret value unavailable: API_KEY")
        low = pattern_engine.analyze_audit_patterns(conn_low, min_events=3, confidence_threshold=0.75).proposals[0]
    finally:
        conn_low.close()

    conn_high = fresh_db()
    try:
        for i in range(1, 9):
            add_external_api_block(conn_high, i, stage="secret_provider", reason="secret value unavailable: API_KEY")
        high = pattern_engine.analyze_audit_patterns(conn_high, min_events=3, confidence_threshold=0.75).proposals[0]
        assert_true(high.score > low.score, f"expected support to increase score, low={low.score}, high={high.score}")
    finally:
        conn_high.close()


def test_d_priority_metadata_persisted_and_pending_only():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_enforcement_rejection(conn, i, reason="token PI is bound to task A, not B")
        result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        proposal = result.proposals[0]
        row = conn.execute(
            "SELECT priority, score, score_basis, status FROM proposals WHERE proposal_id = ?",
            (proposal.proposal_id,),
        ).fetchone()
        assert_true(row["priority"] == proposal.priority, "priority should persist")
        assert_true(float(row["score"]) == proposal.score, "score should persist")
        assert_true("support=" in row["score_basis"], "score_basis should persist review evidence")
        assert_true(row["status"] == "pending_review", "proposal must remain pending_review")
    finally:
        conn.close()


def main():
    tests = [
        ("A critical signature pattern gets P0", test_a_critical_signature_gets_p0_priority),
        ("B HTTP policy pattern gets advisory review priority", test_b_http_policy_pattern_gets_review_priority_without_allowlist_change),
        ("C support increases score", test_c_more_support_increases_score_for_same_pattern),
        ("D priority metadata persisted pending-only", test_d_priority_metadata_persisted_and_pending_only),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as exc:
            print(f"✗ {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print("\nPATTERN PRIORITY SCORING EVIDENCE REPORT")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
