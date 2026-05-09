"""
WHY: Runtime Guard controls whether a task may continue running, separate from capability governance.
INV: Runtime Guard never grants capabilities and never changes governance rules.
SEC: budget exhaustion fails closed before additional tool/model work is spent.
"""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


DEFAULT_MAX_STEPS = 20
DEFAULT_MAX_RUNTIME_SECONDS = 300
DEFAULT_MAX_COST_UNITS = 100
DEFAULT_REPEATED_ACTION_LIMIT = 3


@dataclass(frozen=True)
class RuntimeBudget:
    budget_id: str
    task_id: str
    max_steps: int
    max_runtime_seconds: int
    max_cost_units: int
    repeated_action_limit: int
    created_at: datetime


@dataclass(frozen=True)
class RuntimeDecision:
    decision: str                 # continue | warn | stop | escalate
    reason: str
    remaining_steps: int
    remaining_cost_units: int
    step_id: Optional[str] = None


def create_budget(
    conn: sqlite3.Connection,
    *,
    task_id: str,
    max_steps: int = DEFAULT_MAX_STEPS,
    max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
    max_cost_units: int = DEFAULT_MAX_COST_UNITS,
    repeated_action_limit: int = DEFAULT_REPEATED_ACTION_LIMIT,
) -> RuntimeBudget:
    """
    INV: every controlled task must have exactly one budget row.
    SEC: missing budget must not silently allow execution.
    """
    now = datetime.now(timezone.utc)
    budget_id = f"BUD-{uuid.uuid4().hex[:12].upper()}"

    with conn:
        conn.execute(
            """
            INSERT INTO runtime_budgets (
                budget_id, task_id, max_steps, max_runtime_seconds,
                max_cost_units, repeated_action_limit, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                budget_id, task_id, max_steps, max_runtime_seconds,
                max_cost_units, repeated_action_limit, now.isoformat(),
            ),
        )

    return RuntimeBudget(
        budget_id=budget_id,
        task_id=task_id,
        max_steps=max_steps,
        max_runtime_seconds=max_runtime_seconds,
        max_cost_units=max_cost_units,
        repeated_action_limit=repeated_action_limit,
        created_at=now,
    )


def get_budget(conn: sqlite3.Connection, task_id: str) -> Optional[RuntimeBudget]:
    row = conn.execute(
        """
        SELECT budget_id, task_id, max_steps, max_runtime_seconds,
               max_cost_units, repeated_action_limit, created_at
        FROM runtime_budgets
        WHERE task_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (task_id,),
    ).fetchone()

    if row is None:
        return None

    return RuntimeBudget(
        budget_id=row["budget_id"],
        task_id=row["task_id"],
        max_steps=row["max_steps"],
        max_runtime_seconds=row["max_runtime_seconds"],
        max_cost_units=row["max_cost_units"],
        repeated_action_limit=row["repeated_action_limit"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def evaluate_before_step(
    conn: sqlite3.Connection,
    *,
    task_id: str,
    actor_id: str,
    action_type: str,
    target: str = "",
    cost_units: int = 1,
) -> RuntimeDecision:
    """
    INV: runtime decision is evaluated before the step is allowed to continue.
    SEC: if no budget exists, stop instead of allowing unbounded execution.
    """
    if cost_units <= 0:
        return _record_decision(
            conn, task_id, None, "stop", "invalid cost_units: must be positive", 0, 0
        )

    budget = get_budget(conn, task_id)
    if budget is None:
        return _record_decision(
            conn, task_id, None, "stop", "no runtime budget exists", 0, 0
        )

    now = datetime.now(timezone.utc)
    elapsed = (now - budget.created_at).total_seconds()
    prior_steps = _count_steps(conn, task_id)
    used_cost = _sum_cost(conn, task_id)
    signature = _signature(actor_id, action_type, target)
    repeated_count = _count_signature(conn, task_id, signature)

    remaining_steps = max(budget.max_steps - prior_steps, 0)
    remaining_cost = max(budget.max_cost_units - used_cost, 0)

    if elapsed > budget.max_runtime_seconds:
        return _record_decision(
            conn, task_id, None, "stop",
            f"max_runtime_seconds exceeded: {elapsed:.2f}s > {budget.max_runtime_seconds}s",
            remaining_steps, remaining_cost
        )

    if prior_steps >= budget.max_steps:
        return _record_decision(
            conn, task_id, None, "stop",
            f"max_steps exceeded: {prior_steps} >= {budget.max_steps}",
            remaining_steps, remaining_cost
        )

    if used_cost + cost_units > budget.max_cost_units:
        return _record_decision(
            conn, task_id, None, "stop",
            f"max_cost_units exceeded: {used_cost + cost_units} > {budget.max_cost_units}",
            remaining_steps, remaining_cost
        )

    if repeated_count >= budget.repeated_action_limit:
        return _record_decision(
            conn, task_id, None, "stop",
            f"repeated_action_limit exceeded for signature {signature!r}",
            remaining_steps, remaining_cost
        )

    step_id = _record_step(
        conn,
        task_id=task_id,
        actor_id=actor_id,
        action_type=action_type,
        action_signature=signature,
        cost_units=cost_units,
    )

    # WHY: remaining values are reported after the accepted step.
    return _record_decision(
        conn,
        task_id,
        step_id,
        "continue",
        "within budget",
        max(budget.max_steps - (prior_steps + 1), 0),
        max(budget.max_cost_units - (used_cost + cost_units), 0),
    )


def _signature(actor_id: str, action_type: str, target: str) -> str:
    # WHY: simple structural signature; semantic loop detection is intentionally out of scope.
    return f"{actor_id}:{action_type}:{target}".lower().strip()


def _count_steps(conn: sqlite3.Connection, task_id: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM runtime_steps WHERE task_id = ?",
        (task_id,),
    ).fetchone()[0]


def _sum_cost(conn: sqlite3.Connection, task_id: str) -> int:
    value = conn.execute(
        "SELECT COALESCE(SUM(cost_units), 0) FROM runtime_steps WHERE task_id = ?",
        (task_id,),
    ).fetchone()[0]
    return int(value or 0)


def _count_signature(conn: sqlite3.Connection, task_id: str, signature: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM runtime_steps WHERE task_id = ? AND action_signature = ?",
        (task_id, signature),
    ).fetchone()[0]


def _record_step(
    conn: sqlite3.Connection,
    *,
    task_id: str,
    actor_id: str,
    action_type: str,
    action_signature: str,
    cost_units: int,
) -> str:
    step_id = f"STEP-{uuid.uuid4().hex[:12].upper()}"
    step_index = _count_steps(conn, task_id) + 1
    now = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            """
            INSERT INTO runtime_steps (
                step_id, task_id, step_index, actor_id,
                action_type, action_signature, cost_units, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (step_id, task_id, step_index, actor_id, action_type, action_signature, cost_units, now),
        )

    return step_id


def _record_decision(
    conn: sqlite3.Connection,
    task_id: str,
    step_id: Optional[str],
    decision: str,
    reason: str,
    remaining_steps: int,
    remaining_cost_units: int,
) -> RuntimeDecision:
    decision_id = f"RTD-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            """
            INSERT INTO runtime_decisions (
                decision_id, task_id, step_id, decision, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (decision_id, task_id, step_id, decision, reason, now),
        )

    return RuntimeDecision(
        decision=decision,
        reason=reason,
        remaining_steps=remaining_steps,
        remaining_cost_units=remaining_cost_units,
        step_id=step_id,
    )
