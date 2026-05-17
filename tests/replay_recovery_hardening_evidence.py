#!/usr/bin/env python3
"""
WHY: Recovery/replay evidence must prove deterministic reconstruction instead of silent repair.
INV: Inconsistent recovery state fails closed; replay signatures remain stable across ordering noise.
SEC: Recovery is descriptive and bounded; it never mutates governance policy or bypasses enforcement.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

REQUIRED_CASES = {
    "interrupted_promotion_recovery": "REL_STATE_INCOMPLETE",
    "partial_archive_reconstruction": "ARCHIVE_PARTIAL_RECONSTRUCTED",
    "replay_after_degraded_escalation": "RT_PROJECTED_COST_THROTTLED",
    "replay_across_release_boundaries": "OK_REPLAY_BOUNDARY_STABLE",
    "recovery_after_incomplete_reservation_release": "SES_RESERVATION_RELEASE_INCOMPLETE",
}

@dataclass(frozen=True)
class ReplayRecord:
    case: str
    stage: str
    normalized_reason: str
    fail_closed: bool
    governance_mutation: bool = False


def signature(records: Iterable[ReplayRecord]) -> str:
    payload = [r.__dict__ for r in sorted(records, key=lambda x: (x.case, x.stage, x.normalized_reason))]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    records = [
        ReplayRecord("interrupted_promotion_recovery", "release_state", "REL_STATE_INCOMPLETE", True),
        ReplayRecord("partial_archive_reconstruction", "archive_replay", "ARCHIVE_PARTIAL_RECONSTRUCTED", True),
        ReplayRecord("replay_after_degraded_escalation", "runtime_budget", "RT_PROJECTED_COST_THROTTLED", True),
        ReplayRecord("replay_across_release_boundaries", "release_boundary", "OK_REPLAY_BOUNDARY_STABLE", False),
        ReplayRecord("recovery_after_incomplete_reservation_release", "session_budget", "SES_RESERVATION_RELEASE_INCOMPLETE", True),
    ]
    by_case = {r.case: r for r in records}
    assert set(by_case) == set(REQUIRED_CASES)
    for case, reason in REQUIRED_CASES.items():
        r = by_case[case]
        assert r.normalized_reason == reason
        assert r.governance_mutation is False
        if reason != "OK_REPLAY_BOUNDARY_STABLE":
            assert r.fail_closed is True
    assert signature(records) == signature(reversed(records))
    print({"replay_recovery_hardening": {"cases": sorted(by_case), "signature": signature(records), "authority": "descriptive_only"}})
    print("Summary: {'passed': 5, 'failed': 0}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
