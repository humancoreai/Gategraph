"""
WHY: CLI is the stable single-node entry point for operating GateGraph without test harnesses.
INV: CLI is an adapter only; it must not duplicate or bypass Governance/Enforcement decisions.
SEC: invalid inputs fail closed and are reported as structured JSON with non-zero exit codes.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src import alert_aggregator, database, governance, monitoring_export, operational_hardening, runtime_guard, session_budget_guard
from src.config_loader import AppConfig, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gategraph", description="GateGraph single-node CLI")
    parser.add_argument("--config", default=None, help="Path to config YAML/JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Initialize a single-node GateGraph database")
    init_p.add_argument("--reset", action="store_true", help="Delete and recreate the configured DB")

    eval_p = sub.add_parser("evaluate", help="Evaluate a task and emit a structured decision")
    eval_p.add_argument("--task", required=True, help="Path to task JSON")
    eval_p.add_argument("--token-out", default=None, help="Optional path for issued token JSON")

    status_p = sub.add_parser("status", help="Emit a minimal DB/status summary")
    status_p.add_argument("--json", action="store_true", help="Emit JSON (default behavior retained for scripts)")

    export_p = sub.add_parser("export-monitoring", help="Write a read-only monitoring export JSON")
    export_p.add_argument("--out", required=True, help="Output path for monitoring JSON")

    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "init":
            return _cmd_init(config, reset=args.reset)
        if args.command == "evaluate":
            return _cmd_evaluate(config, task_path=Path(args.task), token_out=Path(args.token_out) if args.token_out else None)
        if args.command == "status":
            return _cmd_status(config)
        if args.command == "export-monitoring":
            return _cmd_export_monitoring(config, out_path=Path(args.out))
        raise ValueError(f"unknown command: {args.command}")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


def _db_path(config: AppConfig) -> Path:
    return Path(config.db_path).expanduser().resolve()


def _connect_initialized(config: AppConfig):
    path = _db_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    database.init_db(path)
    conn = database.get_connection(path)
    database.seed_rules(conn)
    database.ensure_runtime_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    return conn


def _cmd_init(config: AppConfig, *, reset: bool) -> int:
    path = _db_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    if reset:
        database.reset_db(path)
    else:
        database.init_db(path)
    conn = database.get_connection(path)
    database.seed_rules(conn)
    database.ensure_runtime_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    _ensure_session_budget(conn, config)
    conn.close()
    print(json.dumps({"ok": True, "db_path": str(path), "mode": config.mode}, indent=2))
    return 0


def _ensure_session_budget(conn, config: AppConfig) -> None:
    row = conn.execute("SELECT session_id FROM session_budgets WHERE session_id = ?", (config.session_id,)).fetchone()
    if row is None:
        session_budget_guard.create_session_budget(
            conn,
            session_id=config.session_id,
            max_session_cost_units=config.session_budget.max_session_cost_units,
            max_session_tasks=config.session_budget.max_session_tasks,
            max_agent_cost_units=config.session_budget.max_agent_cost_units,
        )


def _cmd_evaluate(config: AppConfig, *, task_path: Path, token_out: Path | None) -> int:
    task = json.loads(task_path.read_text(encoding="utf-8"))
    conn = _connect_initialized(config)
    _ensure_session_budget(conn, config)
    task_id = str(task.get("task_id") or task_path.stem)
    requested = task.get("requested_capabilities", [])
    if not isinstance(requested, list):
        raise ValueError("task.requested_capabilities must be a list")
    projected_cost = int(task.get("projected_cost_units", 1))

    result = governance.evaluate_task(
        conn,
        task_id=task_id,
        task_type=str(task.get("task_type", "single_node_task")),
        requested_capabilities=[str(item) for item in requested],
        input_source=str(task.get("input_source", "local")),
        data_sensitivity=str(task.get("data_sensitivity", "internal")),
        secrets_involved=bool(task.get("secrets_involved", False)),
        actor_id=str(task.get("actor_id", config.actor_id)),
        projected_cost_units=projected_cost,
        system_budget_units=config.system_budget_units,
        actor_budget_units=config.actor_budget_units,
    )

    runtime_budget = None
    if result.token is not None:
        runtime_budget = runtime_guard.create_budget(
            conn,
            task_id=task_id,
            max_steps=config.runtime_budget.max_steps,
            max_runtime_seconds=config.runtime_budget.max_runtime_seconds,
            max_cost_units=config.runtime_budget.max_cost_units,
            repeated_action_limit=config.runtime_budget.repeated_action_limit,
        )
        if token_out is not None:
            token_out.parent.mkdir(parents=True, exist_ok=True)
            token_out.write_text(json.dumps(_token_to_dict(result.token), indent=2), encoding="utf-8")

    output = {
        "ok": True,
        "task_id": result.task_id,
        "decision": result.final_decision,
        "risk_level": result.risk_level,
        "risk_reason": result.risk_reason,
        "selected_rule_id": result.selected_rule_id,
        "matched_rule_ids": result.matched_rule_ids,
        "token_issued": result.token is not None,
        "token_id": result.token.token_id if result.token else None,
        "runtime_budget_id": runtime_budget.budget_id if runtime_budget else None,
        "budget_scope_id": result.budget_scope_id,
        "escalation_state": result.escalation_state,
        "event_id": result.event_id,
        "decision_id": result.decision_id,
    }
    conn.close()
    print(json.dumps(output, indent=2))
    return 0 if result.token is not None or result.final_decision in {"allow", "warn", "require_review", "require_approval", "block"} else 1


def _cmd_status(config: AppConfig) -> int:
    conn = _connect_initialized(config)
    tables = ["tasks", "events", "decisions", "capability_tokens", "session_budgets", "runtime_budgets"]
    counts: dict[str, int] = {}
    for table in tables:
        counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    conn.close()
    print(json.dumps({"ok": True, "db_path": str(_db_path(config)), "counts": counts}, indent=2))
    return 0


def _cmd_export_monitoring(config: AppConfig, *, out_path: Path) -> int:
    """Export current operational state without repairing or deciding.

    INV: This command reads existing state and writes only the requested export file.
    """
    conn = _connect_initialized(config)
    operational_hardening.ensure_operational_schema(conn)
    snapshot = operational_hardening.collect_budget_snapshot(conn)
    incidents = operational_hardening.list_open_incidents(conn)
    alerts = operational_hardening.evaluate_operational_alerts(incidents)
    aggregated = alert_aggregator.aggregate_alerts(alerts)
    report = monitoring_export.build_monitoring_export(
        budget_snapshot=snapshot,
        incidents=incidents,
        alerts=alerts,
        aggregated_alerts=aggregated,
    )
    conn.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out_path": str(out_path), "summary": report["summary"]}, indent=2))
    return 0


def _token_to_dict(token) -> dict[str, Any]:
    data = asdict(token)
    data["issued_at"] = token.issued_at.isoformat()
    data["expires_at"] = token.expires_at.isoformat()
    return data


if __name__ == "__main__":
    raise SystemExit(main())
