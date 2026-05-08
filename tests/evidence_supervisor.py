"""
WHY: Aggregate evidence needs a reliable supervisor even when individual scripts hang during interpreter shutdown.
INV: This runner only supervises tests; it never changes governance/enforcement/runtime semantics.
SEC: Each evidence group runs in a fresh child process with a bounded timeout and clean DB slate.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import traceback
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = PROJECT_ROOT / "tests"
LOG_DIR = TESTS_DIR / "logs"

MANIFEST: List[Tuple[str, str, str, int]] = [
    ("runtime_stress_evidence", "runtime_stress_evidence", "main", 30),
    ("session_budget_evidence", "session_budget_evidence", "main", 30),
    ("guard_orchestration_evidence", "guard_orchestration_evidence", "main", 30),
    ("reason_normalization_evidence", "reason_normalization_evidence", "main", 20),
    ("scale_safety_evidence", "scale_safety_evidence", "main", 30),
    ("external_api_evidence", "external_api_evidence", "main", 30),
    ("runaway_cost_evidence", "runaway_cost_evidence", "main", 20),
    ("capability_token_hardening_evidence", "capability_token_hardening_evidence", "main", 30),
    ("key_rotation_evidence", "key_rotation_evidence", "main", 20),
    ("secret_api_integration_evidence", "secret_api_integration_evidence", "main", 20),
    ("http_policy_evidence", "http_policy_evidence", "main", 20),
    ("security_finesse_evidence", "security_finesse_evidence", "main", 20),
    ("block_c_stress_evidence", "block_c_stress_evidence", "main", 30),
    ("block_d_audit_explain_evidence", "block_d_audit_explain_evidence", "main", 30),
    ("core_loop", "test_loop", "main", 30),
    ("runtime_guard", "runtime_guard_tests", "main", 20),
    ("pattern_engine", "pattern_engine_tests", "main", 20),
    ("usage_simulation", "usage_simulation", "run", 20),
    ("unusual_inputs", "unusual_inputs", "run", 20),
    ("agent_scenarios", "agent_scenarios", "run", 20),
]

@dataclass
class EvidenceCommand:
    name: str
    module: str
    entrypoint: str
    timeout_seconds: int
    returncode: int | None = None
    status: str = "not_run"  # passed | failed | timeout | passed_forced_exit
    child_exited: bool = False
    note: str = ""

@dataclass
class EvidenceSupervisorReport:
    run_id: str
    started_at: str
    finished_at: str | None = None
    passed: bool = False
    commands: List[EvidenceCommand] = field(default_factory=list)
    produced_logs: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.passed = all(cmd.status in {"passed", "passed_forced_exit"} and cmd.returncode == 0 for cmd in self.commands)


def _reset_db_files() -> None:
    for name in ("gategraph.db", "gategraph.db-journal", "gategraph.db-wal", "gategraph.db-shm"):
        try:
            (PROJECT_ROOT / name).unlink()
        except FileNotFoundError:
            pass


def _latest_logs_since(start_marker: float) -> List[str]:
    if not LOG_DIR.exists():
        return []
    out: List[str] = []
    for path in LOG_DIR.glob("*.json"):
        try:
            if path.stat().st_mtime >= start_marker:
                out.append(str(path.relative_to(PROJECT_ROOT)))
        except FileNotFoundError:
            continue
    return sorted(out)


def _child_entry(module_name: str, entrypoint: str, queue: mp.Queue) -> None:
    os.chdir(PROJECT_ROOT)
    for import_path in (str(PROJECT_ROOT), str(TESTS_DIR)):
        if import_path not in sys.path:
            sys.path.insert(0, import_path)
    try:
        module = __import__(module_name)
        fn: Callable[[], Any] = getattr(module, entrypoint)
        result = fn()
        rc = result if isinstance(result, int) else 0
        queue.put({"returncode": int(rc), "error": ""})
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        queue.put({"returncode": int(code), "error": ""})
    except BaseException:
        queue.put({"returncode": 1, "error": traceback.format_exc(limit=8)})


def _run_one(name: str, module: str, entrypoint: str, timeout_seconds: int) -> EvidenceCommand:
    _reset_db_files()
    cmd = EvidenceCommand(name=name, module=module, entrypoint=entrypoint, timeout_seconds=timeout_seconds)
    ctx = mp.get_context("spawn")
    queue = ctx.Queue(maxsize=1)
    proc = ctx.Process(target=_child_entry, args=(module, entrypoint, queue), name=f"evidence:{name}")
    proc.start()

    payload = None
    deadline = time.monotonic() + timeout_seconds
    # WHY: Some children report success but hang during interpreter/queue shutdown; consume the result first.
    while time.monotonic() < deadline:
        try:
            payload = queue.get(timeout=0.2)
            break
        except Exception:
            if not proc.is_alive():
                break

    if payload is not None:
        cmd.returncode = int(payload.get("returncode", 1))
        cmd.note = payload.get("error", "") or ""
        proc.join(1)
        if proc.is_alive():
            cmd.status = "passed_forced_exit" if cmd.returncode == 0 else "failed"
            cmd.note = cmd.note or "Evidence entrypoint returned; child required supervisor termination after result."
            proc.terminate()
            proc.join(3)
            if proc.is_alive():
                proc.kill()
                proc.join(3)
        else:
            cmd.child_exited = True
            cmd.status = "passed" if cmd.returncode == 0 else "failed"
    else:
        if proc.is_alive():
            cmd.status = "timeout"
            cmd.returncode = 124
            cmd.note = "Evidence child exceeded timeout before reporting success."
            proc.terminate()
            proc.join(3)
            if proc.is_alive():
                proc.kill()
                proc.join(3)
        else:
            cmd.child_exited = True
            cmd.returncode = proc.exitcode if proc.exitcode is not None else 1
            cmd.status = "passed" if cmd.returncode == 0 else "failed"
            cmd.note = "Child exited without structured result."

    return cmd


def main() -> int:
    started = datetime.now(timezone.utc)
    start_marker = datetime.now().timestamp()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = EvidenceSupervisorReport(
        run_id=started.strftime("evidence_supervisor_%Y%m%d_%H%M%S"),
        started_at=started.isoformat(),
        notes=["Supervisor runner: one child process per evidence group; timeout-bounded; no production code touched."],
    )

    for name, module, entrypoint, timeout_seconds in MANIFEST:
        print(f"--- {name} ---", flush=True)
        result = _run_one(name, module, entrypoint, timeout_seconds)
        report.commands.append(result)
        mark = "✓" if result.status in {"passed", "passed_forced_exit"} and result.returncode == 0 else "✗"
        suffix = " (forced child exit after success)" if result.status == "passed_forced_exit" else ""
        print(f"{mark} {name} rc={result.returncode} status={result.status}{suffix}", flush=True)
        if result.note and result.status not in {"passed", "passed_forced_exit"}:
            print(result.note, flush=True)

    report.produced_logs = _latest_logs_since(start_marker)
    report.finish()
    out = LOG_DIR / f"{report.run_id}.json"
    out.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nEVIDENCE SUPERVISOR REPORT", flush=True)
    print(f"Log: {out}", flush=True)
    print(f"Passed: {report.passed}", flush=True)
    print(f"Produced logs: {len(report.produced_logs)}", flush=True)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
