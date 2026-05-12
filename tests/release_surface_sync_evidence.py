import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.15.6_CANDIDATE"
EXPECTED_BASE = "v0.15.5_STABLE"
EXPECTED_STATUS = "candidate"
EXPECTED_VERSION = "0.15.6"
EXPECTED_PHASE = "CI parity and fresh-clone release-surface consolidation"
SURFACES = ['README.md', 'VERSION.md', 'RELEASE_NOTES.md', 'RELEASE_STATUS.md', 'RELEASE_METADATA.json', 'RELEASE_MANIFEST.json', 'pyproject.toml', 'tools/build_release.py', 'tools/verify_release.py', 'docs/RECOVERY_FOUNDATION.md', 'docs/RELEASE_v0.15.6_CANDIDATE.md']

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def fail(name, detail):
    raise AssertionError({"check": name, "detail": detail})

def main():
    meta = json.loads(read("RELEASE_METADATA.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))

    if meta.get("release") != EXPECTED_RELEASE:
        fail("metadata_release", meta.get("release"))
    if manifest.get("release") != EXPECTED_RELEASE:
        fail("manifest_release", manifest.get("release"))
    if meta.get("base") != EXPECTED_BASE:
        fail("metadata_base", meta.get("base"))
    if manifest.get("base") != EXPECTED_BASE:
        fail("manifest_base", manifest.get("base"))
    if meta.get("status") != EXPECTED_STATUS:
        fail("metadata_status", meta.get("status"))
    if meta.get("phase") != EXPECTED_PHASE:
        fail("metadata_phase", meta.get("phase"))

    pyproject_text = read("pyproject.toml")
    if f'version = "{EXPECTED_VERSION}"' not in pyproject_text:
        fail("pyproject_version", "missing expected version string")

    missing_release = []
    for rel in SURFACES:
        text = read(rel)
        if EXPECTED_RELEASE not in text:
            missing_release.append(rel)
    if missing_release:
        fail("surface_release_token", missing_release)

    base_missing = []
    for rel in ["README.md", "VERSION.md", "RELEASE_NOTES.md"]:
        if EXPECTED_BASE not in read(rel):
            base_missing.append(rel)
    if base_missing:
        fail("base_token", base_missing)

    stale_current = re.findall(
        r"Current release: \*\*v0\.12\.1_STABLE\*\*|Release: v0\.12\.1_STABLE|Current release: v0\.12\.1_STABLE",
        read("README.md") + read("VERSION.md") + read("RELEASE_STATUS.md"),
    )
    if stale_current:
        fail("stale_current_release", stale_current)

    print({"release": EXPECTED_RELEASE, "base": EXPECTED_BASE, "status": EXPECTED_STATUS, "phase": EXPECTED_PHASE, "surfaces": SURFACES})
    print("PASS release_surface_sync_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")

if __name__ == "__main__":
    main()
