"""
WHY: Evidence classification reduces drift by making gate criticality explicit.
INV: This registry is descriptive only; it cannot disable, auto-prune, or change runtime authority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "evidence_registry.json"

REQUIRED_CLASSES = {"P0", "P1", "P2"}


def check(name: str, ok: bool, detail=None):
    mark = "✓" if ok else "✗"
    print(f"{mark} {name}: {detail or {}}")
    assert ok, detail or name


def main() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    classes = {entry.get("class") for entry in entries}
    tests = [entry.get("test") for entry in entries]
    paths = [entry.get("path") for entry in entries]

    check("registry_release_current", data.get("release") == "v0.15.6_CANDIDATE", {"release": data.get("release")})
    check("registry_base_previous_stable", data.get("base") == "v0.15.5_STABLE", {"base": data.get("base")})
    check("registry_descriptive_only", data.get("registry_mode") == "descriptive_classification_only", {"mode": data.get("registry_mode")})
    check("no_runtime_authority", data.get("runtime_authority") is False and data.get("auto_pruning") is False and data.get("auto_repair") is False, data)
    check("classes_present", REQUIRED_CLASSES.issubset(classes), {"classes": sorted(classes)})
    check("entries_unique", len(tests) == len(set(tests)), {"entries": len(tests), "unique": len(set(tests))})
    missing = [path for path in paths if path and not (ROOT / path).exists()]
    check("entry_paths_resolve", not missing, {"missing": missing})
    p0 = [entry for entry in entries if entry.get("class") == "P0"]
    p2_mutable = [entry for entry in entries if entry.get("class") == "P2" and entry.get("mutable_surface") is True]
    check("p0_core_entries_present", len(p0) >= 10, {"p0_count": len(p0)})
    check("p2_mutable_surface_entries_present", len(p2_mutable) >= 3, {"p2_mutable_count": len(p2_mutable)})
    bad = [entry for entry in entries if entry.get("class") == "P2" and entry.get("criticality") == "critical"]
    check("public_surface_not_critical", not bad, {"bad": bad})
    print("EVIDENCE REGISTRY REPORT")
    print({"passed": 10, "failed": 0, "entries": len(entries)})


if __name__ == "__main__":
    main()
