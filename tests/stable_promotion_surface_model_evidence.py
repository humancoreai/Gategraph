from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def _is_current_stable_claim(text: str, stable_token: str) -> bool:
    return any(marker in text for marker in (
        f"Release: {stable_token}",
        f"Release: **{stable_token}**",
        f"Current release: {stable_token}",
        f"Current release: **{stable_token}**",
        f"Current stable baseline: {stable_token}",
        f"Current stable baseline: **{stable_token}**",
    ))


def main() -> int:
    metadata = json.loads(read("RELEASE_METADATA.json"))
    registry = json.loads(read("registry/stable_promotion_surface_model.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    manifest_paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict) and "path" in entry}

    release = metadata["release"]
    base = metadata["base"]
    status = metadata["status"]
    candidate_mode = release.endswith("_CANDIDATE") and status == "candidate"
    stable_mode = release.endswith("_STABLE") and status == "stable"
    future_stable = release.replace("_CANDIDATE", "_STABLE") if candidate_mode else release

    checks = []
    checks.append(check("metadata_status_matches_release_token", (candidate_mode and release.endswith("_CANDIDATE")) or (stable_mode and release.endswith("_STABLE")), {"release": release, "status": status}))
    checks.append(check("base_is_stable_reference", base.endswith("_STABLE"), {"base": base}))
    checks.append(check("model_declared_descriptive_only", registry.get("mode") == "descriptive_stable_promotion_surface_model_only", {"mode": registry.get("mode")}))
    checks.append(check("no_runtime_or_repair_authority", registry.get("runtime_authority") is False and registry.get("auto_promotion") is False and registry.get("auto_repair") is False and registry.get("policy_mutation") is False, {"runtime_authority": registry.get("runtime_authority"), "auto_promotion": registry.get("auto_promotion"), "auto_repair": registry.get("auto_repair"), "policy_mutation": registry.get("policy_mutation")}))
    checks.append(check("future_stable_token_derivation_matches_status", registry.get("future_stable_token") == future_stable and ((candidate_mode and future_stable != release) or (stable_mode and future_stable == release)), {"future_stable": registry.get("future_stable_token"), "release": release, "status": status}))

    missing_release = []
    missing_manifest = []
    accidental_stable_claims = []
    for path in registry.get("required_candidate_surfaces", []):
        text = read(path)
        if release not in text:
            missing_release.append(path)
        if path != "RELEASE_MANIFEST.json" and path not in manifest_paths:
            missing_manifest.append(path)
        if candidate_mode and path in {"README.md", "VERSION.md", "RELEASE_STATUS.md", "RELEASE_NOTES.md"} and _is_current_stable_claim(text, future_stable):
            # INV: Candidate surfaces may reference the previous stable base, but must not claim their future Stable as current release.
            accidental_stable_claims.append(path)

    checks.append(check("release_surfaces_name_current_release", not missing_release, {"missing": missing_release}))
    checks.append(check("release_surfaces_manifested", not missing_manifest, {"missing": missing_manifest}))
    checks.append(check("candidate_public_surfaces_do_not_claim_future_stable", not accidental_stable_claims, {"stable_claims": accidental_stable_claims, "status": status}))

    required_differences = {"release", "status", "release_doc_path", "zip_name", "root_folder", "manifest_kind"}
    allowed = set(registry.get("allowed_candidate_to_stable_differences", []))
    checks.append(check("stable_allowed_differences_declared", required_differences <= allowed, {"allowed": sorted(allowed)}))

    checks.append(check("docs_and_registry_manifested", "docs/STABLE_PROMOTION_SURFACE_MODEL.md" in manifest_paths and "registry/stable_promotion_surface_model.json" in manifest_paths and "tests/stable_promotion_surface_model_evidence.py" in manifest_paths, {"doc": "docs/STABLE_PROMOTION_SURFACE_MODEL.md" in manifest_paths, "registry": "registry/stable_promotion_surface_model.json" in manifest_paths, "test": "tests/stable_promotion_surface_model_evidence.py" in manifest_paths}))

    failed = [name for name, ok, _ in checks if not ok]
    print("STABLE PROMOTION SURFACE MODEL EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
