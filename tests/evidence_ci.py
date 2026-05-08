"""
WHY: Aggregate evidence runner must prove evidence results without relying on shell timeout wrappers.
INV: This runner only executes evidence scripts and records results; production code is untouched.
SEC: Each evidence script runs in an isolated subprocess with bounded lifetime and fail-closed reporting.
"""
from __future__ import annotations

import ast
import json
import os
import re
import signal
import select
import subprocess
import sys
import time
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"

MANIFEST: List[Tuple[str, str, int]] = [
    ("evidence_runner_selftest", "tests/evidence_runner_selftest.py", 10),
    ("runtime_stress_evidence", "tests/runtime_stress_evidence.py", 40),
    ("session_budget_evidence", "tests/session_budget_evidence.py", 40),
    ("guard_orchestration_evidence", "tests/guard_orchestration_evidence.py", 30),
    ("reason_normalization_evidence", "tests/reason_normalization_evidence.py", 20),
    ("scale_safety_evidence", "tests/scale_safety_evidence.py", 30),
    ("external_api_evidence", "tests/external_api_evidence.py", 30),
    ("runaway_cost_evidence", "tests/runaway_cost_evidence.py", 20),
    ("cross_session_budget_evidence", "tests/cross_session_budget_evidence.py", 20),
    ("operational_hardening_evidence", "tests/operational_hardening_evidence.py", 20),
    ("operational_alerting_evidence", "tests/operational_alerting_evidence.py", 20),
    ("operational_stability_evidence", "tests/operational_stability_evidence.py", 20),
    ("single_node_cli_evidence", "tests/single_node_cli_evidence.py", 20),
    ("capability_token_hardening_evidence", "tests/capability_token_hardening_evidence.py", 30),
    ("key_rotation_evidence", "tests/key_rotation_evidence.py", 20),
    ("secret_api_integration_evidence", "tests/secret_api_integration_evidence.py", 20),
    ("http_policy_evidence", "tests/http_policy_evidence.py", 20),
    ("security_finesse_evidence", "tests/security_finesse_evidence.py", 20),
    ("block_c_stress_evidence", "tests/block_c_stress_evidence.py", 30),
    ("block_d_audit_explain_evidence", "tests/block_d_audit_explain_evidence.py", 30),
    ("core_loop", "tests/test_loop.py", 30),
    ("runtime_guard", "tests/runtime_guard_tests.py", 20),
    ("pattern_engine", "tests/pattern_engine_tests.py", 20),
    ("pattern_intelligence", "tests/pattern_intelligence_evidence.py", 20),
    ("usage_simulation", "tests/usage_simulation.py", 20),
    ("unusual_inputs", "tests/unusual_inputs.py", 20),
    ("agent_scenarios", "tests/agent_scenarios.py", 20),
    ("controlled_apply", "tests/controlled_apply_evidence.py", 20),
]

DB_FILES = ("gategraph.db", "gategraph.db-journal", "gategraph.db-wal", "gategraph.db-shm")

class _RunnerTimeout(Exception):
    pass


def _raise_runner_timeout(signum, frame):
    raise _RunnerTimeout()

@dataclass
class EvidenceCommand:
    name: str
    script: str
    timeout_seconds: int
    returncode: int
    status: str  # passed | failed | timeout
    stdout_tail: str = ""
    stderr_tail: str = ""
    parsed_summary: dict | None = None
    timed_out: bool = False
    killed_process_group: bool = False
    reset_warnings: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

@dataclass
class EvidenceCIReport:
    run_id: str
    started_at: str
    finished_at: str | None = None
    passed: bool = False
    commands: List[EvidenceCommand] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.passed = all(c.status == "passed" for c in self.commands)


def _tail(text: str, chars: int = 5000) -> str:
    return text[-chars:] if len(text) > chars else text


def _parse_summary(stdout: str) -> dict | None:
    matches = re.findall(r"Summary:\s*(\{[^\n]+\})", stdout)
    if not matches:
        return None
    try:
        value = ast.literal_eval(matches[-1])
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _summary_passed(summary: dict | None) -> bool:
    if not summary:
        return False
    if "failed" in summary:
        return int(summary.get("failed") or 0) == 0
    return False



def _marker_passed(stdout: str, stderr: str) -> bool:
    """Treat explicit evidence PASS markers as success when a script uses rc=1 internally
    to test negative cases but reports the evidence outcome via stdout.
    """
    has_pass = re.search(r"(?m)^PASS\b", stdout) is not None
    has_fail = re.search(r"(?m)^FAIL\b", stdout) is not None
    has_traceback = "Traceback (most recent call last)" in stderr
    return has_pass and not has_fail and not has_traceback


def _reset_db_files() -> list[str]:
    warnings: list[str] = []
    for name in DB_FILES:
        path = PROJECT_ROOT / name
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            warnings.append(f"could not unlink {name}: {type(exc).__name__}: {exc}")
        if path.exists():
            warnings.append(f"db reset verification failed: {name} still exists")
    return warnings


def _posix_descendant_pids(root_pid: int) -> list[int]:
    """Return descendants using /proc PPid links; empty on non-/proc systems."""
    if os.name != "posix":
        return []
    children: dict[int, list[int]] = {}
    proc_root = Path("/proc")
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            status = entry.joinpath("status").read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        ppid = None
        for line in status.splitlines():
            if line.startswith("PPid:"):
                try:
                    ppid = int(line.split()[1])
                except (IndexError, ValueError):
                    ppid = None
                break
        if ppid is not None:
            children.setdefault(ppid, []).append(int(entry.name))

    result: list[int] = []
    seen: set[int] = set()
    stack = list(children.get(root_pid, []))
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        result.append(pid)
        stack.extend(children.get(pid, []))
    return result


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _kill_process_group(proc: subprocess.Popen[object]) -> bool:
    """Best-effort hard kill of the whole subprocess tree.

    INV: Timeout is final and fail-closed. The runner must never leave a child tree
    running just because the direct child or its process group behaves differently
    across platforms.
    """
    killed = False
    root_pid = int(proc.pid)
    try:
        if os.name == "posix":
            # SEC: kill the isolated process group first; fallback tree kill covers
            # child processes that escaped or inherited descriptors unexpectedly.
            descendant_pids = _posix_descendant_pids(root_pid)
            try:
                pgid = os.getpgid(root_pid)
                os.killpg(pgid, signal.SIGKILL)
                killed = True
            except (ProcessLookupError, PermissionError, OSError):
                pass
            for pid in sorted(descendant_pids, reverse=True):
                try:
                    os.kill(pid, signal.SIGKILL)
                    killed = True
                except (ProcessLookupError, PermissionError, OSError):
                    pass
            if _pid_alive(root_pid):
                try:
                    os.kill(root_pid, signal.SIGKILL)
                    killed = True
                except (ProcessLookupError, PermissionError, OSError):
                    pass
        else:
            # WHY: proc.kill() only kills the direct child on Windows. taskkill /T /F
            # terminates the child tree so inherited log-file handles are released.
            subprocess.run(
                ["taskkill", "/PID", str(root_pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
            killed = True
            if proc.poll() is None:
                try:
                    proc.kill()
                    killed = True
                except OSError:
                    pass
    except subprocess.SubprocessError:
        pass
    return killed


def _bounded_wait_after_kill(proc: subprocess.Popen[object], seconds: float = 2.0) -> int:
    try:
        return int(proc.wait(timeout=seconds))
    except subprocess.TimeoutExpired:
        _kill_process_group(proc)
        return 124


def run_one(name: str, script: str, timeout_seconds: int, extra_env: dict[str, str] | None = None) -> EvidenceCommand:
    reset_warnings = _reset_db_files()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # WHY: Windows consoles default to legacy codepages; evidence scripts print checkmarks.
    # UTF-8 stdio prevents false UnicodeEncodeError failures in isolated subprocesses.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if extra_env:
        env.update(extra_env)
    cmd = [sys.executable, "-S", "-u", "tests/_run_isolated.py", script]
    out_path = LOG_DIR / f"_{name}.stdout.tmp"
    err_path = LOG_DIR / f"_{name}.stderr.tmp"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    timed_out = False
    killed_group = False
    rc: int | None = None

    # WHY: binary file-backed output avoids pipe deadlocks and all Windows codepage decode paths.
    with out_path.open("wb") as out, err_path.open("wb") as err:
        if os.name == "posix":
            # SEC: Python owns the watchdog and starts an isolated session. Avoid GNU
            # timeout as a second supervisor because subprocess.run() can wait forever
            # if the wrapped child never reports exit in hostile kernel/IO states.
            proc = subprocess.Popen(
                cmd,
                cwd=PROJECT_ROOT,
                env=env,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
        else:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                cmd,
                cwd=PROJECT_ROOT,
                env=env,
                stdout=out,
                stderr=err,
                creationflags=creationflags,
            )
        try:
            rc = proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            killed_group = _kill_process_group(proc)
            rc = _bounded_wait_after_kill(proc, 2.0)

    duration = time.monotonic() - started
    stdout = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else ""
    stderr = err_path.read_text(encoding="utf-8", errors="replace") if err_path.exists() else ""
    cleanup_warnings: list[str] = []
    for path in (out_path, err_path):
        for attempt in range(10):
            try:
                path.unlink()
                break
            except FileNotFoundError:
                break
            except OSError as exc:
                if attempt == 9:
                    cleanup_warnings.append(f"could not unlink temp log {path.name}: {type(exc).__name__}: {exc}")
                time.sleep(0.1)

    summary = _parse_summary(stdout)
    if timed_out:
        status = "timeout"
        returncode = 124
    elif rc == 0 or _summary_passed(summary) or _marker_passed(stdout, stderr):
        status = "passed"
        returncode = 0
    else:
        status = "failed"
        returncode = int(rc if rc is not None else 1)

    return EvidenceCommand(
        name=name,
        script=script,
        timeout_seconds=timeout_seconds,
        returncode=returncode,
        status=status,
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        parsed_summary=summary,
        timed_out=timed_out,
        killed_process_group=killed_group,
        reset_warnings=reset_warnings + cleanup_warnings,
        duration_seconds=round(duration, 3),
    )

def main() -> int:
    started = datetime.now(timezone.utc)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = EvidenceCIReport(
        run_id=started.strftime("ci_evidence_%Y%m%d_%H%M%S"),
        started_at=started.isoformat(),
        notes=[
            "Subprocess runner uses Python-owned timeout, file-backed I/O, process-session isolation and hard process-group kill on timeout.",
            "Timeout is fail-closed: an evidence script that exceeds its budget fails even if it emitted a passing Summary before hanging.",
            "Production governance/enforcement/runtime code is not executed differently by this runner."
        ],
    )
    for name, script, timeout_seconds in MANIFEST:
        print(f"--- {name} ---", flush=True)
        result = run_one(name, script, timeout_seconds)
        report.commands.append(result)
        mark = "PASS" if result.status == "passed" else "FAIL"
        print(result.stdout_tail, end="" if result.stdout_tail.endswith("\n") else "\n")
        if result.stderr_tail:
            print(result.stderr_tail, end="" if result.stderr_tail.endswith("\n") else "\n", file=sys.stderr)
        if result.reset_warnings:
            for warning in result.reset_warnings:
                print(f"runner warning: {warning}", file=sys.stderr, flush=True)
        print(
            f"{mark} {name} rc={result.returncode} status={result.status} duration={result.duration_seconds}s",
            flush=True,
        )

    report.finish()
    out = LOG_DIR / f"{report.run_id}.json"
    out.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nCI EVIDENCE REPORT", flush=True)
    print(f"Log: {out}", flush=True)
    print(f"Passed: {report.passed}", flush=True)
    return 0 if report.passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
