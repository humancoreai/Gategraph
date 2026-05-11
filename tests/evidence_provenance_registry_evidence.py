from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "evidence_provenance_registry.json"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks = []
    checks.append(check("provenance_release_stable", data.get("release") == "v0.14.7_STABLE", {"release": data.get("release")}))
    checks.append(check("provenance_base_stable", data.get("base") == "v0.14.6_STABLE", {"base": data.get("base")}))
    forbidden = ["dynamic_loading", "auto_repair", "runtime_authority", "policy_mutation"]
    checks.append(check("provenance_authority_flags_false", all(data.get(k) is False for k in forbidden), {k: data.get(k) for k in forbidden}))
    evidence = data.get("evidence", [])
    ids = [e.get("evidence_id") for e in evidence]
    checks.append(check("evidence_entries_declared", len(evidence) >= 5 and len(ids) == len(set(ids)), {"count": len(evidence)}))
    missing_paths = [e.get("path") for e in evidence if not (ROOT / str(e.get("path", ""))).exists()]
    checks.append(check("evidence_paths_resolve", not missing_paths, {"missing": missing_paths}))
    bad_authority = [e.get("evidence_id") for e in evidence if e.get("authority") != "descriptive_only" or not e.get("deterministic")]
    checks.append(check("evidence_descriptive_deterministic", not bad_authority, {"bad": bad_authority}))
    unresolved_deps = []
    for e in evidence:
        for dep in e.get("depends_on", []):
            if not (ROOT / dep).exists():
                unresolved_deps.append({"evidence_id": e.get("evidence_id"), "dep": dep})
    checks.append(check("evidence_dependencies_resolve", not unresolved_deps, {"unresolved": unresolved_deps}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
