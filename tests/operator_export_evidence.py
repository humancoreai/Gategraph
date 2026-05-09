import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import get_connection, reset_db, seed_rules
from src.governance import evaluate_task
from src.operator_export_bundle import build_operator_export_manifest, collect_export_sources, create_operator_export_bundle, verify_operator_export_manifest
from src.governance_drift_compare import assert_descriptive_drift_payload

FORBIDDEN_KEYS = {"severity", "risk_level", "requires_attention", "recommended_action", "priority", "score", "root_cause", "alarm", "alert"}

def check(name, condition, details):
    if not condition:
        raise AssertionError(f"{name} failed: {details}")
    print(f"✓ {name}: {details}")

def walk_forbidden(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                return False
            if not walk_forbidden(nested):
                return False
    elif isinstance(value, list):
        for item in value:
            if not walk_forbidden(item):
                return False
    return True

def evaluate_fixture(task_id):
    reset_db(); conn = get_connection(); seed_rules(conn)
    try:
        result = evaluate_task(conn, task_id=task_id, task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
        return {"risk_level": result.risk_level, "final_decision": result.final_decision, "selected_rule_id": result.selected_rule_id, "matched_rule_ids": result.matched_rule_ids}
    finally:
        conn.close()

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "project"
        logs = root / "tests" / "logs"
        op = root / "operator_logs"
        logs.mkdir(parents=True); op.mkdir(parents=True)
        (logs / "ci_evidence_sample.json").write_text(json.dumps({"passed": True, "commands": [{"name": "sample"}]}), encoding="utf-8")
        (op / "governance_archive.jsonl").write_text(json.dumps({"record_kind": "governance_snapshot", "payload_hash": "abc"}) + "\n", encoding="utf-8")
        observations_a = collect_export_sources([logs, op], root=root)
        observations_b = collect_export_sources([op, logs], root=root)
        check("source_observations_deterministic", observations_a == observations_b and len(observations_a) == 2, observations_a)
        manifest_a = build_operator_export_manifest(observations_a, export_id="export-evidence-fixture", timestamp="2026-05-06T21:00:00+00:00")
        manifest_b = build_operator_export_manifest(list(reversed(observations_a)), export_id="export-evidence-fixture", timestamp="2026-05-06T21:00:00+00:00")
        check("manifest_deterministic", manifest_a == manifest_b, {"manifest_hash": manifest_a["manifest_hash"]})
        verification = verify_operator_export_manifest(manifest_a)
        check("manifest_hash_observed", verification["manifest_hash_observed"] is True, verification)
        bundle = create_operator_export_bundle(export_root=root / "operator_exports", sources=[logs, op], root=root, export_id="export-evidence-fixture", timestamp="2026-05-06T21:00:00+00:00")
        manifest_path = Path(bundle["manifest_path"])
        check("bundle_manifest_written", manifest_path.exists(), {"manifest_path": str(manifest_path)})
        copied_paths = sorted(p.relative_to(Path(bundle["bundle_path"]) / "sources").as_posix() for p in (Path(bundle["bundle_path"]) / "sources").rglob("*") if p.is_file())
        check("bundle_sources_copied", copied_paths == ["operator_logs/governance_archive.jsonl", "tests/logs/ci_evidence_sample.json"], copied_paths)
        check("export_payload_descriptive", assert_descriptive_drift_payload(bundle["manifest"]) and walk_forbidden(bundle), {"source_count": bundle["manifest"]["source_count"]})
        before = evaluate_fixture("OPERATOR-EXPORT-TASK")
        _ = create_operator_export_bundle(export_root=root / "operator_exports_2", sources=[logs, op], root=root, export_id="export-evidence-fixture-2", timestamp="2026-05-06T21:10:00+00:00")
        after = evaluate_fixture("OPERATOR-EXPORT-TASK")
        check("governance_decision_unchanged", before == after, {"before": before, "after": after})
    print("\nOPERATOR EXPORT EVIDENCE REPORT")
    print(json.dumps({"failed": 0, "passed": 7}, indent=2, sort_keys=True))
    print("PASS operator_export_evidence")

if __name__ == "__main__":
    main()
