from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "candidate_stable_surface_parity_evidence.py",
    "promotion_surface_symmetry_evidence.py",
    "release_state_transition_evidence.py",
    "replay_provenance_consistency_evidence.py",
    "governance_mutation_visibility_evidence.py",
    "dependency_visibility_evidence.py",
    "governance_lineage_snapshot_evidence.py",
    "evidence_provenance_registry_evidence.py",
    "semantic_registry_evidence.py",
    "invariant_surface_mapping_evidence.py",
    "incident_lifecycle_consistency_evidence.py",
    "semantic_drift_detection_evidence.py",
    "evidence_surface_consistency_evidence.py",
    "semantic_registry_lock_evidence.py",
    "release_manifest_coverage_evidence.py",
    "schema_governance_evidence.py",
    "cross_registry_integrity_evidence.py",
    "deterministic_export_contract_evidence.py",
    "schema_drift_visibility_evidence.py",
    "freeze_snapshot_determinism_evidence.py",
}


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    ci_text = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    evidence_registry = json.loads((ROOT / "tests" / "evidence_registry.json").read_text(encoding="utf-8"))
    registered = {entry.get("path", "").split("/")[-1] for entry in evidence_registry.get("entries", [])}
    invariant_registry = json.loads((ROOT / "registry" / "invariant_surface_registry.json").read_text(encoding="utf-8"))
    mapped = {name for spec in invariant_registry["invariants"].values() for name in spec.get("evidence", [])}

    for name in sorted(EXPECTED):
        checks.append(check(f"{name}_file_exists", (ROOT / "tests" / name).exists(), {}))
        checks.append(check(f"{name}_in_ci_manifest", name in ci_text, {}))
        checks.append(check(f"{name}_in_evidence_registry", name in registered, {}))

    missing_from_mapping = sorted((EXPECTED - {"evidence_surface_consistency_evidence.py"}) - mapped)
    checks.append(check("semantic_evidence_mapped_to_invariants", not missing_from_mapping, {"missing": missing_from_mapping}))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
