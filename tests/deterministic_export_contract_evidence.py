from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    registry = json.loads((ROOT / "registry" / "schema_governance_registry.json").read_text(encoding="utf-8"))
    allowed = {"monitoring_export", "replay_bundle", "recovery_bundle", "incident_bundle"}
    exports = registry.get("exports", [])
    types = {entry.get("bundle_type") for entry in exports}
    checks.append(check("expected_export_contracts_declared", allowed <= types, {"declared": sorted(t for t in types if isinstance(t, str))}))
    bad = [e for e in exports if e.get("runtime_authority") or e.get("auto_import")]
    checks.append(check("exports_have_no_runtime_authority", not bad, {"bad_count": len(bad)}))
    sample = {"bundle_type": "replay_bundle", "records": [{"id": "A", "seq": 1}, {"id": "B", "seq": 2}], "authority": "reference_only"}
    h1 = canonical_hash(sample)
    h2 = canonical_hash({"authority": "reference_only", "records": [{"seq": 1, "id": "A"}, {"seq": 2, "id": "B"}], "bundle_type": "replay_bundle"})
    checks.append(check("canonical_export_hash_stable", h1 == h2, {"hash": h1}))
    mutated = dict(sample)
    mutated["authority"] = "runtime"
    checks.append(check("semantic_export_mutation_changes_hash", h1 != canonical_hash(mutated), {"original": h1, "mutated": canonical_hash(mutated)}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
