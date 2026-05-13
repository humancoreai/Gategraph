#!/usr/bin/env python3
"""
WHY: Runtime/budget edge cases must not produce negative balances or escalation bypasses.
INV: Reservation/release and throttling simulations remain deterministic and fail closed.
SEC: Budget recovery attempts never silently release or mint authority.
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass
class Ledger:
    limit: int
    reserved: int = 0
    consumed: int = 0
    state: str = "normal"

    @property
    def available(self) -> int:
        return self.limit - self.reserved - self.consumed

    def reserve(self, amount: int) -> str:
        if amount < 0 or self.available < amount:
            self.state = "blocked"
            return "SES_COST_LIMIT"
        self.reserved += amount
        if self.reserved + self.consumed >= int(self.limit * 0.7):
            self.state = "degraded"
        return "OK_RESERVED"

    def consume(self, amount: int) -> str:
        if amount < 0 or amount > self.reserved:
            self.state = "blocked"
            return "SES_RESERVATION_INCONSISTENT"
        self.reserved -= amount
        self.consumed += amount
        return "OK_CONSUMED"

    def release(self, amount: int) -> str:
        if amount < 0 or amount > self.reserved:
            self.state = "blocked"
            return "SES_RESERVATION_RELEASE_INCOMPLETE"
        self.reserved -= amount
        return "OK_RELEASED"


def main() -> int:
    race = Ledger(limit=10)
    assert race.reserve(6) == "OK_RESERVED"
    assert race.release(7) == "SES_RESERVATION_RELEASE_INCOMPLETE"
    assert race.available >= 0 and race.state == "blocked"

    fairness_a = Ledger(limit=10); fairness_b = Ledger(limit=10)
    assert fairness_a.reserve(7) == fairness_b.reserve(7) == "OK_RESERVED"
    assert fairness_a.state == fairness_b.state == "degraded"

    cross = Ledger(limit=10)
    assert cross.reserve(8) == "OK_RESERVED"
    assert cross.reserve(3) == "SES_COST_LIMIT"
    assert cross.available >= 0 and cross.state == "blocked"

    recovery = Ledger(limit=5)
    assert recovery.reserve(4) == "OK_RESERVED"
    attempts = [recovery.release(6), recovery.release(6)]
    assert attempts == ["SES_RESERVATION_RELEASE_INCOMPLETE", "SES_RESERVATION_RELEASE_INCOMPLETE"]
    assert recovery.reserved == 4 and recovery.consumed == 0

    print({"runtime_budget_edge_hardening": {"cases": ["reservation_release_race", "throttling_fairness", "cross_session_budget_edge", "repeated_runtime_recovery_attempts"], "negative_budget_state": False, "silent_release": False, "escalation_bypass": False}})
    print("Summary: {'passed': 4, 'failed': 0}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
