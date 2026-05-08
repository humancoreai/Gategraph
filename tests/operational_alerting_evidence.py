"""
WHY: Operational alerting must surface incidents without creating a new control path.
INV: alerts are read-only signals; they never allow, block, acknowledge, or repair actions.
"""
from __future__ import annotations

import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import init_db, get_connection
from src import budget_ledger, operational_hardening


def fresh_conn() -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "tests" / "logs" / "operational_alerting_evidence.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    init_db(db_path)
    return get_connection(db_path)


def check(name: str, condition: bool, detail: dict) -> tuple[bool, str, dict]:
    status = "✓" if condition else "✗"
    print(f"{status} {name}: {detail}")
    return condition, name, detail


def main() -> int:
    checks: list[tuple[bool, str, dict]] = []
    conn = fresh_conn()
    budget_ledger.create_scope(conn, scope_id="actor:alert-test", scope_type="actor", allocated_units=5)
    # Deliberate drift fixture: operational layer must report it, not repair it.
    conn.execute(
        "UPDATE budget_scopes SET consumed_units = 8, state = 'normal', reason_code = 'TEST_DRIFT' WHERE scope_id = ?",
        ("actor:alert-test",),
    )

    incidents = operational_hardening.detect_operational_incidents(conn)
    alerts = operational_hardening.evaluate_open_operational_alerts(conn)
    scope = budget_ledger.get_scope(conn, "actor:alert-test")

    checks.append(check(
        "incidents_recorded_from_drift",
        len(incidents) >= 2 and any(i.reason_code == "OPERATIONAL_BUDGET_ANOMALY" for i in incidents),
        {"incidents": [asdict(i) for i in incidents]},
    ))
    checks.append(check(
        "alerts_created_for_open_incidents",
        len(alerts) >= 2 and all(a.alert_id.startswith("ALERT-INC-") for a in alerts),
        {"alerts": [asdict(a) for a in alerts]},
    ))
    checks.append(check(
        "critical_alerts_sort_before_high",
        alerts[0].severity == "critical",
        {"ordered_severities": [a.severity for a in alerts]},
    ))
    checks.append(check(
        "alerting_does_not_repair_or_mutate_scope",
        scope is not None and scope.consumed_units == 8 and scope.state == "normal",
        {"scope": asdict(scope) if scope else None},
    ))

    passed = sum(1 for ok, _, _ in checks if ok)
    failed = len(checks) - passed
    print("\nOPERATIONAL ALERTING EVIDENCE REPORT")
    print(f"Summary: {{'total': {len(checks)}, 'passed': {passed}, 'failed': {failed}, 'findings': 0}}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
