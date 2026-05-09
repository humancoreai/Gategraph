from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "semantic_registry_evidence.py",
    "invariant_surface_mapping_evidence.py",
    "incident_lifecycle_consistency_evidence.py",
    "semantic_drift_detection_evidence.py",
    "evidence_surface_consistency_evidence.py",
}


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    ci_text = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    release_notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    invariant_registry = json.loads((ROOT / "registry" / "invariant_surface_registry.json").read_text(encoding="utf-8"))
    mapped = {name for spec in invariant_registry["invariants"].values() for name in spec.get("evidence", [])}

    for name in sorted(EXPECTED):
        checks.append(check(f"{name}_file_exists", (ROOT / "tests" / name).exists(), {}))
        checks.append(check(f"{name}_in_ci_manifest", name in ci_text, {}))
        checks.append(check(f"{name}_in_release_notes", name.removesuffix(".py") in release_notes, {}))

    missing_from_mapping = sorted((EXPECTED - {"evidence_surface_consistency_evidence.py"}) - mapped)
    checks.append(check("semantic_evidence_mapped_to_invariants", not missing_from_mapping, {"missing": missing_from_mapping}))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
