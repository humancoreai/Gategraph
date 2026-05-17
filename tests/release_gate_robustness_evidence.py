from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.16.7_STABLE"
EXPECTED_BASE = "v0.16.6_STABLE"
EXPECTED_STATUS = "stable"
SURFACES = [
    "README.md",
    "VERSION.md",
    "RELEASE_NOTES.md",
    "RELEASE_STATUS.md",
    "RELEASE_METADATA.json",
    "pyproject.toml",
    "tools/build_release.py",
    "tools/verify_release.py",
    "docs/RELEASE_v0.16.7_STABLE.md",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: dict | None = None) -> dict:
    print(("✓" if ok else "✗") + f" {name}: {detail or {}}")
    return {"name": name, "ok": ok, "detail": detail or {}}


def main() -> int:
    metadata = json.loads(read("RELEASE_METADATA.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    registry = json.loads(read("registry/release_gate_robustness.json"))
    transition = json.loads(read("registry/release_state_transition_registry.json"))
    manifest_paths = {entry["path"] for entry in manifest.get("files", [])}

    missing_release = []
    missing_base = []
    stable_status_surfaces = []
    for surface in SURFACES:
        text = read(surface)
        if EXPECTED_RELEASE not in text:
            missing_release.append(surface)
        if surface in {"README.md", "VERSION.md", "RELEASE_NOTES.md", "RELEASE_STATUS.md", "RELEASE_METADATA.json", "docs/RELEASE_v0.16.7_STABLE.md"} and EXPECTED_BASE not in text:
            missing_base.append(surface)
        lowered = text.lower()
        if ('"status": "stable"' not in lowered and 'status: stable' not in lowered and 'status = "stable"' not in lowered and '# status: stable' not in lowered):
            stable_status_surfaces.append(surface)

    forbidden = transition.get("forbidden_transitions", [])
    allowed = transition.get("allowed_transitions", [])

    checks = [
        check("metadata_stable_state", metadata.get("release") == EXPECTED_RELEASE and metadata.get("base") == EXPECTED_BASE and metadata.get("status") == EXPECTED_STATUS, {"release": metadata.get("release"), "base": metadata.get("base"), "status": metadata.get("status")}),
        check("manifest_stable_state", manifest.get("release") == EXPECTED_RELEASE and manifest.get("base") == EXPECTED_BASE and manifest.get("status") == EXPECTED_STATUS, {"release": manifest.get("release"), "base": manifest.get("base"), "status": manifest.get("status")}),
        check("registry_stable_state", registry.get("release") == EXPECTED_RELEASE and registry.get("base") == EXPECTED_BASE and registry.get("status") == EXPECTED_STATUS, registry),
        check("stable_surfaces_have_release", not missing_release, {"missing": missing_release}),
        check("stable_surfaces_have_base", not missing_base, {"missing": missing_base}),
        check("stable_status_explicit", bool(stable_status_surfaces), {"surfaces": stable_status_surfaces}),
        check("manual_ci_gate_declared", any(t.get("from") == "stable" and t.get("to") == "stable" and t.get("ci_required") is True and t.get("manual_gate_required") is True for t in allowed), {"allowed": allowed}),
        check("stable_without_candidate_ci_forbidden", any(t.get("from") == "stable" and t.get("to") == "stable_without_candidate_ci" for t in forbidden), {"forbidden": forbidden}),
        check("no_runtime_authority", registry.get("runtime_authority") is False and registry.get("auto_repair") is False and registry.get("auto_promotion") is False, registry),
        check("registry_doc_manifested", "docs/RELEASE_GATE_ROBUSTNESS.md" in manifest_paths and "registry/release_gate_robustness.json" in manifest_paths and "tests/release_gate_robustness_evidence.py" in manifest_paths, {}),
    ]
    failed = [c["name"] for c in checks if not c["ok"]]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
