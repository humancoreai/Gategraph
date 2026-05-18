from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATHS = [ROOT / "registry" / "evidence_suite_profile.json", ROOT / "registry" / "evidence_runtime_profiles.json"]
EXPECTED_RELEASE = "v0.17.8_STABLE"

def validate_profile(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["profile root must be object"]
    if not isinstance(payload.get("release"), str):
        errors.append("release must be string")
    elif payload.get("release") != EXPECTED_RELEASE:
        errors.append("release token mismatch")
    if not isinstance(payload.get("status"), str):
        errors.append("status must be string")
    if isinstance(payload.get("profiles"), str):
        errors.append("profiles must not be string")
    if "profiles" in payload and not isinstance(payload.get("profiles"), (list, dict)):
        errors.append("profiles must be list or object")
    if isinstance(payload.get("evidence"), str):
        errors.append("evidence must not be string")
    return errors

def main() -> int:
    checks=[]
    for path in PROFILE_PATHS:
        payload=json.loads(path.read_text(encoding="utf-8"))
        checks.append((f"{path.name}_types_valid", not validate_profile(payload), validate_profile(payload)))
        mutated=copy.deepcopy(payload); mutated["release"]="v0.17.1_CANDIDATE"
        checks.append((f"{path.name}_wrong_release_detected", any("release token mismatch" in e for e in validate_profile(mutated)), validate_profile(mutated)))
        mutated=copy.deepcopy(payload); mutated["profiles"]="release"
        checks.append((f"{path.name}_string_vs_list_detected", any("profiles must not be string" in e for e in validate_profile(mutated)), validate_profile(mutated)))
    failed=[name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        print(("✓" if ok else "✗") + f" {name}: {detail}")
    print("Summary:", {"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0
if __name__ == "__main__":
    raise SystemExit(main())
