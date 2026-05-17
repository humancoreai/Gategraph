import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.16.1_CANDIDATE"
EXPECTED_BASE = "v0.16.0_STABLE"
EXPECTED_STATUS = "candidate"
EXPECTED_VERSION = "0.16.1"
EXPECTED_PHASE = "Evidence artifact hygiene and revocation negative-path hardening"
EXPECTED_FOCUS = "Evidence Artifact Hygiene / Revocation Negative Path Hardening"

SURFACES = [
    "README.md",
    "VERSION.md",
    "RELEASE_NOTES.md",
    "RELEASE_STATUS.md",
    "RELEASE_METADATA.json",
    "RELEASE_MANIFEST.json",
    "pyproject.toml",
    "tools/build_release.py",
    "tools/verify_release.py",
    "registry/promotion_pipeline_registry.json",
    "registry/semantic_registry_lock.json",
    "docs/RELEASE_v0.16.1_CANDIDATE.md",
    "tests/promotion_surface_matrix_evidence.py",
    "tests/promotion_status_ssot_evidence.py",
]

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def main():
    meta = json.loads(read("RELEASE_METADATA.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict) and "path" in entry}

    assert meta["release"] == EXPECTED_RELEASE
    assert meta["base"] == EXPECTED_BASE
    assert meta["status"] == EXPECTED_STATUS
    assert meta["version"] == EXPECTED_VERSION
    assert meta["phase"] == EXPECTED_PHASE
    assert meta["release_focus"] == EXPECTED_FOCUS
    assert meta.get("promotion_surface_matrix_scope") is True

    assert manifest["release"] == EXPECTED_RELEASE
    assert manifest["base"] == EXPECTED_BASE
    assert manifest["status"] == EXPECTED_STATUS

    missing_files = [rel for rel in SURFACES if not (ROOT / rel).is_file()]
    assert not missing_files, missing_files

    missing_manifest = [rel for rel in SURFACES if rel not in paths]
    allowed_manifest_self_omission = {"RELEASE_MANIFEST.json"}
    missing_manifest = [path for path in missing_manifest if path not in allowed_manifest_self_omission]
    assert not missing_manifest, missing_manifest

    missing_release = [rel for rel in SURFACES if EXPECTED_RELEASE not in read(rel)]
    assert not missing_release, missing_release

    required_status_surfaces = [
        "VERSION.md",
        "RELEASE_STATUS.md",
        "RELEASE_NOTES.md",
        "docs/RELEASE_v0.16.1_CANDIDATE.md",
        "registry/promotion_pipeline_registry.json",
    ]
    missing_status = [rel for rel in required_status_surfaces if EXPECTED_STATUS not in read(rel)]
    assert not missing_status, missing_status

    print({"release": EXPECTED_RELEASE, "base": EXPECTED_BASE, "status": EXPECTED_STATUS, "surfaces": len(SURFACES)})
    print("PASS promotion_surface_matrix_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")

if __name__ == "__main__":
    main()
