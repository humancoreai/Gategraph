from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import copy
from src import semantic_object_registry as registry


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    mark = "✓" if ok else "✗"
    print(f"{mark} {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    report = registry.registry_consistency_report()
    checks.append(check("canonical_registry_complete", report["ok"], report))

    for object_type in registry.CANONICAL_OBJECT_TYPES:
        decision = registry.classify_semantic_object({"object_type": object_type})
        checks.append(check(
            f"{object_type}_descriptive_only",
            decision.decision == "continue" and decision.reason == "SEM_OBJECT_DESCRIPTIVE_ONLY" and bool(decision.surfaces),
            decision.__dict__,
        ))
        blocked = registry.assert_no_semantic_promotion({"object_type": object_type}, "runtime_authority")
        checks.append(check(
            f"{object_type}_promotion_blocked",
            blocked.decision == "stop" and blocked.reason == "SEMANTIC_PROMOTION_BLOCKED",
            blocked.__dict__,
        ))

    unknown = registry.classify_semantic_object({"object_type": "authority_object"})
    checks.append(check("unknown_semantic_object_blocked", unknown.decision == "stop", unknown.__dict__))

    mutated = copy.deepcopy(registry.load_semantic_registry())
    mutated["object_types"]["proposal_object"]["policy_mutation"] = True
    mutated_report = registry.registry_consistency_report(registry=mutated)
    checks.append(check("authority_flag_violation_detected", not mutated_report["ok"] and mutated_report["authority_violations"], mutated_report))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
