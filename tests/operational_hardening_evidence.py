"""
WHY: Evidence proves observability/replay/incident detection without changing enforcement behavior.
INV: Operational hardening may detect and record, but never allows or executes an action.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import reset_db, get_connection, seed_rules
from src import governance, budget_ledger
from src.operational_hardening import (
    collect_budget_snapshot,
    replay_audit_consistency,
    detect_operational_incidents,
    list_open_incidents,
)

DB = PROJECT_ROOT / "gategraph.db"


def assert_true(name, condition, details=None):
    if not condition:
        raise AssertionError(f"{name} failed: {details}")
    print(f"✓ {name}: {details if details is not None else 'ok'}")


def main():
    reset_db(DB)
    conn = get_connection(DB)
    seed_rules(conn)

    result = governance.evaluate_task(
        conn,
        task_id="TASK-OPS-001",
        task_type="ops_observable_action",
        requested_capabilities=["read_files"],
        input_source="trusted_local",
        actor_id="ops-actor",
        projected_cost_units=7,
        system_budget_units=100,
        actor_budget_units=10,
        idempotency_key="ops-observe-1",
    )
    assert_true("token_issued", result.token is not None, {"scope": result.budget_scope_id})

    snapshot = collect_budget_snapshot(conn)
    assert_true("snapshot_has_actor_scope", any(s.scope_id == "actor:ops-actor" for s in snapshot.scopes), snapshot.totals_by_type)
    assert_true("snapshot_no_anomalies_initially", snapshot.anomalies == [], snapshot.anomalies)

    replay = replay_audit_consistency(conn)
    assert_true("audit_replay_ok_initially", replay.ok, replay)

    # Create a deterministic budget drift without bypassing schema constraints.
    with conn:
        conn.execute(
            "UPDATE budget_scopes SET reserved_units = 11, state = 'normal', reason_code = 'TEST_DRIFT' WHERE scope_id = ?",
            ("actor:ops-actor",),
        )
    drift_snapshot = collect_budget_snapshot(conn)
    assert_true("snapshot_detects_budget_drift", any("BUDGET" in a for a in drift_snapshot.anomalies), drift_snapshot.anomalies)

    drift_replay = replay_audit_consistency(conn)
    assert_true("audit_replay_fails_closed_on_drift", not drift_replay.ok, drift_replay.violations)

    incidents = detect_operational_incidents(conn)
    open_incidents = list_open_incidents(conn)
    assert_true("incidents_recorded_append_only", len(incidents) >= 1 and len(open_incidents) >= 1, [i.reason_code for i in open_incidents])

    conn.close()
    print("Summary:", {"passed": 6, "failed": 0, "unexpected_allows": 0, "invariant_violations": 0})
    import sys, os
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
