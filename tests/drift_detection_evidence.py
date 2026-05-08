import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.governance_drift_compare import assert_descriptive_drift_payload, compare_governance_snapshots
from src.governance_drift_log import append_drift_events, read_drift_events
from src.governance_drift_snapshot import create_governance_baseline_snapshot
from src.queue_drift_analysis import queue_drift_correlation
from src.workflow_drift_snapshot import create_workflow_drift_snapshot
from src.database import get_connection, reset_db, seed_rules
from src.governance import evaluate_task


def check(name, condition, details):
    if not condition:
        raise AssertionError(f"{name} failed: {details}")
    print(f"✓ {name}: {details}")


def evaluate_fixture(task_id):
    reset_db()
    conn = get_connection()
    seed_rules(conn)
    try:
        result = evaluate_task(
            conn,
            task_id=task_id,
            task_type="file_operation",
            requested_capabilities=["read_files"],
            input_source="local",
        )
        return {
            "risk_level": result.risk_level,
            "final_decision": result.final_decision,
            "selected_rule_id": result.selected_rule_id,
            "matched_rule_ids": result.matched_rule_ids,
        }
    finally:
        conn.close()


def main():
    events_a = [
        {"reason_code": "OK_ACTION_READY", "guard": "enforcement", "queue_type": "none", "workflow_type": "auto_allow"},
        {"reason_code": "RT_LOOP_DETECTED", "guard": "runtime_guard", "queue_type": "human_review", "workflow_type": "manual_review"},
        {"reason_code": "RT_LOOP_DETECTED", "guard": "runtime_guard", "queue_type": "human_review", "workflow_type": "manual_review"},
    ]
    events_b = [
        {"reason_code": "OK_ACTION_READY", "guard": "enforcement", "queue_type": "none", "workflow_type": "auto_allow"},
        {"reason_code": "SES_COST_LIMIT", "guard": "session_budget_guard", "queue_type": "human_review", "workflow_type": "manual_review"},
        {"reason_code": "SES_COST_LIMIT", "guard": "session_budget_guard", "queue_type": "human_review", "workflow_type": "manual_review"},
        {"reason_code": "RT_LOOP_DETECTED", "guard": "runtime_guard", "queue_type": "human_review", "workflow_type": "manual_review"},
    ]

    snapshot_a = create_governance_baseline_snapshot(events_a, timestamp="2026-05-06T14:00:00+00:00")
    snapshot_a_repeat = create_governance_baseline_snapshot(events_a, timestamp="2026-05-06T14:00:00+00:00")
    snapshot_b = create_governance_baseline_snapshot(events_b, timestamp="2026-05-06T15:00:00+00:00")

    check("snapshot_deterministic", snapshot_a == snapshot_a_repeat, snapshot_a)
    check(
        "snapshot_descriptive_fields",
        snapshot_a["snapshot_mode"] == "descriptive_distribution_snapshot"
        and snapshot_a["reason_distribution"]["RT_LOOP_DETECTED"]["count"] == 2,
        snapshot_a,
    )

    comparison = compare_governance_snapshots(snapshot_a, snapshot_b)
    check(
        "comparison_descriptive_only",
        comparison["comparison_mode"] == "descriptive_snapshot_comparison"
        and assert_descriptive_drift_payload(comparison),
        comparison,
    )
    check(
        "comparison_tracks_presence_and_delta",
        any(
            item["dimension"] == "reason_distribution"
            and item["key"] == "SES_COST_LIMIT"
            and item["presence"] == "snapshot_b_only"
            and item["delta"] > 0
            for item in comparison["distribution_changes"]
        ),
        comparison["distribution_changes"],
    )

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "governance_drift_events.jsonl"
        written = append_drift_events(comparison, drift_log_path=log_path, timestamp="2026-05-06T15:05:00+00:00")
        read_back = read_drift_events(log_path)
        check(
            "drift_event_log_append_only_shape",
            len(written) == len(comparison["distribution_changes"])
            and read_back == written
            and all(event["event_mode"] == "descriptive_change_record" for event in read_back),
            read_back[:2],
        )
        second_write = append_drift_events(comparison, drift_log_path=log_path, timestamp="2026-05-06T15:06:00+00:00")
        read_second = read_drift_events(log_path)
        check(
            "drift_event_log_appends_without_rewrite",
            len(read_second) == len(written) + len(second_write)
            and read_second[0]["event_id"] == "drift-event-000000000001",
            {"count": len(read_second), "first": read_second[0]["event_id"], "last": read_second[-1]["event_id"]},
        )

    correlation = queue_drift_correlation(events_b)
    check(
        "queue_correlation_descriptive",
        correlation["correlation_mode"] == "descriptive_cooccurrence_only"
        and correlation["queue_reason_cooccurrence"]["human_review"]["SES_COST_LIMIT"] == 2,
        correlation,
    )

    workflow_snapshot = create_workflow_drift_snapshot(events_b, timestamp="2026-05-06T15:10:00+00:00")
    check(
        "workflow_snapshot_descriptive",
        workflow_snapshot["snapshot_mode"] == "workflow_distribution_snapshot"
        and "workflow_distribution" in workflow_snapshot,
        workflow_snapshot,
    )

    forbidden_payloads = [
        {"severity": "critical"},
        {"risk_level": "high"},
        {"requires_attention": True},
        {"recommended_action": "change_policy"},
        {"root_cause": "guard"},
    ]
    check(
        "forbidden_drift_schema_terms_blocked",
        all(not assert_descriptive_drift_payload(payload) for payload in forbidden_payloads),
        forbidden_payloads,
    )

    decision_before = evaluate_fixture("DRIFT-TASK-BEFORE")
    _ = create_governance_baseline_snapshot(events_b, timestamp="2026-05-06T15:15:00+00:00")
    _ = compare_governance_snapshots(snapshot_a, snapshot_b)
    decision_after = evaluate_fixture("DRIFT-TASK-BEFORE")
    check("governance_decision_unchanged", decision_before == decision_after, {"before": decision_before, "after": decision_after})

    report = {
        "schema_version": "0.8.44",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"passed": 10, "failed": 0},
    }
    print("\nDRIFT DETECTION EVIDENCE REPORT")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("PASS drift_detection_evidence")


if __name__ == "__main__":
    main()
