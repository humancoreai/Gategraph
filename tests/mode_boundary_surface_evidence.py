#!/usr/bin/env python3
"""
WHY: Mode labels must not become implicit authority or runtime expansion.
INV: This evidence is detection-only; it does not create or execute runtime modes.
SEC: Mode claims that imply privilege, budget, secret, adapter, or governance bypass fail closed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.16.5_CANDIDATE"
EXPECTED_BASE = "v0.16.4_STABLE"
ALLOWED_MODE_LABELS = {"observer", "worker", "reviewer", "blocked"}
FORBIDDEN_CLAIMS = [
    "autonomous policy changes",
    "hidden execution rights",
    "self-selected privilege escalation",
    "budget expansion",
    "unreviewed tool access",
    "governance bypass",
    "direct secret access",
    "adapter-side governance decisions",
    "distributed or multi-node orchestration",
]
REQUIRED_FILES = {
    "docs/MULTI_MODE_SSOT.md",
    "docs/MODE_BOUNDARY_SURFACE.md",
    "docs/RUNTIME_SURFACE_FREEZE.md",
    "docs/OPERATIONAL_BOUNDARY_TIGHTENING.md",
    "RELEASE_METADATA.json",
    "tests/mode_boundary_surface_evidence.py",
}


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest["files"]}

    assert metadata["release"] == EXPECTED_RELEASE
    assert metadata["base"] == EXPECTED_BASE
    assert metadata["status"] == "candidate"
    assert metadata["mode_boundary_surface_scope"] is True
    for key in ["governance_logic_changed", "runtime_logic_changed", "enforcement_logic_changed", "new_runtime_capability", "new_agentic_behavior", "new_adapter", "distributed_governance"]:
        assert metadata[key] is False, key

    assert manifest["release"] == EXPECTED_RELEASE
    assert manifest["base"] == EXPECTED_BASE
    assert manifest["status"] == metadata["status"]
    assert not (REQUIRED_FILES - paths), sorted(REQUIRED_FILES - paths)

    ssot = (ROOT / "docs" / "MULTI_MODE_SSOT.md").read_text(encoding="utf-8")
    boundary = (ROOT / "docs" / "MODE_BOUNDARY_SURFACE.md").read_text(encoding="utf-8")
    runtime = (ROOT / "docs" / "RUNTIME_SURFACE_FREEZE.md").read_text(encoding="utf-8")

    for label in ALLOWED_MODE_LABELS:
        assert label in ssot, label
        assert label in boundary, label
    for phrase in FORBIDDEN_CLAIMS:
        assert phrase in boundary, phrase
    assert "alternative runtime modes beyond the existing local/single-node surfaces" in runtime
    assert "descriptive only" in boundary

    print(json.dumps({"mode_boundary_surface": {"release": EXPECTED_RELEASE, "base": EXPECTED_BASE, "allowed_mode_labels": sorted(ALLOWED_MODE_LABELS), "authority_expansion": False, "detection_only": True}}, indent=2, sort_keys=True))
    print("PASS mode_boundary_surface_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
