"""
WHY: v0.10.1 ties selected freeze invariants to executable runtime boundary checks.
INV: Freeze evidence must fail if runtime entry-boundary behavior drifts.
SEC: Documentation-only freeze claims are not enough for direct-call boundary safety.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import database, governance
from src.config_loader import AppConfig
from src.service_adapter import evaluate_request



def _conn():
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "gategraph.db"
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    database.seed_rules(conn)
    return tmp, conn


def test_freeze_registry_contains_boundary_invariants() -> None:
    registry = (ROOT / "docs" / "INVARIANT_REGISTRY.md").read_text(encoding="utf-8")
    assert "INV-001" in registry
    assert "INV-002" in registry
    assert "INV-015" in registry
    assert re.search(r"INV-0\d+", registry), "no invariant IDs found"


def test_freeze_snapshot_references_runtime_boundary_hardening() -> None:
    freeze = (ROOT / "docs" / "GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md").read_text(encoding="utf-8")
    runtime_doc = (ROOT / "docs" / "RUNTIME_BOUNDARY_HARDENING.md").read_text(encoding="utf-8")
    assert "trusted entry" in runtime_doc.lower()
    assert "service_adapter" in runtime_doc
    assert "governance" in runtime_doc.lower()
    assert "docs/INVARIANT_REGISTRY.md" in freeze


def test_runtime_blocks_naked_governance_entry_by_default() -> None:
    old = os.environ.pop("GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE", None)
    tmp, conn = _conn()
    try:
        try:
            governance.evaluate_task(
                conn,
                task_id="FRZ-001",
                task_type="file_operation",
                requested_capabilities=["read_files"],
                input_source="local",
            )
        except PermissionError as exc:
            assert "trusted_entry_context required" in str(exc)
        else:
            raise AssertionError("freeze runtime invariant failed: naked governance entry succeeded")
    finally:
        conn.close()
        tmp.cleanup()
        if old is not None:
            os.environ["GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE"] = old


def test_runtime_allows_only_declared_public_entry() -> None:
    tmp = tempfile.TemporaryDirectory()
    try:
        config = AppConfig(db_path=str(Path(tmp.name) / "gategraph.db"))
        result = evaluate_request(
            config,
            {
                "task_id": "FRZ-002",
                "task_type": "file_operation",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
                "secrets_involved": False,
            },
        )
        assert result["ok"] is True
        assert result["event_id"]
    finally:
        tmp.cleanup()


def main() -> int:
    tests = [
        test_freeze_registry_contains_boundary_invariants,
        test_freeze_snapshot_references_runtime_boundary_hardening,
        test_runtime_blocks_naked_governance_entry_by_default,
        test_runtime_allows_only_declared_public_entry,
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
