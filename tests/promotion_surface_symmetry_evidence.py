from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.15.2_CANDIDATE"
EXPECTED_BASE = "v0.15.1_STABLE"
REQUIRED_SURFACES = [
    "README.md",
    "VERSION.md",
    "RELEASE_NOTES.md",
    "RELEASE_STATUS.md",
    "RELEASE_METADATA.json",
    "RELEASE_MANIFEST.json",
    "docs/RELEASE_v0.15.2_CANDIDATE.md",
    "docs/RELEASE_STATE_TRANSITION.md",
    "registry/release_state_transition_registry.json",
]


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {entry.get("path") for entry in manifest.get("files", []) if isinstance(entry, dict)}
    registry = json.loads((ROOT / "registry" / "release_state_transition_registry.json").read_text(encoding="utf-8"))
    checks = []
    missing = sorted(path for path in REQUIRED_SURFACES if path not in paths and path != "RELEASE_MANIFEST.json")
    checks.append(check("required_transition_surfaces_manifested", not missing, {"missing": missing}))
    checks.append(check("manifest_release_matches_stable", manifest.get("release") == EXPECTED_RELEASE, {"release": manifest.get("release")}))
    checks.append(check("manifest_base_matches_previous_stable", manifest.get("base") == EXPECTED_BASE, {"base": manifest.get("base")}))
    checks.append(check("surface_parity_declared", bool(registry.get("surface_parity", {}).get("allowed_differences")), registry.get("surface_parity", {})))
    text = (ROOT / "docs" / "RELEASE_STATE_TRANSITION.md").read_text(encoding="utf-8")
    checks.append(check("docs_state_manual_not_auto", "auto-promotion" in text and "auto-repair" in text and "candidate -> stable" in text, {}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
