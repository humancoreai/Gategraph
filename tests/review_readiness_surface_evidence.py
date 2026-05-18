import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.17.8_CANDIDATE"
BASE = "v0.17.7_STABLE"
STATUS = "candidate" if RELEASE.endswith("_CANDIDATE") else "stable"
REQUIRED_SURFACES = [
    "README.md", "VERSION.md", "RELEASE_STATUS.md", "RELEASE_METADATA.json", "RELEASE_MANIFEST.json", "RELEASE_NOTES.md",
    "docs/SCOPE_BACKLOG.md", "docs/RELEASE_v0.17.8_CANDIDATE.md", "SECURITY.md", "PRODUCTION.md", "TRUST_MODEL.md",
]

def main():
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict) and "path" in entry}
    assert metadata["release"] == RELEASE
    assert metadata["base"] == BASE
    assert metadata["status"] == STATUS
    assert metadata.get("review_readiness_scope") is True
    assert metadata.get("external_review_surface_scope") is True
    missing_files = [path for path in REQUIRED_SURFACES if not (ROOT / path).is_file()]
    assert not missing_files, missing_files
    missing_manifest = [path for path in REQUIRED_SURFACES if path not in paths and path != "RELEASE_MANIFEST.json"]
    assert not missing_manifest, missing_manifest
    for path in ["README.md", "VERSION.md", "RELEASE_STATUS.md", "docs/RELEASE_v0.17.8_CANDIDATE.md"]:
        text = (ROOT / path).read_text(encoding="utf-8")
        assert RELEASE in text, path
        assert BASE in text, path
    print({"release": RELEASE, "review_surfaces": len(REQUIRED_SURFACES)})
    print("PASS review_readiness_surface_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")

if __name__ == "__main__":
    main()
