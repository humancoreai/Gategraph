from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _derive_status(release: str) -> str:
    if release.endswith("_CANDIDATE"):
        return "candidate"
    if release.endswith("_STABLE"):
        return "stable"
    return "unknown"


def _derive_future_stable(release: str, status: str) -> str:
    if status == "candidate":
        return release.replace("_CANDIDATE", "_STABLE")
    if status == "stable":
        return release
    return ""


def main() -> int:
    meta = _load_json("RELEASE_METADATA.json")
    constants = _load_json("registry/release_constant_registry.json")
    registry = _load_json("registry/release_status_token_registry.json")
    manifest = _load_json("RELEASE_MANIFEST.json")

    checks: list[tuple[str, bool, dict]] = []

    release = meta["release"]
    status = meta["status"]
    future = meta["future_stable"]
    expected_status = _derive_status(release)
    expected_future = _derive_future_stable(release, status)

    checks.append(("metadata_status_matches_release_suffix", status == expected_status, {"release": release, "status": status}))
    checks.append(("metadata_future_stable_derives_from_status", future == expected_future, {"future_stable": future, "expected": expected_future}))
    checks.append(("manifest_matches_metadata", manifest.get("release") == release and manifest.get("status") == status and manifest.get("base") == meta.get("base"), {"manifest_release": manifest.get("release"), "manifest_status": manifest.get("status")}))

    c = constants["constants"]
    checks.append(("constants_match_metadata", c.get("CURRENT_RELEASE") == release and c.get("CURRENT_STATUS") == status and c.get("CURRENT_BASE") == meta.get("base") and c.get("FUTURE_STABLE") == future, {"constants": c}))

    tokens = registry["tokens"]
    checks.append(("registry_tokens_match_metadata", tokens.get("current_release") == release and tokens.get("current_status") == status and tokens.get("current_base") == meta.get("base") and tokens.get("future_stable") == future, {"tokens": tokens}))
    checks.append(("registry_descriptive_only", not registry.get("runtime_authority") and not registry.get("auto_repair") and not registry.get("auto_promotion") and not registry.get("policy_mutation"), {"mode": registry.get("mode")}))

    required = [
        "registry/release_status_token_registry.json",
        "docs/RELEASE_STATUS_TOKEN_CENTRALIZATION.md",
        "tests/release_status_token_centralization_evidence.py",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    checks.append(("centralization_surfaces_present", not missing, {"missing": missing}))

    failed = [name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        print(("✓" if ok else "✗"), name, detail)
    print("RELEASE STATUS TOKEN CENTRALIZATION EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
