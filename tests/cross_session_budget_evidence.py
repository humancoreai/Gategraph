"""
WHY: Evidence for cross-session budget control against task-splitting cost bypass.
INV: Governance reserves budget; Runtime/Enforcement never create or expand budget.
SEC: exhausted, missing, or stale budget state must fail closed.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules
from src import budget_ledger, governance, enforcement


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_cross_session_budget_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        seed_rules(conn)
        budget_ledger.ensure_budget_schema(conn)
    return conn, db_path


def close_conn(conn, db_path: Path) -> None:
    conn.close()
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


def check(name: str, ok: bool, detail: dict | None = None) -> dict:
    return {"name": name, "ok": bool(ok), "detail": detail or {}}


def test_cross_session_split_attack(conn) -> dict:
    actor = "split-agent"
    accepted = []
    blocked_reason = None
    for i in range(1, 7):
        try:
            result = governance.evaluate_task(
                conn,
                task_id=f"T-SPLIT-{i}",
                task_type="file_operation",
                requested_capabilities=["read_files"],
                input_source="local",
                actor_id=actor,
                projected_cost_units=5,
                actor_budget_units=20,
                idempotency_key=f"split-{i}",
            )
            accepted.append(result.token.budget_reservation_id if result.token else None)
            budget_ledger.consume_reservation(conn, result.token.budget_reservation_id)
        except ValueError as exc:
            blocked_reason = str(exc)
            break
    scope = budget_ledger.get_scope(conn, f"actor:{actor}")
    return check(
        "cross_session_split_attack",
        len(accepted) == 4 and blocked_reason in ("BUDGET_EXCEEDED", "ESCALATION_BLOCKED") and scope is not None and scope.consumed_units == 20 and scope.state == "blocked",
        {"accepted": len(accepted), "blocked_reason": blocked_reason, "scope_state": scope.state if scope else None, "consumed": scope.consumed_units if scope else None},
    )


def test_reservation_idempotency(conn) -> dict:
    budget_ledger.ensure_scope(conn, scope_id="system:idempotent", scope_type="system", allocated_units=100)
    budget_ledger.ensure_scope(conn, scope_id="actor:idempotent", scope_type="actor", parent_scope_id="system:idempotent", allocated_units=10)
    r1 = budget_ledger.reserve_budget(conn, scope_id="actor:idempotent", amount_units=3, idempotency_key="idem-1")
    r2 = budget_ledger.reserve_budget(conn, scope_id="actor:idempotent", amount_units=3, idempotency_key="idem-1")
    scope = budget_ledger.get_scope(conn, "actor:idempotent")
    return check(
        "reservation_idempotency",
        r1.reservation_id == r2.reservation_id and r2.was_duplicate and scope.reserved_units == 3,
        {"reservation_id": r1.reservation_id, "duplicate": r2.was_duplicate, "reserved_units": scope.reserved_units},
    )


def test_reservation_expiry_release(conn) -> dict:
    budget_ledger.ensure_scope(conn, scope_id="system:expiry", scope_type="system", allocated_units=100)
    budget_ledger.ensure_scope(conn, scope_id="actor:expiry", scope_type="actor", parent_scope_id="system:expiry", allocated_units=10)
    r = budget_ledger.reserve_budget(conn, scope_id="actor:expiry", amount_units=4, idempotency_key="expiry-1", ttl_seconds=60)
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    conn.execute("UPDATE budget_reservations SET expires_at = ? WHERE reservation_id = ?", (past, r.reservation_id))
    expired = budget_ledger.expire_stale_reservations(conn)
    scope = budget_ledger.get_scope(conn, "actor:expiry")
    return check("reservation_expiry_release", expired == 1 and scope.reserved_units == 0 and budget_ledger.available_units(conn, "actor:expiry") == 10)


def test_token_budget_claim_enforced(conn) -> dict:
    result = governance.evaluate_task(
        conn,
        task_id="T-TOKEN-BUDGET",
        task_type="file_operation",
        requested_capabilities=["read_files"],
        input_source="local",
        actor_id="token-agent",
        projected_cost_units=2,
        actor_budget_units=10,
        idempotency_key="token-budget",
    )
    token = result.token
    allowed = enforcement.enforce(conn, token, "read_files", "T-TOKEN-BUDGET", result.correlation_id)
    mutated = type(token)(
        token.token_id,
        token.decision_id,
        token.task_id,
        token.capabilities,
        token.issued_at,
        token.expires_at,
        token.signature,
        token.signing_key_id,
        token.budget_scope_id,
        "BRES-FORGED",
        token.max_cost_for_action,
        token.escalation_state,
    )
    rejected = enforcement.enforce(conn, mutated, "read_files", "T-TOKEN-BUDGET", result.correlation_id)
    return check("token_budget_claim_enforced", allowed.allowed and not rejected.allowed, {"reject_reason": rejected.reason})


def test_fail_closed_missing_scope(conn) -> dict:
    try:
        budget_ledger.reserve_budget(conn, scope_id="actor:missing", amount_units=1, idempotency_key="missing-1")
        ok = False
        reason = "unexpected_allow"
    except ValueError as exc:
        ok = str(exc) == "BUDGET_SCOPE_NOT_FOUND"
        reason = str(exc)
    return check("fail_closed_missing_scope", ok, {"reason": reason})


def main() -> int:
    conn, db_path = fresh_conn()
    try:
        checks = [
            test_cross_session_split_attack(conn),
            test_reservation_idempotency(conn),
            test_reservation_expiry_release(conn),
            test_token_budget_claim_enforced(conn),
            test_fail_closed_missing_scope(conn),
        ]
    finally:
        close_conn(conn, db_path)
    failed = [c for c in checks if not c["ok"]]
    print("--- cross_session_budget_evidence ---")
    for c in checks:
        print(("✓" if c["ok"] else "✗"), c["name"], c["detail"])
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed)})
    print("PASS cross_session_budget_evidence" if not failed else "FAIL cross_session_budget_evidence")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
