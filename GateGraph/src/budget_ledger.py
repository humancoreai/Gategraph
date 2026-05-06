"""
WHY: Cross-session budget control prevents agents from bypassing limits by splitting work.
INV: Budget authority belongs to Governance; Runtime only receives signed constraints via tokens.
SEC: missing, invalid, or exhausted budget state fails closed and never issues a reservation.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

ESCALATION_ORDER = ("normal", "degraded", "throttled", "blocked")
VALID_SCOPE_TYPES = ("system", "actor", "task", "session")
ACTIVE_RESERVATION = "reserved"


@dataclass(frozen=True)
class BudgetScope:
    scope_id: str
    scope_type: str
    parent_scope_id: Optional[str]
    allocated_units: int
    consumed_units: int
    reserved_units: int
    state: str


@dataclass(frozen=True)
class BudgetReservation:
    reservation_id: str
    scope_id: str
    amount_units: int
    status: str
    idempotency_key: str
    expires_at: str
    was_duplicate: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_budget_schema(conn: sqlite3.Connection) -> None:
    """WHY: additive schema keeps older evidence DBs compatible while adding ledger authority."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS budget_scopes (
            scope_id TEXT PRIMARY KEY,
            scope_type TEXT NOT NULL CHECK (scope_type IN ('system','actor','task','session')),
            parent_scope_id TEXT,
            allocated_units INTEGER NOT NULL CHECK (allocated_units >= 0),
            consumed_units INTEGER NOT NULL DEFAULT 0 CHECK (consumed_units >= 0),
            reserved_units INTEGER NOT NULL DEFAULT 0 CHECK (reserved_units >= 0),
            state TEXT NOT NULL DEFAULT 'normal' CHECK (state IN ('normal','degraded','throttled','blocked')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            reason_code TEXT NOT NULL DEFAULT 'BUDGET_SCOPE_CREATED',
            FOREIGN KEY (parent_scope_id) REFERENCES budget_scopes(scope_id)
        );

        CREATE TABLE IF NOT EXISTS budget_reservations (
            reservation_id TEXT PRIMARY KEY,
            scope_id TEXT NOT NULL,
            amount_units INTEGER NOT NULL CHECK (amount_units >= 0),
            status TEXT NOT NULL CHECK (status IN ('reserved','consumed','released','expired')),
            idempotency_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            consumed_at TEXT,
            released_at TEXT,
            reason_code TEXT NOT NULL DEFAULT 'BUDGET_RESERVED',
            FOREIGN KEY (scope_id) REFERENCES budget_scopes(scope_id)
        );

        CREATE INDEX IF NOT EXISTS idx_budget_scopes_parent
            ON budget_scopes(parent_scope_id);
        CREATE INDEX IF NOT EXISTS idx_budget_reservations_scope
            ON budget_reservations(scope_id, status);
        CREATE INDEX IF NOT EXISTS idx_budget_reservations_idempotency
            ON budget_reservations(idempotency_key);
        """
    )


def _row_to_scope(row: sqlite3.Row | None) -> Optional[BudgetScope]:
    if row is None:
        return None
    return BudgetScope(
        scope_id=row["scope_id"],
        scope_type=row["scope_type"],
        parent_scope_id=row["parent_scope_id"],
        allocated_units=int(row["allocated_units"]),
        consumed_units=int(row["consumed_units"]),
        reserved_units=int(row["reserved_units"]),
        state=row["state"],
    )


def create_scope(
    conn: sqlite3.Connection,
    *,
    scope_id: str,
    scope_type: str,
    allocated_units: int,
    parent_scope_id: Optional[str] = None,
    reason_code: str = "BUDGET_SCOPE_CREATED",
) -> BudgetScope:
    ensure_budget_schema(conn)
    if scope_type not in VALID_SCOPE_TYPES or allocated_units < 0:
        raise ValueError("invalid budget scope")
    if parent_scope_id and not get_scope(conn, parent_scope_id):
        raise ValueError("parent budget scope not found")
    now = utc_now()
    conn.execute(
        """
        INSERT OR IGNORE INTO budget_scopes
          (scope_id, scope_type, parent_scope_id, allocated_units, consumed_units, reserved_units, state, created_at, updated_at, reason_code)
        VALUES (?, ?, ?, ?, 0, 0, 'normal', ?, ?, ?)
        """,
        (scope_id, scope_type, parent_scope_id, allocated_units, now, now, reason_code),
    )
    scope = get_scope(conn, scope_id)
    if scope is None:
        raise RuntimeError("budget scope create failed")
    return scope


def ensure_scope(
    conn: sqlite3.Connection,
    *,
    scope_id: str,
    scope_type: str,
    allocated_units: int,
    parent_scope_id: Optional[str] = None,
) -> BudgetScope:
    existing = get_scope(conn, scope_id)
    if existing:
        return existing
    return create_scope(conn, scope_id=scope_id, scope_type=scope_type, allocated_units=allocated_units, parent_scope_id=parent_scope_id)


def get_scope(conn: sqlite3.Connection, scope_id: str) -> Optional[BudgetScope]:
    ensure_budget_schema(conn)
    return _row_to_scope(conn.execute("SELECT * FROM budget_scopes WHERE scope_id = ?", (scope_id,)).fetchone())


def available_units(conn: sqlite3.Connection, scope_id: str) -> int:
    expire_stale_reservations(conn)
    scope = get_scope(conn, scope_id)
    if not scope:
        return 0
    return max(scope.allocated_units - scope.consumed_units - scope.reserved_units, 0)


def derive_escalation_state(consumed_units: int, reserved_units: int, allocated_units: int) -> str:
    if allocated_units <= 0:
        return "blocked"
    ratio = (consumed_units + reserved_units) / allocated_units
    if ratio >= 1.0:
        return "blocked"
    if ratio >= 0.90:
        return "throttled"
    if ratio >= 0.70:
        return "degraded"
    return "normal"


def reserve_budget(
    conn: sqlite3.Connection,
    *,
    scope_id: str,
    amount_units: int,
    idempotency_key: str,
    ttl_seconds: int = 300,
) -> BudgetReservation:
    """
    INV: reservation is atomic and idempotent; repeated requests with same key cannot double-reserve.
    SEC: missing scope, blocked state, expired budget, or insufficient units fail closed via ValueError.
    """
    ensure_budget_schema(conn)
    if amount_units <= 0:
        raise ValueError("BUDGET_INVALID_AMOUNT")
    expire_stale_reservations(conn)

    existing = conn.execute(
        "SELECT * FROM budget_reservations WHERE idempotency_key = ?",
        (idempotency_key,),
    ).fetchone()
    if existing:
        if existing["scope_id"] != scope_id or int(existing["amount_units"]) != amount_units:
            raise ValueError("BUDGET_IDEMPOTENCY_CONFLICT")
        return BudgetReservation(existing["reservation_id"], existing["scope_id"], int(existing["amount_units"]), existing["status"], existing["idempotency_key"], existing["expires_at"], True)

    scope = get_scope(conn, scope_id)
    if scope is None:
        raise ValueError("BUDGET_SCOPE_NOT_FOUND")
    if scope.state == "blocked":
        raise ValueError("ESCALATION_BLOCKED")
    if available_units(conn, scope_id) < amount_units:
        _set_scope_state(conn, scope_id, "blocked", "BUDGET_EXCEEDED")
        raise ValueError("BUDGET_EXCEEDED")

    reservation_id = f"BRES-{uuid.uuid4().hex[:12].upper()}"
    now_dt = datetime.now(timezone.utc)
    expires_at = (now_dt + timedelta(seconds=ttl_seconds)).isoformat()
    now = now_dt.isoformat()
    next_reserved = scope.reserved_units + amount_units
    next_state = derive_escalation_state(scope.consumed_units, next_reserved, scope.allocated_units)
    conn.execute(
        """
        INSERT INTO budget_reservations
          (reservation_id, scope_id, amount_units, status, idempotency_key, created_at, expires_at, reason_code)
        VALUES (?, ?, ?, 'reserved', ?, ?, ?, 'BUDGET_RESERVED')
        """,
        (reservation_id, scope_id, amount_units, idempotency_key, now, expires_at),
    )
    conn.execute(
        """
        UPDATE budget_scopes
        SET reserved_units = ?, state = ?, updated_at = ?, reason_code = 'BUDGET_RESERVED'
        WHERE scope_id = ?
        """,
        (next_reserved, next_state, now, scope_id),
    )
    return BudgetReservation(reservation_id, scope_id, amount_units, ACTIVE_RESERVATION, idempotency_key, expires_at, False)


def consume_reservation(conn: sqlite3.Connection, reservation_id: str, actual_units: Optional[int] = None) -> BudgetReservation:
    ensure_budget_schema(conn)
    row = conn.execute("SELECT * FROM budget_reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
    if row is None:
        raise ValueError("BUDGET_RESERVATION_NOT_FOUND")
    if row["status"] == "consumed":
        return BudgetReservation(row["reservation_id"], row["scope_id"], int(row["amount_units"]), row["status"], row["idempotency_key"], row["expires_at"], True)
    if row["status"] != "reserved":
        raise ValueError("BUDGET_RESERVATION_NOT_ACTIVE")
    reserved_amount = int(row["amount_units"])
    amount = reserved_amount if actual_units is None else actual_units
    if amount < 0 or amount > reserved_amount:
        raise ValueError("BUDGET_CONSUME_AMOUNT_INVALID")
    scope = get_scope(conn, row["scope_id"])
    if scope is None:
        raise ValueError("BUDGET_SCOPE_NOT_FOUND")
    now = utc_now()
    next_consumed = scope.consumed_units + amount
    next_reserved = max(scope.reserved_units - reserved_amount, 0)
    next_state = derive_escalation_state(next_consumed, next_reserved, scope.allocated_units)
    conn.execute("UPDATE budget_reservations SET status = 'consumed', consumed_at = ?, reason_code = 'BUDGET_CONSUMED' WHERE reservation_id = ?", (now, reservation_id))
    conn.execute(
        "UPDATE budget_scopes SET consumed_units = ?, reserved_units = ?, state = ?, updated_at = ?, reason_code = 'BUDGET_CONSUMED' WHERE scope_id = ?",
        (next_consumed, next_reserved, next_state, now, row["scope_id"]),
    )
    return BudgetReservation(row["reservation_id"], row["scope_id"], reserved_amount, "consumed", row["idempotency_key"], row["expires_at"], False)


def release_reservation(conn: sqlite3.Connection, reservation_id: str, reason_code: str = "BUDGET_RELEASED") -> BudgetReservation:
    ensure_budget_schema(conn)
    row = conn.execute("SELECT * FROM budget_reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
    if row is None:
        raise ValueError("BUDGET_RESERVATION_NOT_FOUND")
    if row["status"] != "reserved":
        return BudgetReservation(row["reservation_id"], row["scope_id"], int(row["amount_units"]), row["status"], row["idempotency_key"], row["expires_at"], True)
    scope = get_scope(conn, row["scope_id"])
    if scope is None:
        raise ValueError("BUDGET_SCOPE_NOT_FOUND")
    now = utc_now()
    next_reserved = max(scope.reserved_units - int(row["amount_units"]), 0)
    next_state = derive_escalation_state(scope.consumed_units, next_reserved, scope.allocated_units)
    status = "expired" if reason_code == "BUDGET_EXPIRED" else "released"
    conn.execute("UPDATE budget_reservations SET status = ?, released_at = ?, reason_code = ? WHERE reservation_id = ?", (status, now, reason_code, reservation_id))
    conn.execute("UPDATE budget_scopes SET reserved_units = ?, state = ?, updated_at = ?, reason_code = ? WHERE scope_id = ?", (next_reserved, next_state, now, reason_code, row["scope_id"]))
    return BudgetReservation(row["reservation_id"], row["scope_id"], int(row["amount_units"]), status, row["idempotency_key"], row["expires_at"], False)


def expire_stale_reservations(conn: sqlite3.Connection) -> int:
    ensure_budget_schema(conn)
    now = utc_now()
    rows = conn.execute("SELECT reservation_id FROM budget_reservations WHERE status = 'reserved' AND expires_at <= ?", (now,)).fetchall()
    for row in rows:
        release_reservation(conn, row["reservation_id"], "BUDGET_EXPIRED")
    return len(rows)


def _set_scope_state(conn: sqlite3.Connection, scope_id: str, state: str, reason_code: str) -> None:
    if state not in ESCALATION_ORDER:
        state = "blocked"
    conn.execute("UPDATE budget_scopes SET state = ?, updated_at = ?, reason_code = ? WHERE scope_id = ?", (state, utc_now(), reason_code, scope_id))
