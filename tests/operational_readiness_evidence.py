from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check(name: str, condition: bool, detail=None, results=None):
    results.append((name, condition, detail or {}))
    print(("✓" if condition else "✗"), name, detail or {})


def main() -> int:
    results = []
    meta = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    reg = json.loads((ROOT / "registry" / "operational_readiness_registry.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    doc = (ROOT / "docs" / "OPERATIONAL_READINESS.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8")) if (ROOT / "RELEASE_MANIFEST.json").exists() else {"files": []}
    paths = {entry.get("path") for entry in manifest.get("files", [])}

    check("metadata_current_release", meta.get("release") == "v0.17.2_STABLE" and meta.get("base") == "v0.17.1_STABLE" and meta.get("status") == "stable", {"release": meta.get("release"), "base": meta.get("base"), "status": meta.get("status")}, results)
    check("registry_current_release", reg.get("release") == meta.get("release") and reg.get("base") == meta.get("base") and reg.get("status") == meta.get("status"), {"registry": reg.get("release")}, results)
    check("descriptive_only_no_authority", not any([reg.get("runtime_authority"), reg.get("auto_repair"), reg.get("auto_promotion"), reg.get("policy_mutation")]), {"runtime_authority": reg.get("runtime_authority")}, results)
    check("no_performance_claims", reg.get("performance_claims") is False and reg.get("benchmark_claims") is False and "no hard throughput claim" in doc, {}, results)
    check("entry_points_declared", 'gategraph = "src.cli:main"' in pyproject and 'gategraph-server = "src.server:main"' in pyproject, {}, results)
    required = set(reg.get("required_surfaces", []))
    check("surfaces_manifested", required.issubset(paths), {"missing": sorted(required - paths)}, results)
    check("doc_states_non_scope", "no autonomous recovery" in doc and "no automatic governance mutation" in doc, {}, results)

    failed = [name for name, ok, _ in results if not ok]
    print("OPERATIONAL READINESS EVIDENCE REPORT")
    print({"passed": len(results) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
