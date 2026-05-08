import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.archive_integrity import build_archive_integrity_report, verify_archive_record, verify_archive_sequence, verify_replay_consistency
from src.database import get_connection, reset_db, seed_rules
from src.governance import evaluate_task
from src.governance_archive import archive_payloads, read_archive_records
from src.governance_drift_compare import assert_descriptive_drift_payload, compare_governance_snapshots
from src.governance_drift_snapshot import create_governance_baseline_snapshot


def check(name, condition, details):
    if not condition:
        raise AssertionError(f"{name} failed: {details}")
    print(f"✓ {name}: {details}")


def evaluate_fixture(task_id):
    reset_db(); conn = get_connection(); seed_rules(conn)
    try:
        result = evaluate_task(conn, task_id=task_id, task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
        return {"risk_level": result.risk_level, "final_decision": result.final_decision, "selected_rule_id": result.selected_rule_id, "matched_rule_ids": result.matched_rule_ids}
    finally:
        conn.close()


def main():
    events_a = [
        {"reason_code":"OK_ACTION_READY","guard":"enforcement","queue_type":"none","workflow_type":"auto_allow"},
        {"reason_code":"RT_LOOP_DETECTED","guard":"runtime_guard","queue_type":"human_review","workflow_type":"manual_review"},
    ]
    events_b = events_a + [
        {"reason_code":"SES_COST_LIMIT","guard":"session_budget_guard","queue_type":"human_review","workflow_type":"manual_review"},
    ]
    snapshot_a = create_governance_baseline_snapshot(events_a, timestamp="2026-05-06T19:00:00+00:00")
    snapshot_b = create_governance_baseline_snapshot(events_b, timestamp="2026-05-06T20:00:00+00:00")
    comparison = compare_governance_snapshots(snapshot_a, snapshot_b)

    with tempfile.TemporaryDirectory() as tmp:
        archive_path = Path(tmp) / "governance_archive.jsonl"
        archive_payloads([snapshot_a], record_kind="governance_snapshot", archive_path=archive_path, timestamp="2026-05-06T19:00:00+00:00")
        archive_payloads([snapshot_b], record_kind="governance_snapshot", archive_path=archive_path, timestamp="2026-05-06T20:00:00+00:00")
        archive_payloads([comparison], record_kind="drift_comparison", archive_path=archive_path, timestamp="2026-05-06T20:05:00+00:00")
        records = read_archive_records(archive_path)

        sequence = verify_archive_sequence(records)
        check("archive_sequence_contiguous", sequence["archive_sequence_observed"] is True and sequence["archive_sequences"] == [1,2,3], sequence)

        record_checks = [verify_archive_record(r) for r in records]
        check("record_payload_hashes_observed", all(r["payload_hash_observed"] for r in record_checks), record_checks)
        check("record_ids_observed", all(r["record_id_observed"] for r in record_checks), record_checks)

        replay = verify_replay_consistency(records)
        check("replay_consistency_observed", replay["replay_order_observed"] is True and replay["payload_hashes_observed"] is True, replay)

        report_one = build_archive_integrity_report(records)
        report_two = build_archive_integrity_report(list(reversed(records)))
        check("integrity_report_deterministic", report_one == report_two and assert_descriptive_drift_payload(report_one), {"report_id": report_one["archive_integrity_report_id"]})

        tampered = dict(records[0]); tampered["payload"] = dict(tampered["payload"]); tampered["payload"]["snapshot_id"] = "changed-for-observation"
        tampered_check = verify_archive_record(tampered)
        check("payload_hash_change_observed", tampered_check["payload_hash_observed"] is False, tampered_check)

        before = evaluate_fixture("ARCHIVE-INTEGRITY-TASK")
        _ = build_archive_integrity_report(records)
        after = evaluate_fixture("ARCHIVE-INTEGRITY-TASK")
        check("governance_decision_unchanged", before == after, {"before": before, "after": after})

    print("\nARCHIVE INTEGRITY REPLAY CONSISTENCY EVIDENCE REPORT")
    print(json.dumps({"failed": 0, "passed": 7}, indent=2, sort_keys=True))
    print("PASS archive_integrity_replay_consistency_evidence")


if __name__ == "__main__":
    main()
