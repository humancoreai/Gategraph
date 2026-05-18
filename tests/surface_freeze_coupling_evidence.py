#!/usr/bin/env python3
"""
WHY: Release claims, manifest, docs and Evidence CI must describe the same runtime surface.
INV: This test detects release drift only; it does not create new runtime capabilities.
SEC: Candidate/stable metadata leakage and undeclared surface files fail closed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.17.3_STABLE"
EXPECTED_BASE = "v0.17.2_STABLE"
REQUIRED_SURFACE = {
    "docs/STARTUP_SURFACE.md",
    "docs/RUNTIME_SURFACE_FREEZE.md",
    "docs/OPERATIONAL_BOUNDARY_TIGHTENING.md",
    "tests/startup_surface_evidence.py",
    "tests/startup_shutdown_semantics_evidence.py",
    "tests/config_consistency_evidence.py",
    "tests/runtime_surface_consistency_evidence.py",
    "tests/surface_freeze_coupling_evidence.py",
    "RELEASE_METADATA.json",
    "pyproject.toml",
}
REQUIRED_EVIDENCE_NAMES = {
    "startup_surface_evidence",
    "startup_shutdown_semantics_evidence",
    "config_consistency_evidence",
    "runtime_surface_consistency_evidence",
    "surface_freeze_coupling_evidence",
    "packaging_integrity_evidence",
    "release_process_guard_evidence",
}


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest["files"]}

    assert metadata["release"] == EXPECTED_RELEASE
    assert metadata["base"] == EXPECTED_BASE
    assert metadata["status"] in {"candidate", "stable"}
    assert manifest["release"] == EXPECTED_RELEASE
    assert manifest["base"] == EXPECTED_BASE
    assert manifest["status"] == metadata["status"]
    assert manifest["file_count"] == len(manifest["files"])
    assert (ROOT / "RELEASE_MANIFEST.json").exists()
    assert not (REQUIRED_SURFACE - paths), sorted(REQUIRED_SURFACE - paths)

    evidence_ci = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    missing_evidence = [name for name in sorted(REQUIRED_EVIDENCE_NAMES) if name not in evidence_ci]
    assert not missing_evidence, missing_evidence

    runtime_doc = (ROOT / "docs" / "RUNTIME_SURFACE_FREEZE.md").read_text(encoding="utf-8")
    startup_doc = (ROOT / "docs" / "STARTUP_SURFACE.md").read_text(encoding="utf-8")
    boundary_doc = (ROOT / "docs" / "OPERATIONAL_BOUNDARY_TIGHTENING.md").read_text(encoding="utf-8")
    for phrase in ["gategraph init", "gategraph evaluate", "gategraph status", "gategraph-server"]:
        assert phrase in runtime_doc, phrase
    for phrase in ["Canonical start paths", "gategraph --help"]:
        assert phrase in startup_doc, phrase
    for phrase in ["unsupported operational shortcuts", "Candidate metadata"]:
        assert phrase in boundary_doc, phrase

    forbidden = [p for p in paths if p.startswith("dist/") or p.startswith("tests/logs/") or p.endswith((".db", ".csv", ".pyc", ".pyo", ".log", ".tmp", ".zip"))]
    assert not forbidden, forbidden

    print(json.dumps({
        "surface_freeze_coupling": {
            "release": EXPECTED_RELEASE,
            "base": EXPECTED_BASE,
            "surface_files": len(REQUIRED_SURFACE),
            "evidence_names": sorted(REQUIRED_EVIDENCE_NAMES),
            "manifest_files": len(paths),
        }
    }, indent=2, sort_keys=True))
    print("PASS surface_freeze_coupling_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
