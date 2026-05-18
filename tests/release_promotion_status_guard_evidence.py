from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_STATUS = None


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _derive_future_stable(release: str, status: str) -> str:
    if status == "candidate":
        return release.replace("_CANDIDATE", "_STABLE")
    if status == "stable":
        return release
    return ""


def _surface_state(path: str) -> dict:
    data = _load(path)
    state = {
        "release": data.get("release"),
        "base": data.get("base"),
        "status": data.get("status"),
    }
    if "constants" in data:
        constants = data["constants"]
        state.update({
            "release": constants.get("CURRENT_RELEASE"),
            "base": constants.get("CURRENT_BASE"),
            "status": constants.get("CURRENT_STATUS"),
            "future_stable": constants.get("FUTURE_STABLE"),
        })
    if "tokens" in data:
        tokens = data["tokens"]
        state.update({
            "release": tokens.get("current_release"),
            "base": tokens.get("current_base"),
            "status": tokens.get("current_status"),
            "future_stable": tokens.get("future_stable"),
        })
    return state


def main() -> int:
    meta = _load("RELEASE_METADATA.json")
    registry = _load("registry/release_promotion_status_guard.json")
    manifest = _load("RELEASE_MANIFEST.json") if (ROOT / "RELEASE_MANIFEST.json").exists() else {"files": []}

    release = meta["release"]
    base = meta["base"]
    status = meta["status"]
    future = meta.get("future_stable", _derive_future_stable(release, status))

    checks: list[tuple[str, bool, dict]] = []
    expected_status = "stable" if release.endswith("_CANDIDATE") else "stable" if release.endswith("_STABLE") else "unknown"
    checks.append(("metadata_current_release", release == "v0.17.4_STABLE" and base == "v0.17.3_STABLE" and status == expected_status, {"release": release, "base": base, "status": status}))
    checks.append(("guard_registry_current_release", registry.get("release") == release and registry.get("base") == base and registry.get("status") == status, {"registry": {"release": registry.get("release"), "base": registry.get("base"), "status": registry.get("status")}}))
    checks.append(("descriptive_only_no_authority", not registry.get("runtime_authority") and not registry.get("auto_repair") and not registry.get("auto_promotion") and not registry.get("policy_mutation"), {"mode": registry.get("mode")}))

    drift = []
    for path in registry.get("checked_surfaces", []):
        state = _surface_state(path)
        if state.get("release") != release or state.get("base") != base or state.get("status") != status:
            drift.append({"path": path, "state": state})
        if state.get("future_stable") is not None and state.get("future_stable") != future:
            drift.append({"path": path, "future_stable": state.get("future_stable"), "expected": future})
    checks.append(("checked_registry_surfaces_match_metadata", not drift, {"drift": drift}))

    required = [
        "docs/RELEASE_PROMOTION_STATUS_GUARD.md",
        "registry/release_promotion_status_guard.json",
        "tests/release_promotion_status_guard_evidence.py",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    checks.append(("guard_surfaces_present", not missing, {"missing": missing}))
    manifest_paths = {entry.get("path") for entry in manifest.get("files", []) if isinstance(entry, dict)}
    missing_manifest = [path for path in required if manifest_paths and path not in manifest_paths]
    checks.append(("guard_surfaces_manifested", not missing_manifest, {"missing": missing_manifest}))

    failed = [name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        print(("✓" if ok else "✗"), name, detail)
    print("RELEASE PROMOTION STATUS GUARD EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
