"""
WHY: Reviewers need a local, deterministic way to verify a release ZIP.
INV: Verification is read-only and never repairs packages silently.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

VERSION = "v0.9.0_CANDIDATE"
EXPECTED_PREFIX = f"GateGraph_{VERSION}/"
FIXED_ZIP_DT = (2026, 1, 1, 0, 0, 0)
FORBIDDEN_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".db", ".csv", ".zip"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path, "r") as zf:
        infos = zf.infolist()
        names = [i.filename for i in infos]
        errors: list[str] = []
        if names != sorted(names):
            errors.append("zip entries are not lexicographically sorted")
        if any(not name.startswith(EXPECTED_PREFIX) for name in names):
            errors.append("zip contains entries outside expected release root")
        for info in infos:
            rel = info.filename.removeprefix(EXPECTED_PREFIX)
            parts = Path(rel).parts
            if any(part.startswith(".") for part in parts) and rel != ".gitignore":
                errors.append(f"hidden entry found: {info.filename}")
            if set(parts) & FORBIDDEN_PARTS:
                errors.append(f"forbidden path part found: {info.filename}")
            if Path(rel).suffix.lower() in FORBIDDEN_SUFFIXES:
                errors.append(f"forbidden suffix found: {info.filename}")
            if info.date_time != FIXED_ZIP_DT:
                errors.append(f"non-deterministic timestamp: {info.filename}")
        required = [
            f"{EXPECTED_PREFIX}VERSION.md",
            f"{EXPECTED_PREFIX}RELEASE_METADATA.json",
            f"{EXPECTED_PREFIX}RELEASE_MANIFEST.json",
            f"{EXPECTED_PREFIX}EXTERNAL_REVIEW.md",
            f"{EXPECTED_PREFIX}INVARIANTS.md",
            f"{EXPECTED_PREFIX}NON_SCOPE.md",
            f"{EXPECTED_PREFIX}tools/build_release.py",
            f"{EXPECTED_PREFIX}tools/verify_release.py",
            f"{EXPECTED_PREFIX}tests/milestone_release_evidence.py",
        ]
        missing = [name for name in required if name not in names]
        if missing:
            errors.append(f"missing required entries: {missing}")
        manifest_name = f"{EXPECTED_PREFIX}RELEASE_MANIFEST.json"
        if manifest_name in names:
            manifest = json.loads(zf.read(manifest_name).decode("utf-8"))
            if manifest.get("release") != VERSION:
                errors.append("manifest release mismatch")
            manifest_paths = [entry["path"] for entry in manifest.get("files", [])]
            for entry in manifest.get("files", []):
                full = f"{EXPECTED_PREFIX}{entry['path']}"
                if full in names:
                    digest = sha256_bytes(zf.read(full))
                    if digest != entry.get("sha256"):
                        errors.append(f"hash mismatch: {entry['path']}")
            missing_manifest_paths = [p for p in manifest_paths if f"{EXPECTED_PREFIX}{p}" not in names]
            if missing_manifest_paths:
                errors.append(f"manifest paths missing in zip: {missing_manifest_paths}")
        return {"passed": not errors, "errors": errors, "entry_count": len(names)}


def main(argv: list[str]) -> int:
    zip_path = Path(argv[1]) if len(argv) > 1 else Path("dist") / f"GateGraph_{VERSION}.zip"
    result = verify(zip_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
