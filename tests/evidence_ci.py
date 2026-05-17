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

# GitHub Actions Windows consoles may default to cp1252; evidence output contains Unicode markers.
# Force UTF-8 with replacement so logging never becomes a CI failure mode.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"

MANIFEST: List[Tuple[str, str, int]] = [
    ("evidence_runner_selftest", "tests/evidence_runner_selftest.py", 10),
    ("evidence_registry_evidence", "tests/evidence_registry_evidence.py", 20),
    ("promotion_status_ssot_evidence", "tests/promotion_status_ssot_evidence.py", 30),
    ("promotion_surface_matrix_evidence", "tests/promotion_surface_matrix_evidence.py", 30),
    ("stable_surface_separation_evidence", "tests/stable_surface_separation_evidence.py", 30),
    ("release_truth_centralization_evidence", "tests/release_truth_centralization_evidence.py", 30),
    ("release_constant_registry_evidence", "tests/release_constant_registry_evidence.py", 20),
    ("runtime_stress_evidence", "tests/runtime_stress_evidence.py", 40, {"GATEGRAPH_RUNTIME_STRESS_PROFILE": "ci"}),
    ("session_budget_evidence", "tests/session_budget_evidence.py", 40),
    ("guard_orchestration_evidence", "tests/guard_orchestration_evidence.py", 30),
    ("reason_normalization_evidence", "tests/reason_normalization_evidence.py", 20),
    ("scale_safety_evidence", "tests/scale_safety_evidence.py", 30),
    ("external_api_evidence", "tests/external_api_evidence.py", 30),
    ("runaway_cost_evidence", "tests/runaway_cost_evidence.py", 20),
    ("runtime_cost_governance_evidence", "tests/runtime_cost_governance_evidence.py", 20),
    ("observability_evidence", "tests/observability_evidence.py", 20),
    ("failure_analysis_evidence", "tests/failure_analysis_evidence.py", 30),
    ("operator_workflow_evidence", "tests/operator_workflow_evidence.py", 20),
    ("human_review_queue_evidence", "tests/human_review_queue_evidence.py", 20),
    ("drift_detection_evidence", "tests/drift_detection_evidence.py", 20),
    ("governance_archive_replay_evidence", "tests/governance_archive_replay_evidence.py", 20),
    ("archive_integrity_replay_consistency_evidence", "tests/archive_integrity_replay_consistency_evidence.py", 20),
    ("operator_export_evidence", "tests/operator_export_evidence.py", 20),
    ("final_consolidation_evidence", "tests/final_consolidation_evidence.py", 20),
    ("governance_freeze_evidence", "tests/governance_freeze_evidence.py", 20),
    ("milestone_release_evidence", "tests/milestone_release_evidence.py", 30),
    ("caller_boundary_evidence", "tests/caller_boundary_evidence.py", 20),
    ("runtime_boundary_hardening_evidence", "tests/runtime_boundary_hardening_evidence.py", 20),
    ("api_boundary_split_evidence", "tests/api_boundary_split_evidence.py", 20),
    ("freeze_runtime_invariant_evidence", "tests/freeze_runtime_invariant_evidence.py", 20),
    ("runtime_chain_order_evidence", "tests/runtime_chain_order_evidence.py", 20),
    ("release_integrity_evidence", "tests/release_integrity_evidence.py", 40),
    ("release_process_guard_evidence", "tests/release_process_guard_evidence.py", 20),
    ("packaging_integrity_evidence", "tests/packaging_integrity_evidence.py", 20),
    ("release_content_hygiene_evidence", "tests/release_content_hygiene_evidence.py", 20),
    ("install_surface_evidence", "tests/install_surface_evidence.py", 30),
    ("config_consistency_evidence", "tests/config_consistency_evidence.py", 20),
    ("startup_surface_evidence", "tests/startup_surface_evidence.py", 20),
    ("startup_shutdown_semantics_evidence", "tests/startup_shutdown_semantics_evidence.py", 40),
    ("runtime_surface_consistency_evidence", "tests/runtime_surface_consistency_evidence.py", 30),
    ("surface_freeze_coupling_evidence", "tests/surface_freeze_coupling_evidence.py", 30),
    ("mode_boundary_surface_evidence", "tests/mode_boundary_surface_evidence.py", 20),
    ("multi_agent_architecture_evidence", "tests/multi_agent_architecture_evidence.py", 20),
    ("multi_agent_delegation_boundary_evidence", "tests/multi_agent_delegation_boundary_evidence.py", 20),
    ("context_poisoning_evidence", "tests/context_poisoning_evidence.py", 20),
    ("instruction_data_separation_evidence", "tests/instruction_data_separation_evidence.py", 20),
    ("context_provenance_evidence", "tests/context_provenance_evidence.py", 20),
    ("context_lifecycle_evidence", "tests/context_lifecycle_evidence.py", 20),
    ("context_replay_explain_boundary_evidence", "tests/context_replay_explain_boundary_evidence.py", 20),
    ("context_freeze_coupling_evidence", "tests/context_freeze_coupling_evidence.py", 20),
    ("recovery_foundation_evidence", "tests/recovery_foundation_evidence.py", 20),
    ("replay_recovery_consistency_evidence", "tests/replay_recovery_consistency_evidence.py", 20),
    ("replay_recovery_hardening_evidence", "tests/replay_recovery_hardening_evidence.py", 20),
    ("runtime_budget_edge_hardening_evidence", "tests/runtime_budget_edge_hardening_evidence.py", 20),
    ("release_ssot_candidate_evidence", "tests/release_ssot_candidate_evidence.py", 20),
    ("semantic_boundary_preparation_evidence", "tests/semantic_boundary_preparation_evidence.py", 20),
    ("surface_recovery_consistency_evidence", "tests/surface_recovery_consistency_evidence.py", 20),
    ("recovery_idempotency_evidence", "tests/recovery_idempotency_evidence.py", 20),
    ("replay_order_determinism_evidence", "tests/replay_order_determinism_evidence.py", 20),
    ("recovery_surface_registry_evidence", "tests/recovery_surface_registry_evidence.py", 20),
    ("release_surface_sync_evidence", "tests/release_surface_sync_evidence.py", 20),
    ("release_claim_consistency_evidence", "tests/release_claim_consistency_evidence.py", 20),
    ("recovery_replay_finality_evidence", "tests/recovery_replay_finality_evidence.py", 20),
    ("replay_reference_integrity_evidence", "tests/replay_reference_integrity_evidence.py", 20),
    ("version_consistency_evidence", "tests/version_consistency_evidence.py", 20),
    ("surface_contract_registry_evidence", "tests/surface_contract_registry_evidence.py", 20),
    ("semantic_boundary_evidence", "tests/semantic_boundary_evidence.py", 20),
    ("semantic_registry_evidence", "tests/semantic_registry_evidence.py", 20),
    ("invariant_surface_mapping_evidence", "tests/invariant_surface_mapping_evidence.py", 20),
    ("incident_lifecycle_consistency_evidence", "tests/incident_lifecycle_consistency_evidence.py", 20),
    ("semantic_drift_detection_evidence", "tests/semantic_drift_detection_evidence.py", 20),
    ("evidence_surface_consistency_evidence", "tests/evidence_surface_consistency_evidence.py", 20),
    ("semantic_registry_lock_evidence", "tests/semantic_registry_lock_evidence.py", 20),
    ("release_manifest_coverage_evidence", "tests/release_manifest_coverage_evidence.py", 20),
    ("schema_governance_evidence", "tests/schema_governance_evidence.py", 20),
    ("cross_registry_integrity_evidence", "tests/cross_registry_integrity_evidence.py", 20),
    ("deterministic_export_contract_evidence", "tests/deterministic_export_contract_evidence.py", 20),
    ("schema_drift_visibility_evidence", "tests/schema_drift_visibility_evidence.py", 20),
    ("freeze_snapshot_determinism_evidence", "tests/freeze_snapshot_determinism_evidence.py", 20),
    ("evidence_provenance_registry_evidence", "tests/evidence_provenance_registry_evidence.py", 20),
    ("governance_lineage_snapshot_evidence", "tests/governance_lineage_snapshot_evidence.py", 20),
    ("dependency_visibility_evidence", "tests/dependency_visibility_evidence.py", 20),
    ("governance_mutation_visibility_evidence", "tests/governance_mutation_visibility_evidence.py", 20),
    ("replay_provenance_consistency_evidence", "tests/replay_provenance_consistency_evidence.py", 20),
    ("release_state_transition_evidence", "tests/release_state_transition_evidence.py", 20),
    ("candidate_ci_gate_evidence", "tests/candidate_ci_gate_evidence.py", 20),
    ("evidence_suite_profile_evidence", "tests/evidence_suite_profile_evidence.py", 20),
    ("evidence_failure_classification_evidence", "tests/evidence_failure_classification_evidence.py", 20),
    ("evidence_maintainability_evidence", "tests/evidence_maintainability_evidence.py", 20),
    ("public_surface_cleanup_evidence", "tests/public_surface_cleanup_evidence.py", 20),
    ("scope_backlog_evidence", "tests/scope_backlog_evidence.py", 20),
    ("review_readiness_surface_evidence", "tests/review_readiness_surface_evidence.py", 20),
    ("promotion_status_ssot_evidence", "tests/promotion_status_ssot_evidence.py", 20),
    ("promotion_surface_matrix_evidence", "tests/promotion_surface_matrix_evidence.py", 20),
    ("promotion_pipeline_hardening_evidence", "tests/promotion_pipeline_hardening_evidence.py", 20),
    ("release_gate_robustness_evidence", "tests/release_gate_robustness_evidence.py", 20),
    ("failure_root_cause_grouping_evidence", "tests/failure_root_cause_grouping_evidence.py", 20),
    ("artifact_determinism_evidence", "tests/artifact_determinism_evidence.py", 20),
    ("artifact_surface_hygiene_evidence", "tests/artifact_surface_hygiene_evidence.py", 20),
    ("fresh_clone_surface_validation_evidence", "tests/fresh_clone_surface_validation_evidence.py", 20),
    ("github_actions_ci_evidence", "tests/github_actions_ci_evidence.py", 20),
    ("stable_promotion_surface_model_evidence", "tests/stable_promotion_surface_model_evidence.py", 20),
    ("promotion_surface_symmetry_evidence", "tests/promotion_surface_symmetry_evidence.py", 20),
    ("candidate_stable_surface_parity_evidence", "tests/candidate_stable_surface_parity_evidence.py", 20),
    ("governance_integrity_graph_evidence", "tests/governance_integrity_graph_evidence.py", 20),
    ("orphan_governance_artifact_evidence", "tests/orphan_governance_artifact_evidence.py", 20),
    ("governance_impact_visibility_evidence", "tests/governance_impact_visibility_evidence.py", 20),
    ("integrity_graph_freeze_evidence", "tests/integrity_graph_freeze_evidence.py", 20),
    ("deterministic_governance_diff_evidence", "tests/deterministic_governance_diff_evidence.py", 20),
    ("root_surface_hygiene_evidence", "tests/root_surface_hygiene_evidence.py", 20),
    ("governance_semantics_evidence", "tests/governance_semantics_evidence.py", 20),
    ("operator_evidence", "tests/operator_evidence.py", 20),
    ("cross_session_budget_evidence", "tests/cross_session_budget_evidence.py", 20),
    ("operational_hardening_evidence", "tests/operational_hardening_evidence.py", 20),
    ("operational_alerting_evidence", "tests/operational_alerting_evidence.py", 20),
    ("operational_stability_evidence", "tests/operational_stability_evidence.py", 20),
    ("single_node_cli_evidence", "tests/single_node_cli_evidence.py", 20),
    ("practical_single_node_scenario_evidence", "tests/practical_single_node_scenario_evidence.py", 20),
    ("public_repo_hygiene_evidence", "tests/public_repo_hygiene_evidence.py", 20),
    ("fresh_clone_reproducibility_evidence", "tests/fresh_clone_reproducibility_evidence.py", 20),
    ("single_node_monitoring_export_evidence", "tests/single_node_monitoring_export_evidence.py", 20),
    ("server_mode_evidence", "tests/server_mode_evidence.py", 20),
    ("server_hardening_evidence", "tests/server_hardening_evidence.py", 20),
    ("api_contract_evidence", "tests/api_contract_evidence.py", 20),
    ("api_robustness_evidence", "tests/api_robustness_evidence.py", 30),
    ("repo_push_hygiene_evidence", "tests/repo_push_hygiene_evidence.py", 20),
    ("capability_token_hardening_evidence", "tests/capability_token_hardening_evidence.py", 30),
    ("capability_token_redaction_evidence", "tests/capability_token_redaction_evidence.py", 20),
    ("token_exposure_evidence", "tests/token_exposure_evidence.py", 20),
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
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # INV: Legacy direct-governance evidence uses an explicit test-only trusted-entry compatibility path.
    env["GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE"] = "1"
    if extra_env:
        env.update(extra_env)

    cmd = [sys.executable, "-S", "-u", "tests/_run_isolated.py", script]
    started = time.monotonic()
    timed_out = False
    killed_group = False
    rc: int | None = None
    stdout = ""
    stderr = ""

    if os.name == "posix":
        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=True,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        killed_group = _kill_process_group(proc)
        try:
            extra_out, extra_err = proc.communicate(timeout=2)
            stdout = (stdout or "") + (extra_out or "")
            stderr = (stderr or "") + (extra_err or "")
        except subprocess.TimeoutExpired:
            killed_group = _kill_process_group(proc) or killed_group
            stdout = stdout or ""
            stderr = stderr or ""
        rc = 124
        killed_group = True if killed_group or timed_out else False

    duration = time.monotonic() - started
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
        reset_warnings=reset_warnings,
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
            "Legacy direct-governance evidence uses an explicit test-only trusted-entry compatibility path."
        ],
    )
    for command in MANIFEST:
        if len(command) == 4:
            name, script, timeout_seconds, extra_env = command
        else:
            name, script, timeout_seconds = command
            extra_env = None
        print(f"--- {name} ---", flush=True)
        result = run_one(name, script, timeout_seconds, extra_env=extra_env)
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
