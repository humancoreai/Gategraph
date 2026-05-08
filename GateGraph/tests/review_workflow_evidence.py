"""
WHY: Evidence that Review Workflow adds explicit human/process gates without auto-applying proposals.
INV: approving/rejecting a proposal must not mutate rules, policies, secrets, tokens, budgets, or actions.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import reset_db, get_connection, seed_rules, ensure_pattern_schema, ensure_review_schema
from src import event_logger, pattern_engine, review_workflow


def fresh_db():
    reset_db()
    conn = get_connection()
    ensure_pattern_schema(conn)
    ensure_review_schema(conn)
    with conn:
        seed_rules(conn)
    return conn


def add_enforcement_rejection(conn, idx, *, reason="capability token invalid signature: TOK-X", capability="api_call"):
    task_id = f"RVW-TASK-{idx}"
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
        event_id=f"RVW-EVT-{idx}",
        idempotency_key=f"rvw:{idx}",
        correlation_id=f"RVW-COR-{idx}",
        causation_id=None,
        event_type="enforcement_rejection",
        task_id=task_id,
        actor_component="enforcement_layer",
        input_data={"requested_capability": capability},
        evaluation={"check": "capability_token_validation"},
        decision={"status": "block", "reason": reason},
    )


def make_proposal(conn, *, reason="capability token invalid signature: TOK-X"):
    for i in range(1, 4):
        add_enforcement_rejection(conn, i, reason=reason)
    result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
    return result.proposals[0]


def count_table(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_a_pending_reviews_are_ordered_for_human_review():
    conn = fresh_db()
    try:
        p0 = make_proposal(conn, reason="capability token invalid signature: TOK-X")
        # Create a lower-priority proposal manually so ordering can be checked without complex event setup.
        with conn:
            conn.execute(
                """
                INSERT INTO proposals
                  (proposal_id, schema_version, proposal_type, target_rule_id, reason, proposed_change,
                   supporting_events, confidence, confidence_basis, priority, score, score_basis, status, created_at)
                VALUES ('LOW-RVW-1', '0.8.21', 'manual_test', NULL, 'low priority item', 'review only',
                        '[]', 0.1, 'manual', 'P3', 10.0, 'manual', 'pending_review', datetime('now'))
                """
            )
        pending = review_workflow.list_pending_reviews(conn)
        assert_true(pending[0].proposal_id == p0.proposal_id, "P0/high-score proposal should appear first")
    finally:
        conn.close()


def test_b_approval_records_review_without_auto_apply():
    conn = fresh_db()
    try:
        proposal = make_proposal(conn)
        before_rules = count_table(conn, "rules")
        before_policies = count_table(conn, "api_endpoint_policies")
        before_secrets = count_table(conn, "secret_refs")
        review = review_workflow.decide_proposal(
            conn,
            proposal_id=proposal.proposal_id,
            reviewer_id="human-reviewer",
            decision="approved_for_manual_action",
            rationale="Valid security signal; create a manual ticket, do not auto-apply.",
        )
        row = conn.execute("SELECT status FROM proposals WHERE proposal_id = ?", (proposal.proposal_id,)).fetchone()
        assert_true(row["status"] == "approved_for_manual_action", "proposal should be marked approved for manual action")
        assert_true(review.review_id.startswith("REV-"), "review decision should have review id")
        assert_true(count_table(conn, "rules") == before_rules, "approval must not mutate rules")
        assert_true(count_table(conn, "api_endpoint_policies") == before_policies, "approval must not mutate policies")
        assert_true(count_table(conn, "secret_refs") == before_secrets, "approval must not mutate secrets")
    finally:
        conn.close()


def test_c_rejection_records_review_without_auto_apply():
    conn = fresh_db()
    try:
        proposal = make_proposal(conn, reason="token PI is bound to task A, not B")
        before_rules = count_table(conn, "rules")
        review_workflow.decide_proposal(
            conn,
            proposal_id=proposal.proposal_id,
            reviewer_id="human-reviewer",
            decision="rejected",
            rationale="Known test traffic; no governance change required.",
        )
        row = conn.execute("SELECT status FROM proposals WHERE proposal_id = ?", (proposal.proposal_id,)).fetchone()
        assert_true(row["status"] == "rejected", "proposal should be rejected")
        assert_true(count_table(conn, "rules") == before_rules, "rejection must not mutate rules")
    finally:
        conn.close()


def test_d_double_review_is_blocked_fail_closed():
    conn = fresh_db()
    try:
        proposal = make_proposal(conn)
        review_workflow.decide_proposal(
            conn,
            proposal_id=proposal.proposal_id,
            reviewer_id="reviewer-a",
            decision="rejected",
            rationale="First final review decision.",
        )
        try:
            review_workflow.decide_proposal(
                conn,
                proposal_id=proposal.proposal_id,
                reviewer_id="reviewer-b",
                decision="approved_for_manual_action",
                rationale="Second decision should not be accepted.",
            )
        except review_workflow.ReviewWorkflowError:
            return
        raise AssertionError("double review should fail closed")
    finally:
        conn.close()


def test_e_invalid_review_inputs_fail_closed():
    conn = fresh_db()
    try:
        proposal = make_proposal(conn)
        for kwargs in [
            dict(reviewer_id="", decision="rejected", rationale="x"),
            dict(reviewer_id="r", decision="auto_apply", rationale="x"),
            dict(reviewer_id="r", decision="rejected", rationale=""),
        ]:
            try:
                review_workflow.decide_proposal(conn, proposal_id=proposal.proposal_id, **kwargs)
            except review_workflow.ReviewWorkflowError:
                continue
            raise AssertionError(f"invalid review input should fail: {kwargs}")
    finally:
        conn.close()


def main():
    tests = [
        ("A pending reviews ordered for human review", test_a_pending_reviews_are_ordered_for_human_review),
        ("B approval records review without auto-apply", test_b_approval_records_review_without_auto_apply),
        ("C rejection records review without auto-apply", test_c_rejection_records_review_without_auto_apply),
        ("D double review fails closed", test_d_double_review_is_blocked_fail_closed),
        ("E invalid review inputs fail closed", test_e_invalid_review_inputs_fail_closed),
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
    print("\nREVIEW WORKFLOW EVIDENCE REPORT")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
