from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "registry" / "evidence_overlap_matrix.json"
DOC = ROOT / "docs" / "EVIDENCE_PROFILE_CLEANUP.md"
CI = ROOT / "tests" / "evidence_ci.py"
REGISTRY = ROOT / "tests" / "evidence_registry.json"
METADATA = ROOT / "RELEASE_METADATA.json"


def check(name: str, ok: bool, detail: dict | None = None) -> tuple[str, bool, dict]:
    detail = detail or {}
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ci_text = CI.read_text(encoding="utf-8")
    entries = {entry["test"] for entry in registry.get("entries", [])}

    checks: list[tuple[str, bool, dict]] = []
    checks.append(check("metadata_current_candidate", metadata.get("release") == "v0.16.6_CANDIDATE" and metadata.get("base") == "v0.16.5_STABLE" and metadata.get("status") == "candidate", {"release": metadata.get("release"), "base": metadata.get("base"), "status": metadata.get("status")}))
    checks.append(check("matrix_current_candidate", matrix.get("release") == metadata.get("release") and matrix.get("base") == metadata.get("base") and matrix.get("status") == metadata.get("status"), {"release": matrix.get("release"), "base": matrix.get("base"), "status": matrix.get("status")}))
    checks.append(check("descriptive_only_no_authority", not matrix.get("runtime_authority") and not matrix.get("auto_pruning") and not matrix.get("auto_repair") and not matrix.get("policy_mutation"), {"runtime_authority": matrix.get("runtime_authority"), "auto_pruning": matrix.get("auto_pruning"), "auto_repair": matrix.get("auto_repair"), "policy_mutation": matrix.get("policy_mutation")}))
    checks.append(check("tests_not_removed", matrix.get("tests_removed") is False and metadata.get("evidence_tests_removed") is False, {"matrix_tests_removed": matrix.get("tests_removed"), "metadata_tests_removed": metadata.get("evidence_tests_removed")}))
    checks.append(check("profiles_declared", len(matrix.get("profiles", {})) >= 4, {"profiles": sorted(matrix.get("profiles", {}).keys())}))
    checks.append(check("overlap_candidates_declared", len(matrix.get("overlap_candidates", [])) >= 3, {"count": len(matrix.get("overlap_candidates", []))}))
    checks.append(check("all_profile_tests_exist_in_registry", all(test in entries for tests in matrix.get("profiles", {}).values() for test in tests), {}))
    checks.append(check("cleanup_gate_in_ci", "evidence_profile_cleanup_evidence" in ci_text, {}))
    checks.append(check("cleanup_gate_in_registry", "evidence_profile_cleanup_evidence" in entries, {}))
    checks.append(check("doc_manifest_surface_present", DOC.exists(), {"doc": str(DOC.relative_to(ROOT))}))

    failed = [name for name, ok, _ in checks if not ok]
    print("EVIDENCE PROFILE CLEANUP REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
