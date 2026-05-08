"""
WHY: Release packaging must be deterministic and externally verifiable.
INV: This tool packages source/review artifacts only; it does not alter governance behavior.
SEC: Hidden files, runtime databases, caches and generated local artifacts are excluded fail-closed.
"""
from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.9.0_CANDIDATE"
BASE = "v0.8.48_STABLE"
DIST = ROOT / "dist"
ZIP_NAME = f"GateGraph_{VERSION}.zip"
ZIP_PATH = DIST / ZIP_NAME
FIXED_ZIP_DT = (2026, 1, 1, 0, 0, 0)

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".db", ".csv", ".zip"}
EXCLUDED_NAMES = {
    "gategraph.db",
    "gategraph.db-journal",
    "gategraph.db-wal",
    "gategraph.db-shm",
    "ARTIFACTS.sha256",
}

@dataclass(frozen=True)
class ReleaseFile:
    path: str
    size: int
    sha256: str


def _is_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = set(rel.parts)
    if parts & EXCLUDED_DIRS:
        return False
    if _is_hidden_part(rel) and rel.as_posix() != ".gitignore":
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if rel.as_posix().startswith("tests/logs/") and path.name != ".gitkeep":
        return False
    return path.is_file()


def iter_release_files() -> list[Path]:
    return sorted((p for p in ROOT.rglob("*") if _include(p)), key=lambda p: p.relative_to(ROOT).as_posix())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(files: Iterable[Path]) -> dict:
    entries = [
        ReleaseFile(
            path=p.relative_to(ROOT).as_posix(),
            size=p.stat().st_size,
            sha256=sha256_file(p),
        ).__dict__
        for p in files
    ]
    return {
        "release": VERSION,
        "base": BASE,
        "kind": "milestone_release_candidate",
        "scope": "external_review_baseline",
        "deterministic_packaging": True,
        "file_count": len(entries),
        "files": entries,
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_zip(files: list[Path], zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(filename=f"GateGraph_{VERSION}/{rel}", date_time=FIXED_ZIP_DT)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Stable read-only regular file metadata for cross-platform review.
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            zf.writestr(info, path.read_bytes())


def main() -> None:
    DIST.mkdir(exist_ok=True)
    metadata = {
        "release": VERSION,
        "base": BASE,
        "phase": "Milestone Release / External Review Baseline",
        "governance_logic_changed": False,
        "new_governance_features": False,
        "scope_freeze": True,
        "claim_boundary": "deterministic governance/enforcement milestone with auditable evidence and reproducible release packaging",
    }
    write_json(ROOT / "RELEASE_METADATA.json", metadata)

    files_without_manifest = [p for p in iter_release_files() if p.name not in {"RELEASE_MANIFEST.json"}]
    manifest = build_manifest(files_without_manifest)
    write_json(ROOT / "RELEASE_MANIFEST.json", manifest)

    files = iter_release_files()
    source_hashes = [f"{sha256_file(p)}  {p.relative_to(ROOT).as_posix()}" for p in files]
    (ROOT / "ARTIFACTS.sha256").write_text("\n".join(source_hashes) + "\n", encoding="utf-8")

    files = iter_release_files()
    write_zip(files, ZIP_PATH)
    zip_sha = sha256_file(ZIP_PATH)
    (DIST / f"{ZIP_NAME}.sha256").write_text(f"{zip_sha}  {ZIP_NAME}\n", encoding="utf-8")
    print(json.dumps({"zip": str(ZIP_PATH), "sha256": zip_sha, "file_count": len(files)}, indent=2))


if __name__ == "__main__":
    main()
