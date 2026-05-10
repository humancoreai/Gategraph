"""
WHY: Semantic registries became release-critical in v0.12.3; v0.12.9 keeps their declared content with deterministic hashes.
INV: The lock is descriptive release evidence only; it never loads plugins, mutates policy, or grants runtime authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = PROJECT_ROOT / "registry" / "semantic_registry_lock.json"
LOCKED_REGISTRY_PATHS = (
    "registry/semantic_object_types.json",
    "registry/invariant_surface_registry.json",
)
FORBIDDEN_LOCK_FLAGS = (
    "authoritative",
    "executable",
    "runtime_access",
    "policy_mutation",
    "governance_influence",
    "semantic_promotion_allowed",
    "dynamic_loading",
    "auto_repair",
)


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_hash(path: Path) -> str:
    return hashlib.sha256(canonical_json_bytes(load_json(path))).hexdigest()


def build_lock_payload(*, root: Path | None = None, release: str = "v0.13.2_STABLE") -> dict[str, Any]:
    project_root = root or PROJECT_ROOT
    registries = []
    for rel_path in LOCKED_REGISTRY_PATHS:
        path = project_root / rel_path
        registries.append({"path": rel_path, "sha256": registry_hash(path)})
    return {
        "schema_version": "0.13.2",
        "release": release,
        "invariant": "semantic registry locks are release evidence only and never grant authority",
        "authoritative": False,
        "executable": False,
        "runtime_access": False,
        "policy_mutation": False,
        "governance_influence": False,
        "semantic_promotion_allowed": False,
        "dynamic_loading": False,
        "auto_repair": False,
        "registries": registries,
    }


def load_lock(path: Path | None = None) -> dict[str, Any]:
    return dict(load_json(path or LOCK_PATH))


def validate_lock(*, lock: dict[str, Any] | None = None, root: Path | None = None) -> dict[str, Any]:
    project_root = root or PROJECT_ROOT
    payload = lock or load_lock()
    entries = payload.get("registries", [])
    errors: list[str] = []

    for flag in FORBIDDEN_LOCK_FLAGS:
        if bool(payload.get(flag)):
            errors.append(f"lock flag must remain false: {flag}")

    if not isinstance(entries, list) or not entries:
        errors.append("lock registries must be a non-empty list")
        entries = []

    seen: set[str] = set()
    locked_paths = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("lock registry entry must be an object")
            continue
        rel_path = entry.get("path")
        declared_hash = entry.get("sha256")
        if not isinstance(rel_path, str) or rel_path not in LOCKED_REGISTRY_PATHS:
            errors.append(f"unexpected locked registry path: {rel_path!r}")
            continue
        if rel_path in seen:
            errors.append(f"duplicate locked registry path: {rel_path}")
            continue
        seen.add(rel_path)
        locked_paths.append(rel_path)
        current_hash = registry_hash(project_root / rel_path)
        if declared_hash != current_hash:
            errors.append(f"registry hash mismatch: {rel_path}")

    missing = sorted(set(LOCKED_REGISTRY_PATHS) - set(locked_paths))
    if missing:
        errors.append(f"missing locked registry paths: {missing}")

    return {"ok": not errors, "errors": errors, "locked_paths": sorted(locked_paths), "schema_version": payload.get("schema_version")}
