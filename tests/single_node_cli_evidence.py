"""
WHY: Evidence for v0.8.31 proves GateGraph can be used through a single-node CLI adapter.
INV: CLI must initialize, evaluate, and report status without bypassing Governance/Enforcement logic.
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


def main() -> int:
    work = PROJECT_ROOT / "tests" / "logs" / "single_node_cli"
    work.mkdir(parents=True, exist_ok=True)
    db = work / "single_node.db"
    config = work / "config.yaml"
    task = work / "task.json"
    token_out = work / "token.json"
    for path in (db, token_out):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    config.write_text(
        f"""
mode: single_node
db_path: {db.as_posix()}
actor_id: cli-actor
session_id: cli-session
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
                "task_id": "CLI-TASK-READ-001",
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

    init = run_cli("--config", str(config), "init", "--reset")
    init_json = json.loads(init.stdout) if init.stdout.strip() else {}
    checks.append(check(
        "cli_init_creates_single_node_db",
        init.returncode == 0 and init_json.get("ok") is True and db.exists(),
        {"returncode": init.returncode, "stdout": init_json, "stderr": init.stderr[-500:]},
    ))

    evaluate = run_cli("--config", str(config), "evaluate", "--task", str(task), "--token-out", str(token_out))
    eval_json = json.loads(evaluate.stdout) if evaluate.stdout.strip() else {}
    token_json = json.loads(token_out.read_text(encoding="utf-8")) if token_out.exists() else {}
    checks.append(check(
        "cli_evaluate_uses_governance_and_writes_token",
        evaluate.returncode == 0
        and eval_json.get("decision") == "allow"
        and eval_json.get("selected_rule_id") == "RULE-001"
        and eval_json.get("token_issued") is True
        and token_json.get("capabilities", {}).get("read_files") is True,
        {"returncode": evaluate.returncode, "decision": eval_json, "token": {"token_id": token_json.get("token_id"), "capabilities": token_json.get("capabilities")}},
    ))

    status = run_cli("--config", str(config), "status")
    status_json = json.loads(status.stdout) if status.stdout.strip() else {}
    counts = status_json.get("counts", {})
    checks.append(check(
        "cli_status_reports_persisted_counts",
        status.returncode == 0
        and counts.get("tasks", 0) >= 1
        and counts.get("events", 0) >= 1
        and counts.get("capability_tokens", 0) >= 1,
        {"returncode": status.returncode, "counts": counts},
    ))

    bad_config = work / "bad_config.yaml"
    bad_config.write_text("mode: server\n", encoding="utf-8")
    bad = run_cli("--config", str(bad_config), "status")
    checks.append(check(
        "cli_unsupported_mode_fails_closed",
        bad.returncode != 0 and "only mode='single_node'" in bad.stderr,
        {"returncode": bad.returncode, "stderr": bad.stderr[-500:]},
    ))

    failed = [name for ok, name, _ in checks if not ok]
    summary = {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed), "findings": 0}
    print("\nSINGLE NODE CLI EVIDENCE REPORT")
    print(f"Summary: {summary}")
    if failed:
        print(f"FAIL single_node_cli_evidence: {failed}")
        return 1
    print("PASS single_node_cli_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
