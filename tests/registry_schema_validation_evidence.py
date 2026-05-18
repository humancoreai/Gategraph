from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "registry_schema_registry.json"
REQUIRED_FIELDS = {"schema_version": str, "release": str, "status": str, "base": str, "future_stable": str, "release_truth": dict}
ALLOWED_STATUS = {"candidate", "stable"}

def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    for field, typ in REQUIRED_FIELDS.items():
        if field not in payload:
            errors.append(f"missing field: {field}")
        elif not isinstance(payload[field], typ):
            errors.append(f"wrong type for {field}")
    if payload.get("status") not in ALLOWED_STATUS:
        errors.append("invalid status")
    truth = payload.get("release_truth", {})
    for key in ("release", "status", "base", "future_stable", "version"):
        if not isinstance(truth.get(key), str):
            errors.append(f"release_truth missing/wrong type: {key}")
    if payload.get("release") != truth.get("release") or payload.get("status") != truth.get("status"):
        errors.append("release truth parity mismatch")
    if payload.get("runtime_authority") or payload.get("auto_repair") or payload.get("dynamic_loading"):
        errors.append("forbidden authority flag enabled")
    return errors

def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks = []
    checks.append(("registry_schema_valid", not validate(payload), validate(payload)))
    mutated = copy.deepcopy(payload); mutated.pop("release", None)
    checks.append(("missing_required_field_detected", any("missing field: release" in e for e in validate(mutated)), validate(mutated)))
    mutated = copy.deepcopy(payload); mutated["status"] = "preview"
    checks.append(("invalid_status_detected", any("invalid status" in e for e in validate(mutated)), validate(mutated)))
    mutated = copy.deepcopy(payload); mutated["release_truth"]["release"] = "v0.17.6_CANDIDATE"
    checks.append(("candidate_stable_parity_mismatch_detected", any("parity" in e for e in validate(mutated)), validate(mutated)))
    failed=[name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        print(("✓" if ok else "✗") + f" {name}: {detail}")
    print("Summary:", {"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
