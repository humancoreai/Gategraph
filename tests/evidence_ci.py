"""
WHY: CI evidence runner executes GateGraph's proof-oriented test scripts and writes one machine-readable summary.
INV: this file only orchestrates tests; it does not change production governance/enforcement/runtime semantics.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = PROJECT_ROOT / "tests"
LOG_DIR = TESTS_DIR / "logs"

for import_path in (str(PROJECT_ROOT), str(TESTS_DIR)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

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

def load_callable(script_name: str, callable_name: str) -> Callable[[], object]:
    script_path = TESTS_DIR / script_name
    module_name = f"gategraph_ci_{script_path.stem}_{abs(hash(str(script_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    fn = getattr(module, callable_name)
    if not callable(fn):
        raise RuntimeError(f"{script_name}:{callable_name} is not callable")
    return fn

def run_callable(name: str, script_name: str, callable_name: str) -> CommandResult:
    stdout = io.StringIO()
    stderr = io.StringIO()
    returncode = 0
    old_cwd = Path.cwd()
    try:
        os.chdir(PROJECT_ROOT)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            fn = load_callable(script_name, callable_name)
            try:
                result = fn()
                if isinstance(result, int):
                    returncode = result
            except SystemExit as exc:
                code = exc.code
                returncode = int(code) if isinstance(code, int) else (0 if code is None else 1)
    except Exception as exc:
        returncode = 125
        stderr.write(f"{type(exc).__name__}: {exc}\n")
    finally:
        os.chdir(old_cwd)
    return CommandResult(name, ["in-process", script_name, callable_name], returncode, tail(stdout.getvalue()), tail(stderr.getvalue()))

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
    report = CIEvidenceReport(run_id=started.strftime("ci_evidence_%Y%m%d_%H%M%S"), started_at=started.isoformat())
    commands = [
        ("runtime_stress_evidence", "runtime_stress_evidence.py", "main"),
        ("session_budget_evidence", "session_budget_evidence.py", "main"),
        ("guard_orchestration_evidence", "guard_orchestration_evidence.py", "main"),
        ("reason_normalization_evidence", "reason_normalization_evidence.py", "main"),
        ("scale_safety_evidence", "scale_safety_evidence.py", "main"),
        ("external_api_evidence", "external_api_evidence.py", "main"),
        ("runaway_cost_evidence", "runaway_cost_evidence.py", "main"),
        ("capability_token_hardening_evidence", "capability_token_hardening_evidence.py", "main"),
        ("key_rotation_evidence", "key_rotation_evidence.py", "main"),
        ("secret_api_integration_evidence", "secret_api_integration_evidence.py", "main"),
        ("http_policy_evidence", "http_policy_evidence.py", "main"),
        ("security_finesse_evidence", "security_finesse_evidence.py", "main"),
        ("core_loop", "test_loop.py", "main"),
        ("runtime_guard", "runtime_guard_tests.py", "main"),
        ("pattern_engine", "pattern_engine_tests.py", "main"),
        ("usage_simulation", "usage_simulation.py", "run"),
        ("unusual_inputs", "unusual_inputs.py", "run"),
        ("agent_scenarios", "agent_scenarios.py", "run"),
    ]
    for name, script_name, callable_name in commands:
        result = run_callable(name, script_name, callable_name)
        report.commands.append(result)
        mark = "✓" if result.returncode == 0 else "✗"
        print(f"{mark} {name} rc={result.returncode}", flush=True)
    report.produced_logs = latest_logs_since(start_marker)
    if not report.produced_logs:
        report.notes.append("No JSON evidence logs were produced during this CI evidence run.")
    report.finish()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / f"{report.run_id}.json"
    out.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nCI EVIDENCE REPORT", flush=True)
    print(f"Log: {out}", flush=True)
    print(f"Passed: {report.passed}", flush=True)
    print(f"Produced logs: {report.produced_logs}", flush=True)
    return 0 if report.passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
