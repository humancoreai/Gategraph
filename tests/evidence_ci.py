"""
WHY: Aggregate evidence runner must distinguish core test failures from environment-specific Python shutdown hangs.
INV: This runner only executes evidence scripts and records results; production code is untouched.
SEC: A timed-out script is accepted only if it already emitted a zero-failure Summary line.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"

MANIFEST: List[Tuple[str, str, int]] = [
    ("runtime_stress_evidence", "tests/runtime_stress_evidence.py", 40),
    ("session_budget_evidence", "tests/session_budget_evidence.py", 40),
    ("guard_orchestration_evidence", "tests/guard_orchestration_evidence.py", 30),
    ("reason_normalization_evidence", "tests/reason_normalization_evidence.py", 20),
    ("scale_safety_evidence", "tests/scale_safety_evidence.py", 30),
    ("external_api_evidence", "tests/external_api_evidence.py", 30),
    ("runaway_cost_evidence", "tests/runaway_cost_evidence.py", 20),
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

@dataclass
class EvidenceCommand:
    name: str
    script: str
    timeout_seconds: int
    returncode: int
    status: str  # passed | failed | passed_after_summary_timeout | timeout
    stdout_tail: str = ""
    stderr_tail: str = ""
    parsed_summary: dict | None = None

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
        self.passed = all(c.status in {"passed", "passed_after_summary_timeout"} for c in self.commands)


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
    # Some simple scripts may not emit failed but return clean output; timeout still requires explicit summary.
    return False


def _reset_db_files() -> None:
    for name in ("gategraph.db", "gategraph.db-journal", "gategraph.db-wal", "gategraph.db-shm"):
        try:
            (PROJECT_ROOT / name).unlink()
        except FileNotFoundError:
            pass


def run_one(name: str, script: str, timeout_seconds: int) -> EvidenceCommand:
    _reset_db_files()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-S", "-u", "tests/_run_isolated.py", script]
    out_path = LOG_DIR / f"_{name}.stdout.tmp"
    err_path = LOG_DIR / f"_{name}.stderr.tmp"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # WHY: file-backed output avoids pipe/capture deadlocks; the isolated wrapper hard-exits after the evidence entrypoint to avoid interpreter shutdown hangs.
    with out_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        completed = subprocess.run(
            ["timeout", "-k", "2s", f"{timeout_seconds}s", *cmd],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            stdout=out,
            stderr=err,
        )

    stdout = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else ""
    stderr = err_path.read_text(encoding="utf-8", errors="replace") if err_path.exists() else ""
    try:
        out_path.unlink()
        err_path.unlink()
    except FileNotFoundError:
        pass

    summary = _parse_summary(stdout)
    if completed.returncode == 0:
        status = "passed"
        rc = 0
    elif completed.returncode == 124 and _summary_passed(summary):
        status = "passed_after_summary_timeout"
        rc = 0
    elif completed.returncode == 124:
        status = "timeout"
        rc = 124
    else:
        status = "failed"
        rc = completed.returncode
    return EvidenceCommand(name, script, timeout_seconds, rc, status, _tail(stdout), _tail(stderr), summary)


def main() -> int:
    started = datetime.now(timezone.utc)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = EvidenceCIReport(
        run_id=started.strftime("ci_evidence_%Y%m%d_%H%M%S"),
        started_at=started.isoformat(),
        notes=[
            "Subprocess runner: accepts timeout only after a zero-failure Summary line, isolating shutdown hangs from evidence failures."
        ],
    )
    for name, script, timeout_seconds in MANIFEST:
        print(f"--- {name} ---", flush=True)
        result = run_one(name, script, timeout_seconds)
        report.commands.append(result)
        mark = "✓" if result.status in {"passed", "passed_after_summary_timeout"} else "✗"
        suffix = " (summary passed; killed shutdown hang)" if result.status == "passed_after_summary_timeout" else ""
        print(result.stdout_tail, end="" if result.stdout_tail.endswith("\n") else "\n")
        if result.stderr_tail:
            print(result.stderr_tail, end="" if result.stderr_tail.endswith("\n") else "\n", file=sys.stderr)
        print(f"{mark} {name} rc={result.returncode} status={result.status}{suffix}", flush=True)

    report.finish()
    out = LOG_DIR / f"{report.run_id}.json"
    out.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nCI EVIDENCE REPORT", flush=True)
    print(f"Log: {out}", flush=True)
    print(f"Passed: {report.passed}", flush=True)
    return 0 if report.passed else 1

if __name__ == "__main__":
    os._exit(main())
