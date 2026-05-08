"""
WHY: CI evidence runner executes GateGraph's proof-oriented test scripts and writes one machine-readable summary.
INV: this file only orchestrates tests; it does not change production governance/enforcement/runtime semantics.
"""
from __future__ import annotations

import json
import subprocess
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
    try:
        proc = subprocess.run(
            args,
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=45,
        )
        return CommandResult(
            name=name,
            command=args,
            returncode=proc.returncode,
            stdout_tail=tail(proc.stdout),
            stderr_tail=tail(proc.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            name=name,
            command=args,
            returncode=124,
            stdout_tail=tail(exc.stdout or ""),
            stderr_tail=tail(exc.stderr or "timeout"),
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
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
