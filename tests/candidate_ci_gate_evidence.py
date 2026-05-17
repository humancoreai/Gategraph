from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.16.2_CANDIDATE"
EXPECTED_BASE = "v0.16.1_STABLE"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "registry" / "release_state_transition_registry.json").read_text(encoding="utf-8"))
    checks = []
    checks.append(check("stable_release_state", metadata.get("release") == EXPECTED_RELEASE and metadata.get("status") == "candidate", {"release": metadata.get("release"), "status": metadata.get("status")}))
    checks.append(check("stable_base_is_previous_stable", metadata.get("base") == EXPECTED_BASE, {"base": metadata.get("base")}))
    checks.append(check("candidate_ci_gate_scope_declared", metadata.get("candidate_ci_gate_scope") is True, {"scope": metadata.get("candidate_ci_gate_scope")}))
    allowed = registry.get("allowed_transitions", [])
    checks.append(check("stable_promotion_requires_ci_and_manual_gate", any(t.get("from") == "stable" and t.get("to") == "stable" and t.get("ci_required") is True and t.get("manual_gate_required") is True for t in allowed), {"allowed_transitions": allowed}))
    checks.append(check("no_auto_promotion_or_repair", registry.get("auto_promotion") is False and registry.get("auto_repair") is False and metadata.get("release_state_auto_promotion") is False and metadata.get("release_state_auto_repair") is False, {"registry_auto_promotion": registry.get("auto_promotion"), "registry_auto_repair": registry.get("auto_repair"), "metadata_auto_promotion": metadata.get("release_state_auto_promotion"), "metadata_auto_repair": metadata.get("release_state_auto_repair")}))
    forbidden = registry.get("forbidden_transitions", [])
    checks.append(check("stable_without_candidate_ci_forbidden", any(t.get("to") == "stable_without_candidate_ci" for t in forbidden), {"forbidden_transitions": forbidden}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
