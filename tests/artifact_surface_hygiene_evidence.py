#!/usr/bin/env python3
"""
WHY: Release artifacts are now a governance surface; drift must fail before packaging.
INV: This evidence is read-only and validates deterministic manifest/hash/package hygiene only.
SEC: Generated files, cache files, stale ZIPs, and hash/manifest mismatches fail closed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.17.8_STABLE"
EXPECTED_BASE = "v0.17.7_STABLE"
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".db", ".csv", ".zip", ".tmp", ".temp", ".log"}


def check(name: str, ok: bool, detail: object) -> tuple[str, bool, object]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    entries = manifest.get("files", [])
    paths = [entry.get("path") for entry in entries]
    entry_by_path = {entry.get("path"): entry for entry in entries}

    actual_paths = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        parts = set(Path(rel).parts)
        if ".git" in parts or "dist" in parts or rel == "ARTIFACTS.sha256" or rel == "RELEASE_MANIFEST.json" or rel.startswith("tests/logs/"):
            continue
        if parts & FORBIDDEN_PARTS or Path(rel).suffix in FORBIDDEN_SUFFIXES:
            continue
        actual_paths.append(rel)
    actual_paths = sorted(actual_paths)

    duplicates = sorted({p for p in paths if paths.count(p) > 1})
    missing_hash = sorted(p for p, entry in entry_by_path.items() if not entry.get("sha256"))
    hash_mismatch = sorted(
        p for p, entry in entry_by_path.items()
        if (ROOT / p).exists() and entry.get("sha256") != sha256_file(ROOT / p)
    )
    forbidden = sorted(
        p for p in paths
        if (set(Path(p).parts) & FORBIDDEN_PARTS) or Path(p).suffix in FORBIDDEN_SUFFIXES
    )
    manifest_only = sorted(set(paths) - set(actual_paths))
    disk_only = sorted(set(actual_paths) - set(paths))

    checks = [
        check("artifact_release_current", manifest.get("release") == EXPECTED_RELEASE, {"release": manifest.get("release")}),
        check("artifact_base_previous_stable", manifest.get("base") == EXPECTED_BASE, {"base": manifest.get("base")}),
        check("artifact_paths_sorted", paths == sorted(paths), {"count": len(paths)}),
        check("artifact_no_duplicate_paths", not duplicates, duplicates),
        check("artifact_no_missing_hashes", not missing_hash, missing_hash[:10]),
        check("artifact_hashes_match_files", not hash_mismatch, hash_mismatch[:10]),
        check("artifact_file_count_matches", manifest.get("file_count") == len(entries), {"declared": manifest.get("file_count"), "actual": len(entries)}),
        check("artifact_no_forbidden_entries", not forbidden, forbidden[:10]),
        check("artifact_manifest_matches_disk", not manifest_only and not disk_only, {"manifest_only": manifest_only[:10], "disk_only": disk_only[:10]}),
    ]
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
