"""
WHY: Prove the v0.8.40 operator layer is useful while remaining strictly read-only.
INV: Evidence creates fixture data only in an isolated test DB, then opens operator access via mode=ro.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.operator_control import (  # noqa: E402
    TraceQuery,
    drilldown_stop_reason,
    explain_compact,
    inspect_decision,
    query_traces,
)


def _make_fixture_db(path: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript("""
        CREATE TABLE runtime_budgets (
            budget_id TEXT,
            task_id TEXT,
            max_steps INTEGER,
            max_runtime_seconds INTEGER,
            max_cost_units INTEGER,
            repeated_action_limit INTEGER,
            created_at TEXT
        );
        CREATE TABLE runtime_steps (
            step_id TEXT,
            task_id TEXT,
            step_index INTEGER,
            actor_id TEXT,
            action_type TEXT,
            action_signature TEXT,
            cost_units INTEGER,
            timestamp TEXT
        );
        CREATE TABLE runtime_decisions (
            decision_id TEXT,
            task_id TEXT,
            step_id TEXT,
            decision TEXT,
            reason TEXT,
            created_at TEXT
        );
        """)
        conn.execute("INSERT INTO runtime_budgets VALUES (?, ?, ?, ?, ?, ?, ?)", ("b1", "task-cost", 10, 60, 5, 3, "2026-05-02T10:00:00Z"))
        conn.execute("INSERT INTO runtime_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("s1", "task-cost", 1, "agent", "tool", "agent:tool:x", 3, "2026-05-02T10:00:01Z"))
        conn.execute("INSERT INTO runtime_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("s2", "task-cost", 2, "agent", "tool", "agent:tool:y", 4, "2026-05-02T10:00:02Z"))
        conn.execute("INSERT INTO runtime_decisions VALUES (?, ?, ?, ?, ?, ?)", ("d1", "task-cost", "s1", "continue", "ok", "2026-05-02T10:00:01Z"))
        conn.execute("INSERT INTO runtime_decisions VALUES (?, ?, ?, ?, ?, ?)", ("d2", "task-cost", "s2", "stop", "projected_cost_violation", "2026-05-02T10:00:02Z"))
        conn.execute("INSERT INTO runtime_budgets VALUES (?, ?, ?, ?, ?, ?, ?)", ("b2", "task-loop", 10, 60, 100, 1, "2026-05-02T11:00:00Z"))
        conn.execute("INSERT INTO runtime_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("s3", "task-loop", 1, "agent", "delegate", "agent:delegate:agent", 1, "2026-05-02T11:00:01Z"))
        conn.execute("INSERT INTO runtime_decisions VALUES (?, ?, ?, ?, ?, ?)", ("d3", "task-loop", "s3", "stop", "loop_detected", "2026-05-02T11:00:01Z"))
        conn.commit()
    finally:
        conn.close()


def _readonly_conn(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> int:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "operator_fixture.db")
        _make_fixture_db(db_path)
        # WHY: sqlite3.Connection as a context manager does not close the handle.
        # EDGE: Windows keeps the DB file locked until conn.close(), so TemporaryDirectory cleanup can fail.
        conn = _readonly_conn(db_path)
        try:
            inspected = inspect_decision(conn, "task-cost")
            checks.append(("inspect_has_trace_snapshot_timeline", all(k in inspected for k in ("decision_trace", "explain_snapshot", "cost_timeline"))))

            compact = explain_compact(conn, "task-cost")
            checks.append(("compact_explain_is_deterministic_subset", set(compact.keys()) == {"task_id", "final_decision", "triggering_guard", "normalized_reason", "key_metrics"}))
            checks.append(("compact_explain_keeps_final_decision", compact["final_decision"] == "stop"))
            checks.append(("compact_explain_keeps_guard", compact["triggering_guard"] == "runtime_cost_guard"))

            stops = query_traces(conn, TraceQuery(decision="stop"))
            checks.append(("query_stop_returns_only_stops", len(stops) == 2 and all(x["final_decision"] == "stop" for x in stops)))

            cost_stops = query_traces(conn, TraceQuery(decision="stop", guard="runtime_cost_guard"))
            checks.append(("query_guard_filters_runtime_cost", len(cost_stops) == 2 and all(x["triggering_guard"] == "runtime_cost_guard" for x in cost_stops)))

            code = compact["normalized_reason"].get("code")
            drilldown = drilldown_stop_reason(conn, code)
            checks.append(("drilldown_resolves_concrete_case", any(x["task_id"] == "task-cost" for x in drilldown)))

            try:
                conn.execute("INSERT INTO runtime_decisions VALUES ('x','x',NULL,'stop','x','x')")
                read_only_blocked = False
            except sqlite3.OperationalError:
                read_only_blocked = True
            checks.append(("sqlite_readonly_boundary_blocks_write", read_only_blocked))
        finally:
            conn.close()

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("✓" if ok else "✗"), name)
    summary = {"passed": len(checks) - len(failed), "failed": len(failed)}
    print(f"Summary: {summary}")
    if failed:
        print("FAIL operator_evidence", failed)
        return 1
    print("PASS operator_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
