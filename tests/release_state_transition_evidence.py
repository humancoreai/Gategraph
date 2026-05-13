from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.15.9_CANDIDATE"
EXPECTED_BASE = "v0.15.8_STABLE"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    registry = json.loads((ROOT / "registry" / "release_state_transition_registry.json").read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    checks = []
    checks.append(check("registry_release_stable", registry.get("release") == EXPECTED_RELEASE, {"release": registry.get("release")}))
    checks.append(check("registry_base_stable", registry.get("base") == EXPECTED_BASE, {"base": registry.get("base")}))
    checks.append(check("metadata_transition_scope", metadata.get("release_state_transition_scope") is True, {"scope": metadata.get("release_state_transition_scope")}))
    checks.append(check("no_runtime_authority", registry.get("runtime_authority") is False and metadata.get("release_state_runtime_authority") is False, {"registry": registry.get("runtime_authority"), "metadata": metadata.get("release_state_runtime_authority")}))
    checks.append(check("no_auto_promotion_or_repair", registry.get("auto_promotion") is False and registry.get("auto_repair") is False, {"auto_promotion": registry.get("auto_promotion"), "auto_repair": registry.get("auto_repair")}))
    allowed = registry.get("allowed_transitions", [])
    checks.append(check("candidate_to_stable_manual_gate", any(t.get("from") == "stable" and t.get("to") == "stable" and t.get("manual_gate_required") is True and t.get("ci_required") is True for t in allowed), {"allowed": allowed}))
    forbidden = registry.get("forbidden_transitions", [])
    checks.append(check("stable_to_candidate_forbidden", any(t.get("from") == "stable" and t.get("to") == "stable" for t in forbidden), {"forbidden": forbidden}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
