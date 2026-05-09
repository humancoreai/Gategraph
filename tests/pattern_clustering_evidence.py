"""
WHY: Evidence that clustering improves proposal review without granting decision authority.
INV: clustering never mutates rules, policies, budgets, secrets, tokens, or proposals.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import reset_db, get_connection, seed_rules, ensure_pattern_schema
from src import event_logger, pattern_engine
from src.pattern_clustering import cluster_pattern_proposals


def fresh_db():
    reset_db()
    conn = get_connection()
    ensure_pattern_schema(conn)
    with conn:
        seed_rules(conn)
    return conn


def add_enforcement_rejection(conn, idx, *, reason="capability token invalid signature: TOK-X", capability="api_call"):
    task_id = f"PCL-TASK-{idx}"
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
        event_id=f"PCL-EVT-{idx}",
        idempotency_key=f"pcl:{idx}",
        correlation_id=f"PCL-COR-{idx}",
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


def test_a_clusters_duplicate_proposals_without_mutation():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_enforcement_rejection(conn, i, reason="capability token invalid signature: TOK-X")
        result1 = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        result2 = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75)
        before_rules = pattern_engine.active_rule_count(conn)
        clusters = cluster_pattern_proposals(result1.proposals + result2.proposals)
        after_rules = pattern_engine.active_rule_count(conn)
        assert_true(len(clusters) == 1, f"expected one cluster, got {len(clusters)}")
        assert_true(clusters[0]["proposal_count"] == 2, "cluster should deduplicate two matching proposals")
        assert_true(before_rules == after_rules, "clustering must not mutate rules")
    finally:
        conn.close()


def test_b_priority_sorting_preserves_p0_first():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_enforcement_rejection(conn, i, reason="capability token invalid signature: TOK-X")
        critical = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75).proposals[0]
        lower = {
            "proposal_id": "LOW-1",
            "proposal_type": critical.proposal_type,
            "target_rule_id": None,
            "reason": "Repeated guard pattern detected: stage='http_policy', capability='api_call', bucket='http_endpoint_blocked'.",
            "proposed_change": "review only",
            "supporting_events": ["E1", "E2", "E3"],
            "confidence": 0.75,
            "priority": "P2",
            "score": 60.0,
        }
        clusters = cluster_pattern_proposals([lower, critical])
        assert_true(clusters[0]["priority"] == "P0", f"expected P0 first, got {clusters[0]['priority']}")
    finally:
        conn.close()


def test_c_cluster_output_is_plain_review_data():
    conn = fresh_db()
    try:
        for i in range(1, 4):
            add_enforcement_rejection(conn, i, reason="token PI is bound to task A, not B")
        proposal = pattern_engine.analyze_audit_patterns(conn, min_events=3, confidence_threshold=0.75).proposals[0]
        cluster = cluster_pattern_proposals([proposal])[0]
        assert_true(cluster["cluster_id"].startswith("PCL-"), "cluster should have stable prefix")
        assert_true("representative_examples" in cluster, "cluster should carry examples for review")
        assert_true(cluster["proposal_ids"] == [proposal.proposal_id], "cluster should preserve proposal ids")
    finally:
        conn.close()


def test_d_empty_input_returns_empty_clusters():
    clusters = cluster_pattern_proposals([])
    assert_true(clusters == [], "empty proposal list should produce no clusters")


def main():
    tests = [
        ("A duplicate proposals cluster without mutation", test_a_clusters_duplicate_proposals_without_mutation),
        ("B priority sorting preserves P0 first", test_b_priority_sorting_preserves_p0_first),
        ("C cluster output is plain review data", test_c_cluster_output_is_plain_review_data),
        ("D empty input returns empty clusters", test_d_empty_input_returns_empty_clusters),
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
    print("\nPATTERN CLUSTERING EVIDENCE REPORT")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
