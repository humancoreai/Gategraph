"""
WHY: Flood Guard closes micro-task flooding that can bypass per-task limits.
INV: Deterministic hard caps only; no heuristic scoring and no operational alert feedback path.
SEC: Invalid projected cost fails closed before runtime work is recorded.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

from src import session_budget_guard

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_TASKS_PER_WINDOW = 1000
DEFAULT_MAX_COST_UNITS_PER_WINDOW = 1000


@dataclass(frozen=True)
class FloodGuardConfig:
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    max_tasks_per_window: int = DEFAULT_MAX_TASKS_PER_WINDOW
    max_cost_units_per_window: int = DEFAULT_MAX_COST_UNITS_PER_WINDOW


@dataclass(frozen=True)
class FloodGuardDecision:
    decision: str  # continue | stop
    reason: str
    tasks_in_window: int
    cost_units_in_window: int


def _parse_dt(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def evaluate_flood_guard(
    conn: sqlite3.Connection,
    *,
    actor_id: str,
    projected_cost_units: int,
    config: FloodGuardConfig | None = None,
    now: datetime | None = None,
) -> FloodGuardDecision:
    """Evaluate actor-scoped global window limits from existing session decisions.

    INV: This reads committed prior decisions only. It does not reserve, consume, or release budget.
    """
    session_budget_guard.ensure_session_budget_schema(conn)
    cfg = config or FloodGuardConfig()
    now_dt = now or datetime.now(timezone.utc)

    if projected_cost_units <= 0:
        return FloodGuardDecision("stop", "FLOOD_INVALID_PROJECTED_COST", 0, 0)
    if cfg.window_seconds <= 0 or cfg.max_tasks_per_window <= 0 or cfg.max_cost_units_per_window <= 0:
        return FloodGuardDecision("stop", "FLOOD_INVALID_CONFIG", 0, 0)

    window_start = now_dt - timedelta(seconds=cfg.window_seconds)
    rows = conn.execute(
        """
        SELECT projected_cost_units, created_at
        FROM session_budget_decisions
        WHERE actor_id = ? AND decision = 'continue'
        """,
        (actor_id,),
    ).fetchall()

    tasks_in_window = 0
    cost_units_in_window = 0
    for row in rows:
        created_at = _parse_dt(str(row["created_at"] if isinstance(row, sqlite3.Row) else row[1]))
        if created_at >= window_start:
            tasks_in_window += 1
            cost_units_in_window += int(row["projected_cost_units"] if isinstance(row, sqlite3.Row) else row[0])

    if tasks_in_window >= cfg.max_tasks_per_window:
        return FloodGuardDecision("stop", "FLOOD_TASK_WINDOW_LIMIT", tasks_in_window, cost_units_in_window)
    if cost_units_in_window + projected_cost_units > cfg.max_cost_units_per_window:
        return FloodGuardDecision("stop", "FLOOD_COST_WINDOW_LIMIT", tasks_in_window, cost_units_in_window)

    return FloodGuardDecision("continue", "FLOOD_OK", tasks_in_window, cost_units_in_window)
