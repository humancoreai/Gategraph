"""
WHY: Operator Control exposes existing observability evidence for debugging without influencing execution.
INV: All helpers are read-only: no INSERT/UPDATE/DELETE, no guard evaluation, no policy tuning.
SEC: Query filters are exact-match only; no interpretation, ranking, or hidden prioritization.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable

from src.observability import build_cost_timeline, build_explain_snapshot, reconstruct_decision_trace


@dataclass(frozen=True)
class TraceQuery:
    decision: str | None = None
    guard: str | None = None
    normalized_reason_code: str | None = None
    since: str | None = None
    until: str | None = None


def _as_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _readonly_conn(db_path: str) -> sqlite3.Connection:
    # WHY: mode=ro lets SQLite enforce the read-only boundary at connection level.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def inspect_decision(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    """Return trace, explain snapshot, and cost timeline for one task_id."""
    return {
        "task_id": task_id,
        "decision_trace": reconstruct_decision_trace(conn, task_id),
        "explain_snapshot": build_explain_snapshot(conn, task_id),
        "cost_timeline": build_cost_timeline(conn, task_id),
    }


def explain_compact(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    """Compact deterministic answer to: why did this happen?"""
    snapshot = build_explain_snapshot(conn, task_id)
    return {
        "task_id": snapshot.get("task_id"),
        "final_decision": snapshot.get("final_decision"),
        "triggering_guard": snapshot.get("triggering_guard"),
        "normalized_reason": snapshot.get("normalized_reason"),
        "key_metrics": snapshot.get("metrics", {}),
    }


def query_traces(conn: sqlite3.Connection, query: TraceQuery) -> list[dict[str, Any]]:
    """Filter persisted runtime decisions by exact operator criteria."""
    sql = """
        SELECT DISTINCT task_id
        FROM runtime_decisions
        WHERE 1 = 1
    """
    params: list[Any] = []
    if query.decision:
        sql += " AND decision = ?"
        params.append(query.decision)
    if query.since:
        sql += " AND created_at >= ?"
        params.append(query.since)
    if query.until:
        sql += " AND created_at <= ?"
        params.append(query.until)
    sql += " ORDER BY task_id ASC"

    matches: list[dict[str, Any]] = []
    for row in conn.execute(sql, params).fetchall():
        task_id = row["task_id"]
        trace = reconstruct_decision_trace(conn, task_id)
        final = trace.get("final", {})
        normalized = final.get("normalized_reason") or {}
        if query.guard and final.get("triggering_guard") != query.guard:
            continue
        if query.normalized_reason_code and normalized.get("code") != query.normalized_reason_code:
            continue
        matches.append({
            "task_id": task_id,
            "final_decision": final.get("decision"),
            "triggering_guard": final.get("triggering_guard"),
            "normalized_reason_code": normalized.get("code"),
        })
    return matches


def drilldown_stop_reason(conn: sqlite3.Connection, reason_code: str) -> list[dict[str, Any]]:
    """Return concrete stop cases for one normalized stop reason code."""
    return query_traces(conn, TraceQuery(decision="stop", normalized_reason_code=reason_code))


def incident_related_decisions(incident: dict[str, Any]) -> list[str]:
    """Extract decision/task references already present on an incident object."""
    values: list[str] = []
    for key in ("task_id", "task_ids", "related_task_ids", "decision_task_ids"):
        raw = incident.get(key)
        if isinstance(raw, str):
            values.append(raw)
        elif isinstance(raw, list):
            values.extend(str(v) for v in raw if v is not None)
    return sorted(set(values))


def alert_root_cause_trace(conn: sqlite3.Connection, alert: dict[str, Any]) -> dict[str, Any]:
    """Resolve an alert to existing related decisions when the alert carries task references."""
    task_ids = incident_related_decisions(alert)
    return {
        "alert_id": alert.get("alert_id") or alert.get("id"),
        "related_decisions": [inspect_decision(conn, task_id) for task_id in task_ids],
    }


def _print_json(value: Any) -> int:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GateGraph read-only operator control")
    parser.add_argument("--db", required=True, help="Path to existing GateGraph SQLite DB")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect")
    inspect_p.add_argument("task_id")

    explain_p = sub.add_parser("explain")
    explain_p.add_argument("task_id")

    query_p = sub.add_parser("query")
    query_p.add_argument("--decision")
    query_p.add_argument("--guard")
    query_p.add_argument("--reason-code")
    query_p.add_argument("--since")
    query_p.add_argument("--until")

    drill_p = sub.add_parser("drilldown-stop-reason")
    drill_p.add_argument("reason_code")

    args = parser.parse_args(list(argv) if argv is not None else None)
    with _readonly_conn(args.db) as conn:
        if args.command == "inspect":
            return _print_json(inspect_decision(conn, args.task_id))
        if args.command == "explain":
            return _print_json(explain_compact(conn, args.task_id))
        if args.command == "query":
            return _print_json(query_traces(conn, TraceQuery(
                decision=args.decision,
                guard=args.guard,
                normalized_reason_code=args.reason_code,
                since=args.since,
                until=args.until,
            )))
        if args.command == "drilldown-stop-reason":
            return _print_json(drilldown_stop_reason(conn, args.reason_code))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
