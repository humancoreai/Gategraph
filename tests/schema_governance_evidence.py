from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "schema_governance_registry.json"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks.append(check("registry_release_stable", data.get("release") == "v0.16.1_CANDIDATE", {"release": data.get("release")}))
    checks.append(check("registry_base_stable", data.get("base") == "v0.16.0_STABLE", {"base": data.get("base")}))
    forbidden_flags = ["dynamic_loading", "auto_migration", "auto_repair", "runtime_authority"]
    checks.append(check("authority_flags_false", all(data.get(flag) is False for flag in forbidden_flags), {flag: data.get(flag) for flag in forbidden_flags}))
    schemas = data.get("schemas", [])
    checks.append(check("schemas_declared", bool(schemas), {"count": len(schemas)}))
    unresolved = [s.get("path") for s in schemas if not (ROOT / str(s.get("path", ""))).exists()]
    checks.append(check("schema_paths_resolve", not unresolved, {"unresolved": unresolved}))
    non_descriptive = [s.get("schema_id") for s in schemas if s.get("authority") != "descriptive_only"]
    checks.append(check("schemas_descriptive_only", not non_descriptive, {"non_descriptive": non_descriptive}))
    exports = data.get("exports", [])
    bad_exports = [e.get("bundle_type") for e in exports if e.get("runtime_authority") or e.get("auto_import") or not e.get("deterministic_hash_required")]
    checks.append(check("export_contracts_non_authoritative", not bad_exports, {"bad_exports": bad_exports}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
