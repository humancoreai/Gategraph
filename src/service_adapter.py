"""
WHY: service_adapter is the shared adapter seam for CLI and server mode.
INV: It delegates all decisions to governance.py and never duplicates rule/runtime logic.
SEC: malformed requests fail closed before Governance is called.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src import alert_aggregator, database, governance, monitoring_export, operational_hardening, runtime_guard, session_budget_guard
from src.config_loader import AppConfig


def db_path(config: AppConfig) -> Path:
    return Path(config.db_path).expanduser().resolve()


def connect_initialized(config: AppConfig):
    path = db_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    database.init_db(path)
    conn = database.get_connection(path)
    database.seed_rules(conn)
    database.ensure_runtime_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    return conn


def ensure_session_budget(conn, config: AppConfig) -> None:
    row = conn.execute("SELECT session_id FROM session_budgets WHERE session_id = ?", (config.session_id,)).fetchone()
    if row is None:
        session_budget_guard.create_session_budget(
            conn,
            session_id=config.session_id,
            max_session_cost_units=config.session_budget.max_session_cost_units,
            max_session_tasks=config.session_budget.max_session_tasks,
            max_agent_cost_units=config.session_budget.max_agent_cost_units,
        )


def initialize(config: AppConfig, *, reset: bool = False) -> dict[str, Any]:
    path = db_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    if reset:
        database.reset_db(path)
    else:
        database.init_db(path)
    conn = database.get_connection(path)
    database.seed_rules(conn)
    database.ensure_runtime_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    ensure_session_budget(conn, config)
    conn.close()
    return {"ok": True, "db_path": str(path), "mode": config.mode}


def evaluate_request(config: AppConfig, task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(task, dict):
        raise ValueError("request body must be a JSON object")
    task_id = str(task.get("task_id") or "server-task")
    requested = task.get("requested_capabilities", [])
    if not isinstance(requested, list):
        raise ValueError("task.requested_capabilities must be a list")
    projected_cost = int(task.get("projected_cost_units", 1))

    conn = connect_initialized(config)
    try:
        ensure_session_budget(conn, config)
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
        token_json = None
        if result.token is not None:
            runtime_budget = runtime_guard.create_budget(
                conn,
                task_id=task_id,
                max_steps=config.runtime_budget.max_steps,
                max_runtime_seconds=config.runtime_budget.max_runtime_seconds,
                max_cost_units=config.runtime_budget.max_cost_units,
                repeated_action_limit=config.runtime_budget.repeated_action_limit,
            )
            token_json = token_to_dict(result.token)

        return {
            "ok": True,
            "task_id": result.task_id,
            "decision": result.final_decision,
            "risk_level": result.risk_level,
            "risk_reason": result.risk_reason,
            "selected_rule_id": result.selected_rule_id,
            "matched_rule_ids": result.matched_rule_ids,
            "token_issued": result.token is not None,
            "token_id": result.token.token_id if result.token else None,
            "token": token_json,
            "runtime_budget_id": runtime_budget.budget_id if runtime_budget else None,
            "budget_scope_id": result.budget_scope_id,
            "escalation_state": result.escalation_state,
            "event_id": result.event_id,
            "decision_id": result.decision_id,
        }
    finally:
        conn.close()


def status(config: AppConfig) -> dict[str, Any]:
    conn = connect_initialized(config)
    try:
        tables = ["tasks", "events", "decisions", "capability_tokens", "session_budgets", "runtime_budgets"]
        counts = {table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}
        return {"ok": True, "db_path": str(db_path(config)), "mode": config.mode, "counts": counts}
    finally:
        conn.close()


def monitoring(config: AppConfig) -> dict[str, Any]:
    """Read-only operational export for CLI and server.

    INV: This function observes existing state only; it never repairs or decides.
    """
    conn = connect_initialized(config)
    try:
        operational_hardening.ensure_operational_schema(conn)
        snapshot = operational_hardening.collect_budget_snapshot(conn)
        incidents = operational_hardening.list_open_incidents(conn)
        alerts = operational_hardening.evaluate_operational_alerts(incidents)
        aggregated = alert_aggregator.aggregate_alerts(alerts)
        return monitoring_export.build_monitoring_export(
            budget_snapshot=snapshot,
            incidents=incidents,
            alerts=alerts,
            aggregated_alerts=aggregated,
        )
    finally:
        conn.close()


def token_to_dict(token) -> dict[str, Any]:
    data = asdict(token)
    data["issued_at"] = token.issued_at.isoformat()
    data["expires_at"] = token.expires_at.isoformat()
    return data
