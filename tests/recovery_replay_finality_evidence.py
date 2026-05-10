#!/usr/bin/env python3
"""
WHY: Recovery/replay finality must be observable before any operational repair path exists.
INV: Final recovery states remain final; replay/recovery objects stay reference-only and non-authoritative.
SEC: Ambiguous or conflicting finality fails closed instead of being repaired or promoted to runtime input.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.recovery_foundation import (  # noqa: E402
    recover_attempt_once,
    recover_interrupted_reservation,
    validate_reference_only_object,
    validate_reservation_recovery_collision,
)


def main() -> int:
    checks = []

    decision = recover_attempt_once({"REC-1"}, "REC-1")
    assert decision.decision == "continue"
    assert decision.reason == "RECOVERY_ATTEMPT_ALREADY_FINAL"
    assert decision.effect == "descriptive_only"
    checks.append(("duplicate_recovery_attempt_is_final_reference", decision.to_dict()))

    decision = recover_interrupted_reservation(
        {"reservation_id": "R-CONSUMED", "state": "consumed", "consumed": True, "released": False}
    )
    assert decision.decision == "continue"
    assert decision.reason == "RECOVERY_CONSUME_ALREADY_FINAL"
    assert decision.effect == "descriptive_only"
    checks.append(("consumed_reservation_is_final", decision.to_dict()))

    decision = recover_interrupted_reservation(
        {"reservation_id": "R-RELEASED", "state": "released", "consumed": False, "released": True}
    )
    assert decision.decision == "continue"
    assert decision.reason == "RECOVERY_RELEASE_ALREADY_FINAL"
    assert decision.effect == "descriptive_only"
    checks.append(("released_reservation_is_final", decision.to_dict()))

    decision = validate_reservation_recovery_collision(
        {"reservation_id": "R-CONFLICT", "state": "consumed", "consumed": True, "released": False},
        [
            {"event_id": "E-1", "sequence": 1, "reservation_id": "R-CONFLICT", "event_type": "reservation_consumed"},
            {"event_id": "E-2", "sequence": 2, "reservation_id": "R-CONFLICT", "event_type": "reservation_released"},
        ],
    )
    assert decision.decision == "stop"
    assert decision.reason == "RECOVERY_RESERVATION_AUDIT_FINALITY_CONFLICT"
    checks.append(("conflicting_audit_finality_fails_closed", decision.to_dict()))

    decision = validate_reference_only_object(
        {
            "context_type": "recovery_snapshot",
            "executable": False,
            "governance_influence": False,
            "rehydrate_runtime": False,
        }
    )
    assert decision.decision == "continue"
    assert decision.reason == "REPLAY_REFERENCE_ONLY_OBJECT_OK"
    assert decision.effect == "descriptive_only"
    checks.append(("recovery_snapshot_reference_only", decision.to_dict()))

    decision = validate_reference_only_object(
        {
            "context_type": "recovery_snapshot",
            "executable": False,
            "governance_influence": False,
            "rehydrate_runtime": True,
        }
    )
    assert decision.decision == "stop"
    assert decision.reason == "REPLAY_REFERENCE_RUNTIME_REHYDRATION_BLOCKED"
    checks.append(("recovery_snapshot_runtime_rehydration_blocked", decision.to_dict()))

    for name, payload in checks:
        print(f"✓ {name}: {payload}")
    print("\nRECOVERY REPLAY FINALITY EVIDENCE REPORT")
    print({"passed": len(checks), "failed": 0})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
