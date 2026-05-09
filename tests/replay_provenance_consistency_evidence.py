from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / "registry" / "governance_lineage.json"
SCHEMA = ROOT / "registry" / "schema_governance_registry.json"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    lineage = json.loads(LINEAGE.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    replay = lineage.get("replay_provenance", {})
    checks = []
    checks.append(check("replay_state_matches_release", replay.get("governance_state_release") == lineage.get("release"), {"replay": replay.get("governance_state_release"), "release": lineage.get("release")}))
    checks.append(check("replay_registry_state_exists", (ROOT / replay.get("registry_state", "")).exists(), {"registry_state": replay.get("registry_state")}))
    checks.append(check("replay_schema_state_matches_schema_registry", replay.get("schema_state") == "registry/schema_governance_registry.json" and schema.get("release") == lineage.get("release"), {"schema_release": schema.get("release")}))
    checks.append(check("replay_freeze_state_exists", (ROOT / replay.get("freeze_state", "")).exists(), {"freeze_state": replay.get("freeze_state")}))
    checks.append(check("replay_descriptive_only", replay.get("replay_mode") == "descriptive_reconstruction_only", {"replay_mode": replay.get("replay_mode")}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
