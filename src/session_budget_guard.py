"""
WHY: Session Budget Guard closes cross-task cost drift without changing capability governance.
INV: this module never grants capabilities and never mutates Governance/Enforcement/Pattern rules.
SEC: missing session budget fails closed when a session_id is explicitly evaluated.
SEC: session budget evaluation uses a write transaction to avoid read-then-write races under parallel callers.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


DEFAULT_MAX_SESSION_COST_UNITS = 100
DEFAULT_MAX_SESSION_TASKS = 50
DEFAULT_MAX_AGENT_COST_UNITS = 60


@dataclass(frozen=True)
class SessionBudget:
    session_id: str
    max_session_cost_units: int
    max_session_tasks: int
    max_agent_cost_units: int
    created_at: datetime


@dataclass(frozen=True)
class SessionDecision:
    decision: str  # continue | stop
    reason: str
    remaining_session_cost_units: int
    remaining_session_tasks: int
    remaining_agent_cost_units: int
    decision_id: str


def ensure_session_budget_schema(conn: sqlite3.Connection) -> None:
    """
    INV: additive schema only; does not modify existing runtime or governance tables.
    """
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS session_budgets (
        session_id TEXT PRIMARY KEY,
        max_session_cost_units INTEGER NOT NULL,
        max_session_tasks INTEGER NOT NULL,
        max_agent_cost_units INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS session_task_links (
        session_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        reserved_cost_units INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        PRIMARY KEY (session_id, task_id)
    );

    CREATE TABLE IF NOT EXISTS session_budget_decisions (
        decision_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        projected_cost_units INTEGER NOT NULL,
        decision TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_session_task_links_session
        ON session_task_links(session_id);

    CREATE INDEX IF NOT EXISTS idx_session_task_links_actor
        ON session_task_links(session_id, actor_id);

    CREATE INDEX IF NOT EXISTS idx_session_budget_decisions_session
        ON session_budget_decisions(session_id);
    """)

    # WHY: v0.8.3 keeps old DBs compatible if they were created before reserved_cost_units existed.
    columns = {
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in conn.execute("PRAGMA table_info(session_task_links)").fetchall()
    }
    if "reserved_cost_units" not in columns:
        conn.execute(
            "ALTER TABLE session_task_links ADD COLUMN reserved_cost_units INTEGER NOT NULL DEFAULT 0"
        )


def create_session_budget(
    conn: sqlite3.Connection,
    *,
    session_id: Optional[str] = None,
    max_session_cost_units: int = DEFAULT_MAX_SESSION_COST_UNITS,
    max_session_tasks: int = DEFAULT_MAX_SESSION_TASKS,
    max_agent_cost_units: int = DEFAULT_MAX_AGENT_COST_UNITS,
) -> SessionBudget:
    ensure_session_budget_schema(conn)
    sid = session_id or f"SES-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    with conn:
        conn.execute(
            """
            INSERT INTO session_budgets (
                session_id, max_session_cost_units, max_session_tasks,
                max_agent_cost_units, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (sid, max_session_cost_units, max_session_tasks, max_agent_cost_units, now.isoformat()),
        )
    return SessionBudget(
        session_id=sid,
        max_session_cost_units=max_session_cost_units,
        max_session_tasks=max_session_tasks,
        max_agent_cost_units=max_agent_cost_units,
        created_at=now,
    )


def evaluate_before_task(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    task_id: str,
    actor_id: str,
    projected_cost_units: int,
) -> SessionDecision:
    """
    INV: evaluates cumulative session/agent cost before a task receives fresh runtime work.
    SEC: BEGIN IMMEDIATE serializes read-budget/write-link so parallel callers cannot oversubscribe budget.
    SEC: projected cost is reserved on the session link so the next task sees committed reservations immediately.
    """
    ensure_session_budget_schema(conn)
    _begin_immediate(conn)
    try:
        budget = _get_session_budget(conn, session_id)
        if budget is None:
            decision = _record_decision(
                conn, session_id, task_id, actor_id, projected_cost_units,
                "stop", "no session budget exists", 0, 0, 0
            )
            conn.commit()
            return decision

        linked_tasks = _count_linked_tasks(conn, session_id)
        session_cost = _sum_reserved_or_actual_session_cost(conn, session_id)
        agent_cost = _sum_reserved_or_actual_agent_cost(conn, session_id, actor_id)

        remaining_session_tasks = max(budget.max_session_tasks - linked_tasks, 0)
        remaining_session_cost = max(budget.max_session_cost_units - session_cost, 0)
        remaining_agent_cost = max(budget.max_agent_cost_units - agent_cost, 0)

        if linked_tasks >= budget.max_session_tasks:
            decision = _record_decision(
                conn, session_id, task_id, actor_id, projected_cost_units,
                "stop",
                f"max_session_tasks exceeded: {linked_tasks} >= {budget.max_session_tasks}",
                remaining_session_cost, remaining_session_tasks, remaining_agent_cost,
            )
            conn.commit()
            return decision

        if session_cost + projected_cost_units > budget.max_session_cost_units:
            decision = _record_decision(
                conn, session_id, task_id, actor_id, projected_cost_units,
                "stop",
                f"max_session_cost_units exceeded: {session_cost + projected_cost_units} > {budget.max_session_cost_units}",
                remaining_session_cost, remaining_session_tasks, remaining_agent_cost,
            )
            conn.commit()
            return decision

        if agent_cost + projected_cost_units > budget.max_agent_cost_units:
            decision = _record_decision(
                conn, session_id, task_id, actor_id, projected_cost_units,
                "stop",
                f"max_agent_cost_units exceeded: {agent_cost + projected_cost_units} > {budget.max_agent_cost_units}",
                remaining_session_cost, remaining_session_tasks, remaining_agent_cost,
            )
            conn.commit()
            return decision

        _link_task(conn, session_id, task_id, actor_id, projected_cost_units)

        decision = _record_decision(
            conn, session_id, task_id, actor_id, projected_cost_units,
            "continue",
            "within session budget",
            max(budget.max_session_cost_units - (session_cost + projected_cost_units), 0),
            max(budget.max_session_tasks - (linked_tasks + 1), 0),
            max(budget.max_agent_cost_units - (agent_cost + projected_cost_units), 0),
        )
        conn.commit()
        return decision
    except Exception:
        conn.rollback()
        raise


def _begin_immediate(conn: sqlite3.Connection) -> None:
    """
    WHY: sqlite3 context managers open deferred transactions by default; BEGIN IMMEDIATE takes the write lock up front.
    EDGE: if caller already opened a transaction, SQLite rejects BEGIN IMMEDIATE; in that case we stay inside caller's transaction.
    """
    if conn.in_transaction:
        return
    conn.execute("BEGIN IMMEDIATE")


def _get_session_budget(conn: sqlite3.Connection, session_id: str) -> Optional[SessionBudget]:
    row = conn.execute(
        """
        SELECT session_id, max_session_cost_units, max_session_tasks,
               max_agent_cost_units, created_at
        FROM session_budgets
        WHERE session_id = ?
        """,
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    return SessionBudget(
        session_id=row["session_id"],
        max_session_cost_units=row["max_session_cost_units"],
        max_session_tasks=row["max_session_tasks"],
        max_agent_cost_units=row["max_agent_cost_units"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _link_task(conn: sqlite3.Connection, session_id: str, task_id: str, actor_id: str, reserved_cost_units: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO session_task_links (
            session_id, task_id, actor_id, reserved_cost_units, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, task_id, actor_id, reserved_cost_units, now),
    )


def _count_linked_tasks(conn: sqlite3.Connection, session_id: str) -> int:
    return int(conn.execute(
        "SELECT COUNT(*) FROM session_task_links WHERE session_id = ?",
        (session_id,),
    ).fetchone()[0] or 0)


def _sum_reserved_or_actual_session_cost(conn: sqlite3.Connection, session_id: str) -> int:
    value = conn.execute(
        """
        SELECT COALESCE(SUM(MAX(st.reserved_cost_units, COALESCE(actual.actual_cost_units, 0))), 0)
        FROM session_task_links st
        LEFT JOIN (
            SELECT task_id, SUM(cost_units) AS actual_cost_units
            FROM runtime_steps
            GROUP BY task_id
        ) actual ON actual.task_id = st.task_id
        WHERE st.session_id = ?
        """,
        (session_id,),
    ).fetchone()[0]
    return int(value or 0)


def _sum_reserved_or_actual_agent_cost(conn: sqlite3.Connection, session_id: str, actor_id: str) -> int:
    value = conn.execute(
        """
        SELECT COALESCE(SUM(MAX(st.reserved_cost_units, COALESCE(actual.actual_cost_units, 0))), 0)
        FROM session_task_links st
        LEFT JOIN (
            SELECT task_id, SUM(cost_units) AS actual_cost_units
            FROM runtime_steps
            GROUP BY task_id
        ) actual ON actual.task_id = st.task_id
        WHERE st.session_id = ? AND st.actor_id = ?
        """,
        (session_id, actor_id),
    ).fetchone()[0]
    return int(value or 0)


def _record_decision(
    conn: sqlite3.Connection,
    session_id: str,
    task_id: str,
    actor_id: str,
    projected_cost_units: int,
    decision: str,
    reason: str,
    remaining_session_cost_units: int,
    remaining_session_tasks: int,
    remaining_agent_cost_units: int,
) -> SessionDecision:
    decision_id = f"SBD-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO session_budget_decisions (
            decision_id, session_id, task_id, actor_id, projected_cost_units,
            decision, reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (decision_id, session_id, task_id, actor_id, projected_cost_units, decision, reason, now),
    )

    return SessionDecision(
        decision=decision,
        reason=reason,
        remaining_session_cost_units=remaining_session_cost_units,
        remaining_session_tasks=remaining_session_tasks,
        remaining_agent_cost_units=remaining_agent_cost_units,
        decision_id=decision_id,
    )
