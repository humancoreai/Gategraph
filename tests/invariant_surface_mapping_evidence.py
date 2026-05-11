from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "invariant_surface_registry.json"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks = []
    invariants = data.get("invariants", {})
    checks.append(check("registry_release_stable", data.get("release") == "v0.14.0_CANDIDATE", {"release": data.get("release")}))
    checks.append(check("invariants_present", bool(invariants), {"count": len(invariants)}))

    for invariant_id, spec in sorted(invariants.items()):
        evidence = spec.get("evidence", [])
        surfaces = spec.get("surfaces", [])
        checks.append(check(f"{invariant_id}_has_surfaces", isinstance(surfaces, list) and bool(surfaces), {"surfaces": surfaces}))
        checks.append(check(f"{invariant_id}_has_evidence", isinstance(evidence, list) and bool(evidence), {"evidence": evidence}))
        missing = [name for name in evidence if not (ROOT / "tests" / name).exists()]
        checks.append(check(f"{invariant_id}_evidence_files_exist", not missing, {"missing": missing}))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
