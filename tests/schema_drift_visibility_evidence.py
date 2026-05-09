from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def diff_schema(a: dict, b: dict) -> dict:
    a_ids = {s["schema_id"] for s in a.get("schemas", [])}
    b_ids = {s["schema_id"] for s in b.get("schemas", [])}
    return {
        "added": sorted(b_ids - a_ids),
        "removed": sorted(a_ids - b_ids),
        "changed_flags": sorted(flag for flag in ("dynamic_loading", "auto_migration", "auto_repair", "runtime_authority") if a.get(flag) != b.get(flag)),
        "mode": "descriptive_schema_drift_visibility_only",
        "auto_repair": False,
    }


def main() -> int:
    checks = []
    base = json.loads((ROOT / "registry" / "schema_governance_registry.json").read_text(encoding="utf-8"))
    clean = diff_schema(base, copy.deepcopy(base))
    checks.append(check("clean_registry_has_no_schema_drift", not clean["added"] and not clean["removed"] and not clean["changed_flags"], clean))
    mutated = copy.deepcopy(base)
    mutated["schemas"].append({"schema_id": "unreviewed_schema", "path": "registry/unreviewed.json", "authority": "descriptive_only"})
    added = diff_schema(base, mutated)
    checks.append(check("added_schema_visible", added["added"] == ["unreviewed_schema"], added))
    mutated2 = copy.deepcopy(base)
    mutated2["runtime_authority"] = True
    flag = diff_schema(base, mutated2)
    checks.append(check("authority_flag_drift_visible", flag["changed_flags"] == ["runtime_authority"], flag))
    checks.append(check("schema_drift_no_auto_repair", added["auto_repair"] is False and flag["auto_repair"] is False, {"added_auto_repair": added["auto_repair"], "flag_auto_repair": flag["auto_repair"]}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
