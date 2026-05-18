from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(name: str, ok: bool, detail: dict | None = None, failed: list[str] | None = None) -> None:
    marker = "✓" if ok else "✗"
    print(marker, name, detail or {})
    if not ok and failed is not None:
        failed.append(name)


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "registry" / "release_status_assertion_policy.json").read_text(encoding="utf-8"))
    release = metadata["release"]
    status = metadata["status"]
    expected_status = "stable" if release.endswith("_CANDIDATE") else "stable" if release.endswith("_STABLE") else None
    failed: list[str] = []

    check("metadata_status_derives_from_release_suffix", status == expected_status, {"release": release, "status": status, "expected": expected_status}, failed)
    check("registry_current_release", registry.get("release") == release and registry.get("status") == status, {"registry_release": registry.get("release"), "registry_status": registry.get("status")}, failed)
    check("descriptive_only_no_authority", not any(registry.get(k) for k in ("runtime_authority", "auto_repair", "auto_pruning", "policy_mutation")), {k: registry.get(k) for k in ("runtime_authority", "auto_repair", "auto_pruning", "policy_mutation")}, failed)

    monitored = [
        "tests/promotion_status_ssot_evidence.py",
        "tests/promotion_surface_matrix_evidence.py",
        "tests/release_surface_sync_evidence.py",
        "tests/release_claim_consistency_evidence.py",
        "tests/version_consistency_evidence.py",
        "tests/evidence_maintainability_evidence.py",
        "tests/release_gate_robustness_evidence.py",
        "tests/candidate_stable_surface_parity_evidence.py",
    ]
    missing = [p for p in monitored if not (ROOT / p).exists()]
    check("monitored_status_sensitive_gates_exist", not missing, {"missing": missing}, failed)

    # Focused safeguard: the formerly drifting gates must no longer assert a single literal status as the only allowed state.
    offenders = []
    for rel in monitored:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if 'status == "candidate"' in text or "status == 'candidate'" in text or 'status == "stable"' in text or "status == 'stable'" in text:
            offenders.append(rel)
    check("no_single_status_literal_assertions_in_monitored_gates", not offenders, {"offenders": offenders}, failed)

    manifested = []
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest.get("files", [])}
    for required in ["registry/release_status_assertion_policy.json", "docs/RELEASE_STATUS_ASSERTION_POLICY.md", "tests/release_status_assertion_policy_evidence.py"]:
        if required not in paths:
            manifested.append(required)
    check("policy_surfaces_manifested", not manifested, {"missing": manifested}, failed)

    print("RELEASE STATUS ASSERTION POLICY EVIDENCE REPORT")
    print({"passed": 6 - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
