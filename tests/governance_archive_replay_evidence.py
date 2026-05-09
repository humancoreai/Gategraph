import json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.database import get_connection, reset_db, seed_rules
from src.governance import evaluate_task
from src.governance_archive import archive_payloads, create_archive_record, read_archive_records
from src.governance_drift_compare import assert_descriptive_drift_payload, compare_governance_snapshots
from src.governance_drift_snapshot import create_governance_baseline_snapshot
from src.governance_replay import build_historical_replay

def check(name, condition, details):
    if not condition: raise AssertionError(f"{name} failed: {details}")
    print(f"✓ {name}: {details}")
def evaluate_fixture(task_id):
    reset_db(); conn = get_connection(); seed_rules(conn)
    try:
        r = evaluate_task(conn, task_id=task_id, task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
        return {"risk_level": r.risk_level, "final_decision": r.final_decision, "selected_rule_id": r.selected_rule_id, "matched_rule_ids": r.matched_rule_ids}
    finally: conn.close()
def unsupported_kind_blocked(payload):
    try: create_archive_record("policy_adjustment", payload)
    except ValueError: return True
    return False
def main():
    events_a = [{"reason_code":"OK_ACTION_READY","guard":"enforcement","queue_type":"none","workflow_type":"auto_allow"},{"reason_code":"RT_LOOP_DETECTED","guard":"runtime_guard","queue_type":"human_review","workflow_type":"manual_review"}]
    events_b = events_a + [{"reason_code":"SES_COST_LIMIT","guard":"session_budget_guard","queue_type":"human_review","workflow_type":"manual_review"}]
    snapshot_a = create_governance_baseline_snapshot(events_a, timestamp="2026-05-06T16:00:00+00:00")
    snapshot_b = create_governance_baseline_snapshot(events_b, timestamp="2026-05-06T17:00:00+00:00")
    comparison = compare_governance_snapshots(snapshot_a, snapshot_b)
    record_a = create_archive_record("governance_snapshot", snapshot_a, timestamp="2026-05-06T16:00:00+00:00")
    record_b = create_archive_record("governance_snapshot", snapshot_b, timestamp="2026-05-06T17:00:00+00:00")
    record_c = create_archive_record("drift_comparison", comparison, timestamp="2026-05-06T17:05:00+00:00")
    check("archive_record_shape_descriptive", record_a["archive_mode"] == "historical_record_archive" and assert_descriptive_drift_payload(record_a), {"kind": record_a["record_kind"], "schema": record_a["archive_schema_version"]})
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "governance_archive.jsonl"
        archive_payloads([snapshot_a, snapshot_b], record_kind="governance_snapshot", archive_path=path, timestamp="2026-05-06T18:00:00+00:00", source_ref="archive-evidence")
        archive_payloads([comparison], record_kind="drift_comparison", archive_path=path, timestamp="2026-05-06T18:05:00+00:00", source_ref="archive-evidence")
        records = read_archive_records(path)
        check("archive_append_only_sequence", len(records) == 3 and records[0]["archive_sequence"] == 1 and records[-1]["archive_sequence"] == 3, {"count": len(records), "last": records[-1]["archive_sequence"]})
        replay_one = build_historical_replay(records); replay_two = build_historical_replay(list(reversed(records)))
        check("replay_deterministic_ordering", replay_one == replay_two and [i["replay_index"] for i in replay_one["timeline"]] == [1,2,3], {"record_count": replay_one["record_count"]})
        check("replay_payload_hash_verification", all(i["payload_hash_verified"] for i in replay_one["timeline"]), "all payload hashes verified")
        check("replay_descriptive_only", replay_one["replay_mode"] == "historical_archive_reconstruction" and assert_descriptive_drift_payload(replay_one), replay_one["replay_mode"])
    check("unsupported_record_kind_blocked", unsupported_kind_blocked(snapshot_a), "unsupported archive kinds are rejected")
    before = evaluate_fixture("ARCHIVE-REPLAY-TASK"); _ = build_historical_replay([record_c, record_a, record_b]); after = evaluate_fixture("ARCHIVE-REPLAY-TASK")
    check("governance_decision_unchanged", before == after, {"before": before, "after": after})
    print("\nGOVERNANCE ARCHIVE REPLAY EVIDENCE REPORT")
    print(json.dumps({"failed":0,"passed":7}, indent=2, sort_keys=True))
    print("PASS governance_archive_replay_evidence")
if __name__ == "__main__": main()
