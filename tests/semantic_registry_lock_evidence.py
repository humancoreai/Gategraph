from __future__ import annotations

import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import semantic_registry_lock as lock


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    report = lock.validate_lock()
    checks.append(check("semantic_registry_lock_valid", report["ok"], report))

    payload = lock.load_lock()
    checks.append(check(
        "locked_paths_complete",
        sorted(report["locked_paths"]) == sorted(lock.LOCKED_REGISTRY_PATHS),
        {"locked_paths": report["locked_paths"]},
    ))

    mutated = copy.deepcopy(payload)
    mutated["registries"][0]["sha256"] = "0" * 64
    mutation_report = lock.validate_lock(lock=mutated)
    checks.append(check(
        "registry_hash_mutation_detected",
        not mutation_report["ok"] and any("hash mismatch" in e for e in mutation_report["errors"]),
        mutation_report,
    ))

    authority_mutated = copy.deepcopy(payload)
    authority_mutated["dynamic_loading"] = True
    authority_report = lock.validate_lock(lock=authority_mutated)
    checks.append(check(
        "lock_authority_flag_detected",
        not authority_report["ok"] and any("dynamic_loading" in e for e in authority_report["errors"]),
        authority_report,
    ))

    rebuilt = lock.build_lock_payload()
    checks.append(check(
        "lock_builder_reproducible",
        rebuilt["registries"] == payload["registries"],
        {"rebuilt": rebuilt["registries"], "locked": payload["registries"]},
    ))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
