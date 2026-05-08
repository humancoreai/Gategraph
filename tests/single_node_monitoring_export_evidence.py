"""
WHY: Evidence for v0.8.32 proves Single Node can export operational monitoring state.
INV: Monitoring export is read-only for core governance state and writes only the requested JSON file.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=20,
    )


def check(name: str, condition: bool, detail: dict) -> tuple[bool, str, dict]:
    status = "✓" if condition else "✗"
    print(f"{status} {name}: {detail}")
    return condition, name, detail


def _status_counts(config: Path) -> dict:
    status = run_cli("--config", str(config), "status")
    payload = json.loads(status.stdout) if status.stdout.strip() else {}
    return payload.get("counts", {})


def main() -> int:
    work = PROJECT_ROOT / "tests" / "logs" / "single_node_monitoring"
    work.mkdir(parents=True, exist_ok=True)
    db = work / "single_node.db"
    config = work / "config.yaml"
    task = work / "task.json"
    export_path = work / "monitoring.json"
    for path in (db, export_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    config.write_text(
        f"""
mode: single_node
db_path: {db.as_posix()}
actor_id: cli-monitor
session_id: cli-monitor-session
system_budget_units: 50
actor_budget_units: 20
session_budget:
  max_session_cost_units: 10
  max_session_tasks: 5
  max_agent_cost_units: 10
runtime_budget:
  max_steps: 5
  max_runtime_seconds: 60
  max_cost_units: 10
  repeated_action_limit: 2
flood_guard:
  window_seconds: 60
  max_tasks_per_window: 5
  max_cost_units_per_window: 10
""".strip(),
        encoding="utf-8",
    )
    task.write_text(
        json.dumps(
            {
                "task_id": "CLI-MONITOR-READ-001",
                "task_type": "single_node_task",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
                "secrets_involved": False,
                "projected_cost_units": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    checks: list[tuple[bool, str, dict]] = []

    run_cli("--config", str(config), "init", "--reset")
    run_cli("--config", str(config), "evaluate", "--task", str(task))
    before = _status_counts(config)

    export = run_cli("--config", str(config), "export-monitoring", "--out", str(export_path))
    payload = json.loads(export_path.read_text(encoding="utf-8")) if export_path.exists() else {}
    stdout_payload = json.loads(export.stdout) if export.stdout.strip() else {}
    after = _status_counts(config)

    checks.append(check(
        "cli_export_monitoring_writes_json",
        export.returncode == 0 and export_path.exists() and stdout_payload.get("ok") is True,
        {"returncode": export.returncode, "stdout": stdout_payload, "stderr": export.stderr[-500:]},
    ))

    checks.append(check(
        "monitoring_export_has_expected_blocks",
        all(key in payload for key in ("schema_version", "generated_at", "budget_snapshot", "incidents", "alerts", "aggregated_alerts", "summary")),
        {"keys": sorted(payload.keys())},
    ))

    summary = payload.get("summary", {})
    checks.append(check(
        "monitoring_export_summary_is_consistent",
        summary.get("incident_count") == len(payload.get("incidents", []))
        and summary.get("alert_count") == len(payload.get("alerts", []))
        and summary.get("aggregated_alert_count") == len(payload.get("aggregated_alerts", [])),
        {"summary": summary},
    ))

    checks.append(check(
        "monitoring_export_does_not_mutate_core_counts",
        before == after,
        {"before": before, "after": after},
    ))

    failed = [name for ok, name, _ in checks if not ok]
    summary_report = {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed), "findings": 0}
    print("\nSINGLE NODE MONITORING EXPORT EVIDENCE REPORT")
    print(f"Summary: {summary_report}")
    if failed:
        print(f"FAIL single_node_monitoring_export_evidence: {failed}")
        return 1
    print("PASS single_node_monitoring_export_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
