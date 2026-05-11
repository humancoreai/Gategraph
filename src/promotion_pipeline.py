"""
WHY: v0.14.6 makes release promotion drift visible before stable packaging.
INV: This module is descriptive evidence support only; it cannot promote, repair, or mutate governance policy.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CURRENT_RELEASE = "v0.14.6_CANDIDATE"
CURRENT_BASE = "v0.14.5_STABLE"
CURRENT_STATUS = "candidate"
REGISTRY_PATH = PROJECT_ROOT / "registry" / "promotion_pipeline_registry.json"

SURFACE_FILES = (
    "README.md",
    "VERSION.md",
    "RELEASE_NOTES.md",
    "RELEASE_STATUS.md",
    "RELEASE_METADATA.json",
    "pyproject.toml",
    "tools/build_release.py",
    "tools/verify_release.py",
    "docs/RELEASE_v0.14.6_CANDIDATE.md",
    "registry/promotion_pipeline_registry.json",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_entries(root: Path | None = None) -> dict[str, dict[str, Any]]:
    project_root = root or PROJECT_ROOT
    manifest = load_json(project_root / "RELEASE_MANIFEST.json")
    entries: dict[str, dict[str, Any]] = {}

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            rel = obj.get("path") or obj.get("relative_path")
            if isinstance(rel, str):
                entries[rel] = obj
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(manifest)
    return entries


def check_surface_tokens(root: Path | None = None) -> dict[str, Any]:
    project_root = root or PROJECT_ROOT
    missing_release: list[str] = []
    missing_base: list[str] = []
    missing_status: list[str] = []
    for rel in SURFACE_FILES:
        path = project_root / rel
        if not path.exists():
            missing_release.append(rel)
            continue
        text = path.read_text(encoding="utf-8")
        if CURRENT_RELEASE not in text:
            missing_release.append(rel)
        if rel != "RELEASE_MANIFEST.json" and CURRENT_BASE not in text:
            missing_base.append(rel)
        if rel in ("RELEASE_METADATA.json", "RELEASE_STATUS.md", "VERSION.md", "docs/RELEASE_v0.14.6_CANDIDATE.md", "registry/promotion_pipeline_registry.json"):
            if CURRENT_STATUS not in text:
                missing_status.append(rel)
    return {
        "ok": not missing_release and not missing_base and not missing_status,
        "missing_release": missing_release,
        "missing_base": missing_base,
        "missing_status": missing_status,
    }


def check_manifest_freshness(root: Path | None = None) -> dict[str, Any]:
    project_root = root or PROJECT_ROOT
    entries = manifest_entries(project_root)
    errors: list[str] = []
    for rel in SURFACE_FILES:
        path = project_root / rel
        entry = entries.get(rel)
        if not path.exists():
            errors.append(f"surface missing: {rel}")
            continue
        if entry is None:
            errors.append(f"manifest missing: {rel}")
            continue
        actual_sha = file_sha256(path)
        actual_size = path.stat().st_size
        declared_sha = entry.get("sha256") or entry.get("hash") or entry.get("sha")
        declared_size = entry.get("size") or entry.get("size_bytes") or entry.get("bytes")
        if declared_sha and declared_sha != actual_sha:
            errors.append(f"manifest sha mismatch: {rel}")
        if declared_size and int(declared_size) != actual_size:
            errors.append(f"manifest size mismatch: {rel}")
    return {"ok": not errors, "errors": errors}


def check_registry_lock_fresh(root: Path | None = None) -> dict[str, Any]:
    project_root = root or PROJECT_ROOT
    from src import semantic_registry_lock

    return semantic_registry_lock.validate_lock(root=project_root)


def promotion_pipeline_report(root: Path | None = None) -> dict[str, Any]:
    project_root = root or PROJECT_ROOT
    registry = load_json(project_root / "registry" / "promotion_pipeline_registry.json")
    surface = check_surface_tokens(project_root)
    manifest = check_manifest_freshness(project_root)
    lock = check_registry_lock_fresh(project_root)
    no_authority = not any(bool(registry.get(flag)) for flag in ("runtime_authority", "auto_promotion", "auto_repair", "policy_mutation"))
    ok = surface["ok"] and manifest["ok"] and lock["ok"] and no_authority
    return {
        "release": CURRENT_RELEASE,
        "base": CURRENT_BASE,
        "status": CURRENT_STATUS,
        "ok": ok,
        "surface": surface,
        "manifest": manifest,
        "registry_lock": lock,
        "no_authority": no_authority,
        "mode": registry.get("mode"),
    }
