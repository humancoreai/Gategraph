
from __future__ import annotations

import os
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import database, governance
from src.config_loader import AppConfig
from src.runtime_path_assertions import service_adapter_context
from src.service_adapter import evaluate_request


def _conn():
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "gategraph.db"
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    database.seed_rules(conn)
    return tmp, conn


def test_direct_governance_fails_without_trusted_context() -> None:
    old = os.environ.pop("GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE", None)
    tmp, conn = _conn()
    try:
        try:
            governance.evaluate_task(
                conn,
                task_id="BT-001",
                task_type="file_operation",
                requested_capabilities=["read_files"],
                input_source="local",
            )
        except PermissionError as exc:
            assert "trusted_entry_context required" in str(exc)
        else:
            raise AssertionError("direct governance invocation unexpectedly succeeded")
    finally:
        conn.close()
        tmp.cleanup()
        if old is not None:
            os.environ["GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE"] = old


def test_service_adapter_entry_succeeds_and_audits_context() -> None:
    tmp = tempfile.TemporaryDirectory()
    try:
        config = AppConfig(db_path=str(Path(tmp.name) / "gategraph.db"))
        result = evaluate_request(
            config,
            {
                "task_id": "BT-002",
                "task_type": "file_operation",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
                "secrets_involved": False,
            },
        )
        assert result["ok"] is True
        assert result["caller_boundary"]["trust_boundary"] == "caller_supplied_metadata"

        conn = database.get_connection(Path(tmp.name) / "gategraph.db")
        row = conn.execute("SELECT input_json FROM events WHERE task_id = ?", ("BT-002",)).fetchone()
        conn.close()
        assert row is not None
        assert "trusted_entry_context" in row[0]
        assert "service_adapter" in row[0]
    finally:
        tmp.cleanup()


def test_untrusted_context_fails_closed() -> None:
    tmp, conn = _conn()
    try:
        try:
            governance.evaluate_task(
                conn,
                task_id="BT-003",
                task_type="file_operation",
                requested_capabilities=["read_files"],
                input_source="local",
                trusted_entry_context={
                    "kind": "trusted_entry_context",
                    "source_component": "external_plugin",
                    "public_entry": True,
                    "boundary_validated": True,
                    "runtime_path": "external_plugin->governance",
                    "direct_governance_call": False,
                },
            )
        except PermissionError as exc:
            assert "forbidden governance entry component" in str(exc)
        else:
            raise AssertionError("untrusted context unexpectedly succeeded")
    finally:
        conn.close()
        tmp.cleanup()


def test_explicit_service_context_allows_internal_call() -> None:
    tmp, conn = _conn()
    try:
        result = governance.evaluate_task(
            conn,
            task_id="BT-004",
            task_type="file_operation",
            requested_capabilities=["read_files"],
            input_source="local",
            trusted_entry_context=service_adapter_context(),
        )
        assert result.final_decision in {"allow", "warn", "require_review", "deny"}
    finally:
        conn.close()
        tmp.cleanup()


def main() -> int:
    tests = [
        test_direct_governance_fails_without_trusted_context,
        test_service_adapter_entry_succeeds_and_audits_context,
        test_untrusted_context_fails_closed,
        test_explicit_service_context_allows_internal_call,
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
