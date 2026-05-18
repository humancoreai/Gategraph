"""
INV: Release-state normalization is descriptive validation only; it never promotes or repairs releases.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "release": "v0.17.7_STABLE",
    "status": "stable",
    "base": "v0.17.6_STABLE",
    "future_stable": "v0.17.7_STABLE",
    "version": "0.17.7",
}
ALLOWED_STATUS = {"candidate", "stable"}

def load_json(rel_path: str) -> Any:
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def release_state_from_metadata() -> dict[str, Any]:
    meta = load_json("RELEASE_METADATA.json")
    return {k: meta.get(k) for k in EXPECTED}

def validate_release_state() -> dict[str, Any]:
    errors: list[str] = []
    meta_state = release_state_from_metadata()
    for key, expected in EXPECTED.items():
        if meta_state.get(key) != expected:
            errors.append(f"metadata {key} mismatch: {meta_state.get(key)!r} != {expected!r}")
    if meta_state.get("status") not in ALLOWED_STATUS:
        errors.append("status is not allowed")

    constants = load_json("registry/release_constant_registry.json")
    const = constants.get("constants", {})
    required = {"CURRENT_RELEASE": EXPECTED["release"], "CURRENT_STATUS": EXPECTED["status"], "CURRENT_BASE": EXPECTED["base"], "FUTURE_STABLE": EXPECTED["future_stable"]}
    for key, expected in required.items():
        if const.get(key) != expected:
            errors.append(f"constant {key} mismatch: {const.get(key)!r} != {expected!r}")

    schema_registry = load_json("registry/registry_schema_registry.json")
    for key, expected in EXPECTED.items():
        if schema_registry.get("release_truth", {}).get(key) != expected:
            errors.append(f"registry_schema release_truth {key} mismatch")

    return {"ok": not errors, "errors": errors, "state": meta_state, "expected": EXPECTED}
