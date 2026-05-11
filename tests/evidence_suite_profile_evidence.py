from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.14.4_CANDIDATE"
EXPECTED_BASE = "v0.14.3_STABLE"


def check(name: str, ok: bool, detail: dict | None = None) -> dict:
    marker = "✓" if ok else "✗"
    print(f"{marker} {name}: {detail or {}}")
    return {"name": name, "ok": ok, "detail": detail or {}}


def main() -> int:
    data = json.loads((ROOT / "registry" / "evidence_suite_profile.json").read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    ci_text = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest_paths = {item["path"] for item in manifest.get("files", [])}

    mandatory = set(data.get("mandatory_for_stable", []))
    profiles = data.get("profiles", {})
    release_profile = set(profiles.get("release", []))

    checks = [
        check("profile_release_current", data.get("release") == EXPECTED_RELEASE, {"release": data.get("release")}),
        check("profile_base_previous_stable", data.get("base") == EXPECTED_BASE, {"base": data.get("base")}),
        check("profile_is_descriptive_only", data.get("profile_mode") == "descriptive_grouping_only", {"mode": data.get("profile_mode")}),
        check("no_runtime_authority", data.get("runtime_authority") is False and data.get("auto_pruning") is False and data.get("auto_promotion") is False, data),
        check("metadata_declares_profile_scope", metadata.get("evidence_suite_profile_scope") is True and metadata.get("evidence_suite_profile_runtime_authority") is False, {"scope": metadata.get("evidence_suite_profile_scope")}),
        check("mandatory_gates_in_release_profile", mandatory.issubset(release_profile), {"missing": sorted(mandatory - release_profile)}),
        check("mandatory_gates_in_ci_manifest", all(name in ci_text for name in mandatory), {"mandatory": sorted(mandatory)}),
        check("profile_registry_manifested", "registry/evidence_suite_profile.json" in manifest_paths, {}),
        check("profile_doc_manifested", "docs/EVIDENCE_SUITE_PROFILE.md" in manifest_paths, {}),
        check("profile_evidence_manifested", "tests/evidence_suite_profile_evidence.py" in manifest_paths, {}),
    ]
    failed = [c for c in checks if not c["ok"]]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": [c["name"] for c in failed]})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
