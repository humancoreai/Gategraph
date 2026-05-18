"""
WHY: Evidence profiles should make local validation less noisy without weakening full CI gates.
INV: Profiles are descriptive execution bundles only; they do not prune, demote, or bypass evidence.
SEC: Mandatory release gates remain in full CI and no profile has runtime, repair, or promotion authority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def ci_names() -> set[str]:
    text = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    names: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('("'):
            names.add(line.split('"', 2)[1])
    return names


def check(name: str, ok: bool, detail=None, failures=None):
    marker = "✓" if ok else "✗"
    print(f"{marker} {name}: {detail if detail is not None else {}}")
    if not ok:
        failures.append(name)


def main() -> int:
    failures: list[str] = []
    registry = load_json("registry/evidence_runtime_profiles.json")
    metadata = load_json("RELEASE_METADATA.json")
    manifest = load_json("RELEASE_MANIFEST.json")
    ci = ci_names()

    check("metadata_current_release", metadata.get("release") == "v0.17.2_CANDIDATE" and metadata.get("status") in {"candidate", "stable"}, {"release": metadata.get("release"), "status": metadata.get("status")}, failures)
    check("registry_current_release", registry.get("release") == metadata.get("release") and registry.get("base") == metadata.get("base") and registry.get("status") == metadata.get("status"), {"release": registry.get("release"), "base": registry.get("base"), "status": registry.get("status")}, failures)
    check("descriptive_only_no_authority", not any(registry.get(k) for k in ["runtime_authority", "auto_pruning", "auto_repair", "auto_promotion", "policy_mutation"]), {k: registry.get(k) for k in ["runtime_authority", "auto_pruning", "auto_repair", "auto_promotion", "policy_mutation"]}, failures)
    check("tests_not_removed", registry.get("tests_removed") is False and metadata.get("tests_removed") is False, {"registry": registry.get("tests_removed"), "metadata": metadata.get("tests_removed")}, failures)

    profiles = registry.get("profiles", {})
    for profile_name in ["release_fast", "core_runtime", "security_boundary"]:
        items = profiles.get(profile_name)
        missing = sorted(name for name in items if name not in ci)
        check(f"{profile_name}_tests_exist_in_full_ci", isinstance(items, list) and not missing, {"count": len(items or []), "missing": missing}, failures)

    mandatory = set(load_json("registry/evidence_suite_profile.json").get("mandatory_for_stable", []))
    release_fast = set(profiles.get("release_fast", []))
    check("mandatory_release_gates_covered_by_release_fast_or_full_ci", mandatory.issubset(ci) and {"release_integrity_evidence", "release_process_guard_evidence", "semantic_registry_lock_evidence"}.issubset(release_fast), {"mandatory_count": len(mandatory)}, failures)

    paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict) and "path" in entry}
    required = {
        "registry/evidence_runtime_profiles.json",
        "docs/EVIDENCE_RUNTIME_PROFILES.md",
        "tests/evidence_runtime_profile_evidence.py",
    }
    check("runtime_profile_surfaces_manifested", required.issubset(paths), {"missing": sorted(required - paths)}, failures)
    check("runtime_profile_gate_in_ci", "evidence_runtime_profile_evidence" in ci, {}, failures)

    print("EVIDENCE RUNTIME PROFILE REPORT")
    print({"passed": 9 - len(failures), "failed": len(failures), "failed_checks": failures})
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
