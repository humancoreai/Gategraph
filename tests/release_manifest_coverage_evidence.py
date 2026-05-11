from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COVERAGE = {
    "src/semantic_registry_lock.py",
    "registry/semantic_registry_lock.json",
    "tests/semantic_registry_lock_evidence.py",
    "tests/release_manifest_coverage_evidence.py",
    "registry/semantic_object_types.json",
    "registry/invariant_surface_registry.json",
    "registry/schema_governance_registry.json",
    "docs/SCHEMA_GOVERNANCE.md",
    "docs/RELEASE_v0.14.5_STABLE.md",
    "tests/schema_governance_evidence.py",
    "tests/cross_registry_integrity_evidence.py",
    "tests/deterministic_export_contract_evidence.py",
    "tests/schema_drift_visibility_evidence.py",
    "tests/freeze_snapshot_determinism_evidence.py",
    "tests/candidate_stable_surface_parity_evidence.py",
    "tests/promotion_surface_symmetry_evidence.py",
    "tests/release_state_transition_evidence.py",
    "docs/RELEASE_STATE_TRANSITION.md",
    "registry/release_state_transition_registry.json",
    "registry/governance_integrity_graph.json",
    "docs/GOVERNANCE_INTEGRITY_GRAPH.md",
    "tests/governance_integrity_graph_evidence.py",
    "tests/orphan_governance_artifact_evidence.py",
    "tests/governance_impact_visibility_evidence.py",
    "tests/integrity_graph_freeze_evidence.py",
    "tests/deterministic_governance_diff_evidence.py",
}


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
    missing = sorted(REQUIRED_COVERAGE - paths)
    checks.append(check("release_manifest_declares_registry_lock_surface", not missing, {"missing": missing}))
    checks.append(check("manifest_release_matches_current", manifest.get("release") == "v0.14.5_STABLE", {"release": manifest.get("release")}))
    checks.append(check("manifest_status_candidate", manifest.get("status") == "stable", {"status": manifest.get("status")}))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
