"""
WHY: Proves the evidence runner's own isolation and timeout behavior before real evidence scripts run.
INV: Synthetic target is a dedicated test input only; production GateGraph code is untouched.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import evidence_ci

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"
TARGET = "tests/evidence_runner_case.py"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
            output = result.stdout.decode("utf-8", errors="replace")
            return str(pid) in output
        except Exception:
            return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, object]] = []
    failed = 0

    pass_result = evidence_ci.run_one("selftest_pass", TARGET, 3, {"RUNNER_SELFTEST_MODE": "pass"})
    pass_ok = pass_result.status == "passed" and pass_result.returncode == 0
    checks.append({"name": "pass_script", "ok": pass_ok, "status": pass_result.status})
    failed += 0 if pass_ok else 1

    fail_result = evidence_ci.run_one("selftest_fail", TARGET, 3, {"RUNNER_SELFTEST_MODE": "fail"})
    fail_ok = fail_result.status == "failed" and fail_result.returncode != 0
    checks.append({"name": "fail_script", "ok": fail_ok, "status": fail_result.status})
    failed += 0 if fail_ok else 1

    hang_result = evidence_ci.run_one("selftest_hang", TARGET, 1, {"RUNNER_SELFTEST_MODE": "hang"})
    hang_ok = hang_result.status == "timeout" and hang_result.timed_out and hang_result.killed_process_group
    checks.append({"name": "timeout_script", "ok": hang_ok, "status": hang_result.status, "killed_process_group": hang_result.killed_process_group})
    failed += 0 if hang_ok else 1

    child_result = evidence_ci.run_one("selftest_child_hang", TARGET, 1, {"RUNNER_SELFTEST_MODE": "child_hang"})
    child_pid = -1
    for line in child_result.stdout_tail.splitlines():
        if line.startswith("CHILD_PID:"):
            child_pid = int(line.split(":", 1)[1])
    deadline = time.monotonic() + 2.0
    child_dead = False
    while time.monotonic() < deadline:
        if child_pid > 0 and not _pid_alive(child_pid):
            child_dead = True
            break
        time.sleep(0.05)
    child_ok = child_result.status == "timeout" and child_result.killed_process_group and child_dead
    checks.append({
        "name": "process_group_kill",
        "ok": child_ok,
        "status": child_result.status,
        "killed_process_group": child_result.killed_process_group,
        "child_pid": child_pid,
        "child_dead": child_dead,
    })
    failed += 0 if child_ok else 1

    passed = len(checks) - failed
    print(json.dumps({"checks": checks}, indent=2), flush=True)
    print(f"Summary: {{'passed': {passed}, 'failed': {failed}}}", flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    os._exit(main())
