"""
WHY: CI evidence runner executes GateGraph's proof-oriented test scripts and writes one machine-readable summary.
INV: this file only orchestrates tests; it does not change production governance/enforcement/runtime semantics.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


@dataclass
class CommandResult:
    name: str
    command: List[str]
    returncode: int
    stdout_tail: str
    stderr_tail: str


@dataclass
class CIEvidenceReport:
    run_id: str
    started_at: str
    finished_at: str | None = None
    passed: bool = False
    commands: List[CommandResult] = field(default_factory=list)
    produced_logs: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.passed = all(cmd.returncode == 0 for cmd in self.commands)


def tail(text: str, max_chars: int = 4000) -> str:
    return text[-max_chars:] if len(text) > max_chars else text


def run_command(name: str, args: List[str]) -> CommandResult:
    # WHY: some Python environments hang during interpreter shutdown when stdout/stderr are piped.
    # SEC: command timeout is enforced explicitly and failures are reported as evidence, not hidden.
    with tempfile.NamedTemporaryFile(prefix=f"gategraph_{name}_stdout_", mode="w+", encoding="utf-8", delete=True) as out, \
         tempfile.NamedTemporaryFile(prefix=f"gategraph_{name}_stderr_", mode="w+", encoding="utf-8", delete=True) as err:
        try:
            proc = subprocess.Popen(args, cwd=PROJECT_ROOT, text=True, stdout=out, stderr=err)
            try:
                returncode = proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                returncode = 124
                err.write("\ntimeout\n")
        except Exception as exc:
            return CommandResult(name=name, command=args, returncode=125, stdout_tail="", stderr_tail=tail(str(exc)))

        out.flush(); err.flush()
        out.seek(0); err.seek(0)
        return CommandResult(
            name=name,
            command=args,
            returncode=returncode,
            stdout_tail=tail(out.read()),
            stderr_tail=tail(err.read()),
        )

def latest_logs_since(start_marker: float) -> List[str]:
    if not LOG_DIR.exists():
        return []
    logs = []
    for path in LOG_DIR.glob("*.json"):
        try:
            if path.stat().st_mtime >= start_marker:
                logs.append(str(path.relative_to(PROJECT_ROOT)))
        except FileNotFoundError:
            continue
    return sorted(logs)


def main() -> int:
    started = datetime.now(timezone.utc)
    start_marker = datetime.now().timestamp()
    report = CIEvidenceReport(
        run_id=started.strftime("ci_evidence_%Y%m%d_%H%M%S"),
        started_at=started.isoformat(),
    )

    py = [sys.executable, "-S", "-u"]

    commands = [
        ("runtime_stress_evidence", [*py, "tests/runtime_stress_evidence.py"]),
        ("session_budget_evidence", [*py, "tests/session_budget_evidence.py"]),
        ("guard_orchestration_evidence", [*py, "tests/guard_orchestration_evidence.py"]),
        ("reason_normalization_evidence", [*py, "tests/reason_normalization_evidence.py"]),
        ("scale_safety_evidence", [*py, "tests/scale_safety_evidence.py"]),
        ("external_api_evidence", [*py, "tests/external_api_evidence.py"]),
        ("runaway_cost_evidence", [*py, "tests/runaway_cost_evidence.py"]),
        ("core_loop", [*py, "tests/test_loop.py"]),
        ("runtime_guard", [*py, "tests/runtime_guard_tests.py"]),
        ("pattern_engine", [*py, "tests/pattern_engine_tests.py"]),
        ("usage_simulation", [*py, "tests/usage_simulation.py"]),
        ("unusual_inputs", [*py, "tests/unusual_inputs.py"]),
        ("agent_scenarios", [*py, "tests/agent_scenarios.py"]),
    ]

    for name, args in commands:
        result = run_command(name, args)
        report.commands.append(result)
        mark = "✓" if result.returncode == 0 else "✗"
        print(f"{mark} {name} rc={result.returncode}")

    report.produced_logs = latest_logs_since(start_marker)
    if not report.produced_logs:
        report.notes.append("No JSON evidence logs were produced during this CI evidence run.")
    report.finish()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / f"{report.run_id}.json"
    out.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nCI EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Passed: {report.passed}")
    print(f"Produced logs: {report.produced_logs}")
    # WHY: terminate immediately after evidence is written; some environments hang during Python shutdown.
    os._exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
