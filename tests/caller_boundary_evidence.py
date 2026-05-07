"""
WHY: v0.9.1 makes caller-supplied security metadata explicit at the adapter boundary.
INV: Boundary validation must not infer, repair, downgrade or reclassify caller metadata.
SEC: Missing or malformed boundary metadata fails closed before governance evaluation.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config_loader import AppConfig
from src import database, service_adapter


def base_task(task_id: str = "boundary-ok") -> dict:
    return {
        "task_id": task_id,
        "task_type": "single_node_task",
        "requested_capabilities": ["read_files"],
        "input_source": "local",
        "data_sensitivity": "internal",
        "secrets_involved": False,
        "projected_cost_units": 1,
    }


def expect_boundary_reject(config: AppConfig, task: dict, expected: str) -> None:
    try:
        service_adapter.evaluate_request(config, task)
    except ValueError as exc:
        assert expected in str(exc), str(exc)
        return
    raise AssertionError("boundary request unexpectedly succeeded")


def read_event_input(db_path: str, event_id: str) -> dict:
    conn = database.get_connection(Path(db_path))
    try:
        row = conn.execute("SELECT input_json FROM events WHERE event_id = ?", (event_id,)).fetchone()
        assert row is not None, "event not found"
        return json.loads(row["input_json"])
    finally:
        conn.close()


def main() -> None:
    assert (ROOT / "TRUST_MODEL.md").exists(), "TRUST_MODEL.md missing"
    trust_model = (ROOT / "TRUST_MODEL.md").read_text(encoding="utf-8").lower()
    for term in [
        "caller-controlled",
        "trusted caller metadata",
        "does not semantically inspect",
        "does not automatically correct",
        "semantic truth verification",
    ]:
        assert term in trust_model, f"TRUST_MODEL.md missing boundary term: {term}"

    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "boundary.db")
        config = AppConfig(mode="single_node", db_path=db_path, actor_id="boundary-test", session_id="boundary-session")

        for field in ["input_source", "data_sensitivity", "secrets_involved"]:
            task = base_task(f"missing-{field}")
            task.pop(field)
            expect_boundary_reject(config, task, "missing required caller boundary field")

        malformed = base_task("malformed-secret-flag")
        malformed["secrets_involved"] = "false"
        expect_boundary_reject(config, malformed, "secrets_involved must be a boolean")

        manipulated = base_task("manipulated-caller-fields")
        manipulated["input_source"] = "caller_claimed_safe_zone"
        manipulated["data_sensitivity"] = "caller_claimed_public"
        result_one = service_adapter.evaluate_request(config, manipulated)
        result_two = service_adapter.evaluate_request(config, dict(manipulated, task_id="manipulated-caller-fields-2"))

        assert result_one["caller_boundary"]["input_source"] == "caller_claimed_safe_zone"
        assert result_one["caller_boundary"]["data_sensitivity"] == "caller_claimed_public"
        assert result_one["caller_boundary"]["automatic_reclassification"] is False
        assert result_one["caller_boundary"]["semantic_truthfulness_verified"] is False
        assert "unknown input_source" in result_one["risk_reason"]
        assert result_one["risk_level"] == result_two["risk_level"]
        assert result_one["risk_reason"] == result_two["risk_reason"]
        assert result_one["decision"] == result_two["decision"]

        event_input = read_event_input(db_path, result_one["event_id"])
        assert event_input["input_source"] == "caller_claimed_safe_zone"
        assert event_input["data_sensitivity"] == "caller_claimed_public"
        assert event_input["secrets_involved"] is False
        assert "corrected" not in json.dumps(event_input).lower()
        assert "inferred" not in json.dumps(event_input).lower()

    print("PASS caller_boundary_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")


if __name__ == "__main__":
    main()
