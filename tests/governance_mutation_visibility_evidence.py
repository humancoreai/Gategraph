from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / "registry" / "governance_lineage.json"


def diff_lineage(before: dict, after: dict) -> dict:
    before_map = {item["release"]: item for item in before.get("lineage", [])}
    after_map = {item["release"]: item for item in after.get("lineage", [])}
    added = sorted(set(after_map) - set(before_map))
    removed = sorted(set(before_map) - set(after_map))
    changed = sorted(rel for rel in set(before_map) & set(after_map) if before_map[rel] != after_map[rel])
    return {"added": added, "removed": removed, "changed": changed, "mode": "descriptive_mutation_visibility_only", "auto_repair": False}


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    data = json.loads(LINEAGE.read_text(encoding="utf-8"))
    checks = []
    clean = diff_lineage(data, copy.deepcopy(data))
    checks.append(check("clean_lineage_has_no_mutation", clean == {"added": [], "removed": [], "changed": [], "mode": "descriptive_mutation_visibility_only", "auto_repair": False}, clean))
    added = copy.deepcopy(data)
    added["lineage"].append({"release": "vX", "adds": ["x"], "governance_logic_changed": False})
    added_report = diff_lineage(data, added)
    checks.append(check("added_lineage_visible", added_report["added"] == ["vX"], added_report))
    changed = copy.deepcopy(data)
    changed["lineage"][-1]["governance_logic_changed"] = True
    changed_report = diff_lineage(data, changed)
    checks.append(check("changed_lineage_visible", changed_report["changed"] == ["v0.17.2_CANDIDATE"], changed_report))
    checks.append(check("mutation_visibility_no_auto_repair", not added_report["auto_repair"] and not changed_report["auto_repair"], {"added_auto_repair": added_report["auto_repair"], "changed_auto_repair": changed_report["auto_repair"]}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
