from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    metadata = json.loads(read("RELEASE_METADATA.json"))
    registry = json.loads(read("registry/stable_surface_separation.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict)}

    release = metadata["release"]
    base = metadata["base"]
    status = metadata["status"]
    candidate_mode = status == "candidate"
    future_stable = release.replace("_CANDIDATE", "_STABLE")

    checks = []
    checks.append(check("metadata_status_matches_release_token", release == "v0.15.6_CANDIDATE" and base == "v0.15.5_STABLE" and status == "candidate", {"release": release, "base": base, "status": status}))
    checks.append(check("registry_descriptive_only", registry.get("mode") == "descriptive_stable_surface_separation_only", {"mode": registry.get("mode")}))
    checks.append(check("no_runtime_or_repair_authority", registry.get("runtime_authority") is False and registry.get("auto_promotion") is False and registry.get("auto_repair") is False and registry.get("policy_mutation") is False, {"runtime_authority": registry.get("runtime_authority"), "auto_promotion": registry.get("auto_promotion"), "auto_repair": registry.get("auto_repair"), "policy_mutation": registry.get("policy_mutation")}))

    missing_release = []
    missing_base = []
    accidental_stable_current = []
    for surface in registry.get("current_release_surfaces", []):
        text = read(surface)
        if release not in text:
            missing_release.append(surface)
        if surface in {"README.md", "VERSION.md", "RELEASE_STATUS.md", "RELEASE_NOTES.md", "CHANGELOG.md", "RELEASE_METADATA.json", "docs/RELEASE_v0.15.6_CANDIDATE.md"} and base not in text:
            missing_base.append(surface)
        # EDGE: Only Candidate surfaces are forbidden from claiming their future Stable as current.
        # In Stable status, the stable token is expected on public release surfaces.
        if candidate_mode and surface in {"README.md", "VERSION.md", "RELEASE_STATUS.md", "RELEASE_NOTES.md"} and future_stable != base and future_stable in text:
            accidental_stable_current.append(surface)

    checks.append(check("candidate_release_surfaces_name_current_candidate", not missing_release, {"missing": missing_release}))
    checks.append(check("candidate_release_surfaces_name_previous_stable_base", not missing_base, {"missing": missing_base}))
    checks.append(check("public_surfaces_do_not_claim_future_stable", not accidental_stable_current, {"stable_claims": accidental_stable_current, "status": status}))

    required_paths = {
        "docs/STABLE_SURFACE_SEPARATION.md",
        "registry/stable_surface_separation.json",
        "tests/stable_surface_separation_evidence.py",
    }
    checks.append(check("separation_surfaces_manifested", required_paths <= paths, {"missing": sorted(required_paths - paths)}))

    failed = [name for name, ok, _ in checks if not ok]
    print("STABLE SURFACE SEPARATION EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
