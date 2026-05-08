import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import get_connection, reset_db, seed_rules
from src.governance import evaluate_task
from src.operator_workflow import (
    append_workflow_event,
    assert_no_workflow_interpretation_labels,
    link_incident_playbooks,
    load_playbooks,
    match_playbooks,
    read_workflow_events,
    workflow_snapshot,
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

    playbooks = load_playbooks()
    results["playbooks"] = playbooks
    ids = [item["playbook_id"] for item in playbooks]
    check("playbooks_loaded", "PB-LOOP-001" in ids and "PB-COST-001" in ids, ids)

    loop_match = match_playbooks(reason_code="RT_LOOP_DETECTED", guard="runtime_guard", playbooks=playbooks)
    results["loop_match"] = loop_match
    check(
        "matching_descriptive_multiple_basis",
        loop_match["matches"] == [{"playbook_id": "PB-LOOP-001", "matched_on": ["reason_code", "guard"]}]
        and loop_match["match_mode"] == "descriptive_mapping_only",
        loop_match,
    )

    broad_match = match_playbooks(guard="runtime_cost_guard", playbooks=playbooks)
    results["broad_match"] = broad_match
    check(
        "matching_no_selection_output",
        broad_match["matches"] == [{"playbook_id": "PB-COST-001", "matched_on": ["guard"]}],
        broad_match,
    )

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "workflow_events.jsonl"
        before = read_workflow_events(log_path)
        event = append_workflow_event(
            playbook_id="PB-LOOP-001",
            task_id="WF-TASK-1",
            filter_ref={"reason_code": "RT_LOOP_DETECTED"},
            steps_observed=["inspect_trace", "check_runtime_limits"],
            operator_comment="human note only",
            log_path=log_path,
            timestamp="2026-05-06T12:00:00+00:00",
        )
        after = read_workflow_events(log_path)
        results["workflow_event"] = event
        check("workflow_log_append_only_documentation", len(before) == 0 and len(after) == 1, after)
        check("workflow_event_no_system_effect", event["effect"] == "documentation_only", event)

        link = link_incident_playbooks(
            incident_id="INC-1",
            pattern_id="PAT-LOOP-1",
            reason_code="RT_LOOP_DETECTED",
            guard="runtime_guard",
            playbooks=playbooks,
        )
        results["incident_link"] = link
        check(
            "incident_link_reference_only",
            link["linked_playbooks"] == ["PB-LOOP-001"] and link["link_mode"] == "reference_only",
            link,
        )

        snapshot = workflow_snapshot(
            pattern_id="PAT-LOOP-1",
            reason_code="RT_LOOP_DETECTED",
            guard="runtime_guard",
            task_id="WF-TASK-1",
            log_path=log_path,
            playbooks=playbooks,
            timestamp="2026-05-06T12:05:00+00:00",
        )
        results["snapshot"] = snapshot
        check(
            "workflow_snapshot_reference_view",
            snapshot["playbook_ids"] == ["PB-LOOP-001"]
            and len(snapshot["workflow_events"]) == 1
            and snapshot["snapshot_mode"] == "reproducible_reference_view_only",
            snapshot,
        )

    decision_before = evaluate_fixture("WF-TASK-BEFORE")
    append_workflow_event(
        playbook_id="PB-LOOP-001",
        task_id="WF-TASK-1",
        steps_observed=["inspect_trace"],
        log_path=Path(tempfile.gettempdir()) / "gategraph_operator_workflow_evidence.jsonl",
        timestamp="2026-05-06T12:10:00+00:00",
    )
    decision_after = evaluate_fixture("WF-TASK-BEFORE")
    check("governance_decision_unchanged", decision_before == decision_after, {"before": decision_before, "after": decision_after})

    check("no_interpretation_labels", assert_no_workflow_interpretation_labels(results), results)
    check("interpretation_checker_blocks", not assert_no_workflow_interpretation_labels({"priority": "high"}), {"priority": "high"})

    report = {
        "schema_version": "0.8.42",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"passed": 10, "failed": 0},
        "results": results,
    }
    print("\nOPERATOR WORKFLOW EVIDENCE REPORT")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("PASS operator_workflow_evidence")


if __name__ == "__main__":
    main()
