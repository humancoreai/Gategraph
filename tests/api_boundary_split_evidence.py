"""
WHY: v0.10.1 makes the internal/public API split executable rather than implicit.
INV: service_adapter is the only public evaluation entry; Governance is internal.
SEC: Agent, plugin, framework, UI or unknown components may not enter Governance directly.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import database, governance
from src.api_boundary import classify_component
from src.config_loader import AppConfig
from src.runtime_path_assertions import service_adapter_context, test_harness_context
from src.service_adapter import evaluate_request


def _conn():
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "gategraph.db"
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    database.seed_rules(conn)
    return tmp, conn


def test_public_internal_forbidden_classification() -> None:
    assert classify_component("service_adapter").boundary_class == "public"
    assert classify_component("governance").boundary_class == "internal"
    assert classify_component("test_harness").boundary_class == "internal"
    for component in ["external_plugin", "framework_adapter", "agent_runtime", "operator_ui", "unknown"]:
        assert classify_component(component).boundary_class == "forbidden", component


def test_only_service_adapter_public_entry_succeeds() -> None:
    tmp = tempfile.TemporaryDirectory()
    try:
        config = AppConfig(db_path=str(Path(tmp.name) / "gategraph.db"))
        result = evaluate_request(
            config,
            {
                "task_id": "API-B-001",
                "task_type": "file_operation",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
                "secrets_involved": False,
            },
        )
        assert result["ok"] is True
        conn = database.get_connection(Path(tmp.name) / "gategraph.db")
        row = conn.execute("SELECT input_json FROM events WHERE event_id = ?", (result["event_id"],)).fetchone()
        conn.close()
        event_input = json.loads(row["input_json"])
        ctx = event_input["trusted_entry_context"]
        assert ctx["source_component"] == "service_adapter"
        assert ctx["boundary_class"] == "public"
        assert ctx["runtime_path"] == "public_api->service_adapter->governance"
    finally:
        tmp.cleanup()


def test_internal_governance_component_cannot_fake_public_entry() -> None:
    tmp, conn = _conn()
    try:
        try:
            governance.evaluate_task(
                conn,
                task_id="API-B-002",
                task_type="file_operation",
                requested_capabilities=["read_files"],
                input_source="local",
                trusted_entry_context={
                    "kind": "trusted_entry_context",
                    "source_component": "governance",
                    "public_entry": True,
                    "boundary_validated": True,
                    "runtime_path": "public_api->governance",
                    "direct_governance_call": False,
                },
            )
        except PermissionError as exc:
            assert "public governance entry must pass through service_adapter" in str(exc)
        else:
            raise AssertionError("internal component unexpectedly acted as public entry")
    finally:
        conn.close()
        tmp.cleanup()


def test_forbidden_components_fail_closed() -> None:
    tmp, conn = _conn()
    try:
        for component in ["framework_adapter", "agent_runtime", "operator_ui", "unknown"]:
            try:
                governance.evaluate_task(
                    conn,
                    task_id=f"API-B-FORBID-{component}",
                    task_type="file_operation",
                    requested_capabilities=["read_files"],
                    input_source="local",
                    trusted_entry_context={
                        "kind": "trusted_entry_context",
                        "source_component": component,
                        "public_entry": True,
                        "boundary_validated": True,
                        "runtime_path": f"{component}->governance",
                        "direct_governance_call": False,
                    },
                )
            except PermissionError as exc:
                assert "forbidden governance entry component" in str(exc), str(exc)
            else:
                raise AssertionError(f"forbidden component unexpectedly succeeded: {component}")
    finally:
        conn.close()
        tmp.cleanup()


def test_test_harness_direct_path_is_env_gated() -> None:
    old = os.environ.pop("GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE", None)
    tmp, conn = _conn()
    try:
        try:
            governance.evaluate_task(
                conn,
                task_id="API-B-003",
                task_type="file_operation",
                requested_capabilities=["read_files"],
                input_source="local",
                trusted_entry_context=test_harness_context(),
            )
        except PermissionError as exc:
            assert "direct governance invocation is not a production entry path" in str(exc)
        else:
            raise AssertionError("test harness path succeeded without env gate")

        os.environ["GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE"] = "1"
        result = governance.evaluate_task(
            conn,
            task_id="API-B-004",
            task_type="file_operation",
            requested_capabilities=["read_files"],
            input_source="local",
            trusted_entry_context=test_harness_context(),
        )
        assert result.final_decision in {"allow", "warn", "require_review", "deny"}
    finally:
        conn.close()
        tmp.cleanup()
        os.environ.pop("GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE", None)
        if old is not None:
            os.environ["GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE"] = old


def main() -> int:
    tests = [
        test_public_internal_forbidden_classification,
        test_only_service_adapter_public_entry_succeeds,
        test_internal_governance_component_cannot_fake_public_entry,
        test_forbidden_components_fail_closed,
        test_test_harness_direct_path_is_env_gated,
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
