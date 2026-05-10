from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import copy
from src import semantic_object_registry as registry

DRIFT_FLAGS = ("authoritative", "executable", "runtime_access", "policy_mutation", "governance_influence", "semantic_promotion_allowed")


def detect_semantic_drift(candidate: dict) -> dict:
    report = registry.registry_consistency_report(registry=candidate)
    drift = []
    for violation in report["authority_violations"]:
        drift.append({"kind": "semantic_authority_drift", **violation})
    return {"ok": not drift and report["ok"], "drift": drift, "registry_ok": report["ok"]}


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    base = registry.load_semantic_registry()
    checks.append(check("clean_registry_has_no_drift", detect_semantic_drift(base)["ok"], detect_semantic_drift(base)))

    for flag in DRIFT_FLAGS:
        mutated = copy.deepcopy(base)
        mutated["object_types"]["replay_object"][flag] = True
        result = detect_semantic_drift(mutated)
        checks.append(check(f"{flag}_drift_detected", not result["ok"] and result["drift"], result))

    blocked = registry.assert_no_semantic_promotion({"object_type": "proposal_object"}, "policy_mutation")
    checks.append(check("proposal_to_authority_blocked", blocked.decision == "stop", blocked.__dict__))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
