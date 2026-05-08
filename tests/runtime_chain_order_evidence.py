"""
WHY: v0.10.3 proves the guard chain/order invariant with executable skipped-stage checks.
INV: action_ready requires Enforcement -> Flood Guard -> Session Budget -> Runtime Guard -> action_ready.
SEC: invalid enforcement chains fail closed before later guards can be treated as valid.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import database, guard_orchestrator, runtime_guard, session_budget_guard
from src.runtime_chain_assertions import RUNTIME_CHAIN_ORDER, assert_runtime_chain


def _conn():
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "gategraph.db"
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    database.seed_rules(conn)
    database.ensure_runtime_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    return tmp, conn


def _must_fail(fn, expected: str) -> None:
    try:
        fn()
    except PermissionError as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError(f"expected PermissionError containing: {expected}")


def test_valid_complete_chain_allows_action_ready() -> None:
    assertion = assert_runtime_chain(
        evaluated_stages=RUNTIME_CHAIN_ORDER,
        terminal_stage="action_ready",
        enforcement_allowed=True,
    )
    assert assertion.action_ready is True
    assert assertion.evaluated_stages == RUNTIME_CHAIN_ORDER


def test_skipped_stage_fails_closed() -> None:
    _must_fail(
        lambda: assert_runtime_chain(
            evaluated_stages=("enforcement", "session_budget"),
            terminal_stage="session_budget",
            enforcement_allowed=True,
        ),
        "skipped stage",
    )


def test_action_ready_without_runtime_guard_fails_closed() -> None:
    _must_fail(
        lambda: assert_runtime_chain(
            evaluated_stages=("enforcement", "flood_guard", "session_budget", "action_ready"),
            terminal_stage="action_ready",
            enforcement_allowed=True,
        ),
        "skipped stage",
    )


def test_downstream_after_enforcement_denied_fails_closed() -> None:
    _must_fail(
        lambda: assert_runtime_chain(
            evaluated_stages=("enforcement", "flood_guard"),
            terminal_stage="flood_guard",
            enforcement_allowed=False,
        ),
        "invalid enforcement chain",
    )


def test_guard_orchestrator_records_ordered_chain_for_action_ready() -> None:
    tmp, conn = _conn()
    try:
        session_budget_guard.create_session_budget(
            conn,
            session_id="CHAIN-OK",
            max_session_cost_units=100,
            max_session_tasks=10,
            max_agent_cost_units=100,
        )
        runtime_guard.create_budget(conn, task_id="CHAIN-TASK", max_steps=5, max_cost_units=100)
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=True,
            enforcement_reason="allowed",
            session_id="CHAIN-OK",
            task_id="CHAIN-TASK",
            actor_id="agent-a",
            action_type="model_call",
            target="x",
            projected_cost_units=1,
        )
        assert decision.decision == "continue"
        assert decision.stage == "action_ready"
        assert decision.evaluated_stages == RUNTIME_CHAIN_ORDER
        assert decision.runtime_chain_assertion["action_ready"] is True
    finally:
        conn.close()
        tmp.cleanup()


def test_guard_orchestrator_records_enforcement_stop_prefix_only() -> None:
    tmp, conn = _conn()
    try:
        decision = guard_orchestrator.evaluate_guard_pipeline(
            conn,
            enforcement_allowed=False,
            enforcement_reason="no capability token provided",
            session_id="CHAIN-BLOCK",
            task_id="CHAIN-BLOCK-TASK",
            actor_id="agent-a",
            action_type="model_call",
            target="x",
            projected_cost_units=1,
        )
        assert decision.decision == "stop"
        assert decision.stage == "enforcement"
        assert decision.evaluated_stages == ("enforcement",)
        assert decision.runtime_chain_assertion["action_ready"] is False
    finally:
        conn.close()
        tmp.cleanup()


def main() -> int:
    tests = [
        test_valid_complete_chain_allows_action_ready,
        test_skipped_stage_fails_closed,
        test_action_ready_without_runtime_guard_fails_closed,
        test_downstream_after_enforcement_denied_fails_closed,
        test_guard_orchestrator_records_ordered_chain_for_action_ready,
        test_guard_orchestrator_records_enforcement_stop_prefix_only,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"✗ {test.__name__}: {type(exc).__name__}: {exc}")
    print(f"Summary: {{'passed': {len(tests) - failed}, 'failed': {failed}}}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
