"""
Release surface symmetry evidence for GateGraph v0.17.6_CANDIDATE.
Descriptive validation only. No governance mutation.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

SURFACES = [
    "README.md",
    "VERSION.md",
    "RELEASE_STATUS.md",
    "RELEASE_NOTES.md",
    "RELEASE_METADATA.json",
    "RELEASE_MANIFEST.json",
    "CONTEXT_GOVERNANCE_MODEL.md",
]

EXPECTED_RELEASE = "v0.17.6_CANDIDATE"

def classify(content: str):
    findings = []
    legacy = re.findall(r"v0\.14\.[0-6]_(?:STABLE|CANDIDATE)", content)
    if legacy:
        findings.append("LEGACY_REFERENCE")
    if EXPECTED_RELEASE not in content:
        findings.append("VERSION_DRIFT")
    return sorted(set(findings))

def main():
    failures = {}
    for surface in SURFACES:
        path = ROOT / surface
        if not path.exists():
            failures[surface] = ["SURFACE_MISSING"]
            continue

        findings = classify(path.read_text(encoding="utf-8"))
        if findings:
            failures[surface] = findings

    if failures:
        raise SystemExit(f"release surface drift detected: {failures}")

    print("release_surface_symmetry_evidence: PASS")

if __name__ == "__main__":
    main()
