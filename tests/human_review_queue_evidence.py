import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import get_connection, reset_db, seed_rules
from src.governance import evaluate_task
from src.human_review_queue import (
    append_review_activity,
    append_review_item,
    assert_no_queue_prioritization_labels,
    filter_review_items_reference_only,
    human_review_queue_snapshot,
    read_review_activity,
    read_review_items,
)


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
    results = {}

    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "human_review_queue.jsonl"
        activity_log = Path(tmp) / "human_review_activity.jsonl"

        first = append_review_item(
            source_type="failure_pattern",
            source_id="PAT-LOOP-1",
            task_id="HR-TASK-1",
            incident_id="INC-1",
            pattern_id="PAT-LOOP-1",
            reason_code="RT_LOOP_DETECTED",
            guard="runtime_guard",
            playbook_ids=["PB-LOOP-001"],
            operator_comment="human reference note only",
            queue_log_path=queue_log,
            timestamp="2026-05-06T13:00:00+00:00",
        )
        second = append_review_item(
            source_type="incident",
            source_id="INC-2",
            task_id="HR-TASK-2",
            incident_id="INC-2",
            pattern_id="PAT-COST-1",
            reason_code="RT_COST_LIMIT",
            guard="runtime_cost_guard",
            playbook_ids=["PB-COST-001"],
            queue_log_path=queue_log,
            timestamp="2026-05-06T13:01:00+00:00",
        )
        items = read_review_items(queue_log)
        results["items"] = items
        check(
            "queue_append_order_only",
            [item["review_item_id"] for item in items] == [first["review_item_id"], second["review_item_id"]]
            and all(item["order_semantics"] == "append_order_only" for item in items),
            items,
        )
        check(
            "queue_items_documentation_only",
            all(item["queue_mode"] == "human_review_reference_only" and item["effect"] == "documentation_only" for item in items),
            items,
        )

        filtered = filter_review_items_reference_only(items=items, playbook_id="PB-LOOP-001")
        results["filtered"] = filtered
        check(
            "queue_filter_reference_only",
            [item["review_item_id"] for item in filtered["items"]] == [first["review_item_id"]]
            and filtered["filter_mode"] == "reference_match_only",
            filtered,
        )

        activity = append_review_activity(
            review_item_id=first["review_item_id"],
            observed_steps=["inspect_trace", "open_playbook_reference"],
            linked_playbook_ids=["PB-LOOP-001"],
            human_note="documentation only",
            activity_log_path=activity_log,
            timestamp="2026-05-06T13:05:00+00:00",
        )
        activities = read_review_activity(activity_log)
        results["activity"] = activity
        check(
            "review_activity_no_outcome",
            len(activities) == 1 and activity["activity_mode"] == "documentation_only" and "outcome" not in activity,
            activity,
        )

        snapshot = human_review_queue_snapshot(
            queue_log_path=queue_log,
            activity_log_path=activity_log,
            task_id="HR-TASK-1",
            timestamp="2026-05-06T13:10:00+00:00",
        )
        results["snapshot"] = snapshot
        check(
            "snapshot_reference_view_only",
            len(snapshot["review_items"]) == 1
            and len(snapshot["review_activity"]) == 1
            and snapshot["snapshot_mode"] == "human_review_reference_view_only",
            snapshot,
        )

    decision_before = evaluate_fixture("HR-TASK-BEFORE")
    with tempfile.TemporaryDirectory() as tmp:
        append_review_item(
            source_type="failure_pattern",
            source_id="PAT-UNCHANGED",
            task_id="HR-TASK-BEFORE",
            queue_log_path=Path(tmp) / "queue.jsonl",
            timestamp="2026-05-06T13:20:00+00:00",
        )
    decision_after = evaluate_fixture("HR-TASK-BEFORE")
    check("governance_decision_unchanged", decision_before == decision_after, {"before": decision_before, "after": decision_after})

    check("no_prioritization_labels", assert_no_queue_prioritization_labels(results), results)
    check("prioritization_checker_blocks", not assert_no_queue_prioritization_labels({"priority": "high"}), {"priority": "high"})
    check("decision_checker_blocks", not assert_no_queue_prioritization_labels({"decision": "approve"}), {"decision": "approve"})

    report = {
        "schema_version": "0.8.43",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"passed": 9, "failed": 0},
        "results": results,
    }
    print("\nHUMAN REVIEW QUEUE EVIDENCE REPORT")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("PASS human_review_queue_evidence")


if __name__ == "__main__":
    main()
