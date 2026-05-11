from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / "registry" / "governance_lineage.json"


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    data = json.loads(LINEAGE.read_text(encoding="utf-8"))
    checks = []
    checks.append(check("lineage_release_stable", data.get("release") == "v0.14.7_STABLE", {"release": data.get("release")}))
    checks.append(check("lineage_base_stable", data.get("base") == "v0.14.6_STABLE", {"base": data.get("base")}))
    flags = ["runtime_authority", "auto_mutation", "auto_repair", "dynamic_loading"]
    checks.append(check("lineage_authority_flags_false", all(data.get(f) is False for f in flags), {f: data.get(f) for f in flags}))
    releases = [item.get("release") for item in data.get("lineage", [])]
    expected_tail = ["v0.12.3_STABLE", "v0.12.4_STABLE", "v0.12.5_STABLE", "v0.12.6_STABLE", "v0.12.7_STABLE", "v0.14.4_STABLE", "v0.14.6_STABLE", "v0.14.7_STABLE"]
    checks.append(check("lineage_order_deterministic", releases == expected_tail, {"releases": releases}))
    logic_changes = [item.get("release") for item in data.get("lineage", []) if item.get("governance_logic_changed")]
    checks.append(check("lineage_no_governance_logic_change", not logic_changes, {"logic_changes": logic_changes}))
    h1 = canonical_hash(data)
    h2 = canonical_hash(json.loads(LINEAGE.read_text(encoding="utf-8")))
    checks.append(check("lineage_snapshot_hash_stable", h1 == h2, {"hash": h1}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
