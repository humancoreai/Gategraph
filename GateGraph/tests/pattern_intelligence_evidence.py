"""
WHY: Evidence for Pattern Engine intelligence must prove proposal-only learning across guard stages.
INV: Running the Pattern Engine must not mutate active rules, policies, budgets, secrets, tokens, or decisions.
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
    task_id = f"PI-TASK-{idx}"
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
    elif stage == "secret_provider":
        evaluation = {
            "pipeline_stage": "action_ready",
            "pipeline_decision": "continue",
            "pipeline_reason": "all guards passed",
            "http_policy": {"allowed": True, "reason": "http policy allowed", "policy_id": "POL-1"},
            "secret_resolution": {"allowed": False, "reason": reason, "secret_ref_id": "SEC-MISSING"},
        }
    else:
        evaluation = {"pipeline_stage": stage, "pipeline_decision": "block", "pipeline_reason": reason}
    event_logger.log_event(
        conn,
        event_id=f"PI-EVT-{idx}",
        idempotency_key=f"pi:{idx}",
        correlation_id=f"PI-COR-{idx}",
        causation_id=None,
        event_type="external_api_call",
        task_id=task_id,
        actor_component="external_api_adapter",
        input_data={"requested_capability": capability, "endpoint": "https://evil.example/v1", "method": "POST"},
        evaluation=evaluation,
        decision={"status": "blocked", "response_summary": reason},
    )


def add_enforcement_rejection(conn, idx, *, reason="capability token invalid signature: TOK-X", capability="api_call"):
    task_id = f"PI-ENF-TASK-{idx}"
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
        event_id=f"PI-ENF-EVT-{idx}",
        idempotency_key=f"pi-enf:{idx}",
        correlation_id=f"PI-ENF-COR-{idx}",
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


def test_a_http_policy_pattern_proposal_only():
    conn = fresh_db()
    try:
        for i in range(1, 5):
            add_external_api_block(conn, i, stage="http_policy")
        before_rules = pattern_engine.active_rule_count(conn)
        result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        after_rules = pattern_engine.active_rule_count(conn)
        assert_true(result.proposals_created == 1, f"expected 1 proposal, got {result.proposals_created}")
        proposal = result.proposals[0]
        assert_true(proposal.status == "pending_review", "proposal must remain pending_review")
        assert_true("http_policy" in proposal.reason, "proposal should identify HTTP policy stage")
        assert_true("do not widen allowlists automatically" in proposal.proposed_change, "proposal must not auto-widen policy")
        assert_true(before_rules == after_rules, "rules must not mutate")
    finally:
        conn.close()


def test_b_secret_provider_pattern_proposal_only():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_external_api_block(conn, i, stage="secret_provider", reason="secret value unavailable: API_KEY")
        result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        assert_true(result.proposals_created == 1, f"expected 1 proposal, got {result.proposals_created}")
        proposal = result.proposals[0]
        assert_true("secret_provider" in proposal.reason, "proposal should identify secret provider stage")
        assert_true("never expose or log raw secret values" in proposal.proposed_change, "secret proposal must retain leak guard")
    finally:
        conn.close()


def test_c_mixed_patterns_do_not_overfit():
    conn = fresh_db()
    try:
        add_external_api_block(conn, 1, stage="http_policy", reason="http endpoint not allowlisted: a.test/v1")
        add_external_api_block(conn, 2, stage="secret_provider", reason="secret ref not found: SEC-X")
        add_enforcement_rejection(conn, 3, reason="capability token invalid signature: TOK-X")
        add_enforcement_rejection(conn, 4, reason="token PI is bound to task A, not B")
        result = pattern_engine.analyze_audit_patterns(conn, min_events=1, confidence_threshold=0.75)
        assert_true(result.proposals_created == 0, "distributed one-off failures must not pass high confidence threshold")
    finally:
        conn.close()


def test_d_enforcement_signature_pattern_is_critical_context():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_enforcement_rejection(conn, i, reason="capability token invalid signature: TOK-X")
        result = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        assert_true(result.proposals_created == 1, f"expected 1 proposal, got {result.proposals_created}")
        proposal = result.proposals[0]
        assert_true("invalid_signature" in proposal.reason, "proposal should preserve signature-tamper bucket")
        assert_true("do not auto-grant capabilities" in proposal.proposed_change, "proposal must not grant capabilities")
    finally:
        conn.close()


def main():
    tests = [
        ("A HTTP policy proposal-only pattern", test_a_http_policy_pattern_proposal_only),
        ("B secret provider proposal-only pattern", test_b_secret_provider_pattern_proposal_only),
        ("C mixed failures do not overfit", test_c_mixed_patterns_do_not_overfit),
        ("D enforcement signature pattern remains advisory", test_d_enforcement_signature_pattern_is_critical_context),
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
    print("\nPATTERN INTELLIGENCE EVIDENCE REPORT")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
