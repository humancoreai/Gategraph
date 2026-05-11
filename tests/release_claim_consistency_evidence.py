from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.14.2_CANDIDATE"
EXPECTED_BASE = "v0.14.1_STABLE"
EXPECTED_STATUS = "candidate"
EXPECTED_PHASE = "Install / Packaging / Public Repo Hygiene"
SURFACES = [
    "README.md",
    "VERSION.md",
    "RELEASE_NOTES.md",
    "RELEASE_STATUS.md",
    "CHANGELOG.md",
    "docs/RELEASE_v0.14.2_CANDIDATE.md",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    meta = json.loads(read("RELEASE_METADATA.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    checks = []
    checks.append(check("metadata_claims_current_stable", meta.get("release") == EXPECTED_RELEASE and meta.get("base") == EXPECTED_BASE and meta.get("status") == EXPECTED_STATUS, {"release": meta.get("release"), "base": meta.get("base"), "status": meta.get("status")}))
    checks.append(check("metadata_declares_claim_consistency_scope", meta.get("release_claim_consistency_scope") is True, {"scope": meta.get("release_claim_consistency_scope")}))
    checks.append(check("manifest_claims_current_stable", manifest.get("release") == EXPECTED_RELEASE and manifest.get("base") == EXPECTED_BASE and manifest.get("status") == EXPECTED_STATUS, {"release": manifest.get("release"), "base": manifest.get("base"), "status": manifest.get("status")}))

    missing = []
    for surface in SURFACES:
        text = read(surface)
        if EXPECTED_RELEASE not in text or EXPECTED_BASE not in text or EXPECTED_PHASE not in text:
            missing.append(surface)
    checks.append(check("release_claims_present_on_surfaces", not missing, {"missing": missing}))

    forbidden_runtime_claims = []
    for surface in SURFACES:
        text = read(surface).lower()
        for phrase in ["runtime logic changed: true", "governance logic changed: true", "auto-promotion enabled", "automatic repair enabled"]:
            if phrase in text:
                forbidden_runtime_claims.append({"surface": surface, "phrase": phrase})
    checks.append(check("no_authority_expansion_claims", not forbidden_runtime_claims, {"violations": forbidden_runtime_claims}))

    manifest_paths = {entry["path"] for entry in manifest.get("files", [])}
    checks.append(check("release_doc_manifested", "docs/RELEASE_v0.14.2_CANDIDATE.md" in manifest_paths, {"present": "docs/RELEASE_v0.14.2_CANDIDATE.md" in manifest_paths}))
    checks.append(check("evidence_manifested", "tests/release_claim_consistency_evidence.py" in manifest_paths, {"present": "tests/release_claim_consistency_evidence.py" in manifest_paths}))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
