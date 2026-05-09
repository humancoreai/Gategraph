"""
WHY: Proves the public API contract is deterministic and machine-readable.
INV: Server responses are normalized at the adapter boundary; governance output is not reinterpreted.
SEC: Error payloads expose stable codes only, never tracebacks or ad-hoc messages.
"""
from __future__ import annotations

import http.client
import json
import tempfile
import threading
from pathlib import Path

from src import response_normalizer, service_adapter
from src.config_loader import AppConfig
from src.server import build_server

EXPECTED_TOP_KEYS = {"ok", "data", "error", "meta"}
EXPECTED_SUCCESS_DATA_KEYS = {"decision", "stage", "normalized_reason"}
EXPECTED_META_KEYS = {"schema_version", "request_id", "timestamp", "stage"}


def _request(port: int, method: str, path: str, body=None, headers=None, raw: bytes | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    payload = raw if raw is not None else (None if body is None else json.dumps(body).encode("utf-8"))
    conn.request(method, path, body=payload, headers=headers or ({"content-type": "application/json"} if payload else {}))
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    conn.close()
    return res.status, data


def _assert_base_contract(payload: dict) -> None:
    response_normalizer.assert_contract(payload)
    assert set(payload) == EXPECTED_TOP_KEYS, payload
    assert set(payload["meta"]) == EXPECTED_META_KEYS, payload
    assert payload["meta"]["schema_version"] == response_normalizer.SCHEMA_VERSION, payload
    assert isinstance(payload["meta"]["request_id"], str) and payload["meta"]["request_id"], payload
    assert isinstance(payload["meta"]["timestamp"], str) and payload["meta"]["timestamp"], payload


def _shape(payload: dict) -> dict:
    return {
        "top": sorted(payload.keys()),
        "ok": payload["ok"],
        "data": sorted(payload["data"].keys()) if isinstance(payload.get("data"), dict) else None,
        "error": sorted(payload["error"].keys()) if isinstance(payload.get("error"), dict) else None,
        "meta": sorted(payload["meta"].keys()),
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        config = AppConfig(mode="server", db_path=str(Path(tmp) / "api_contract.db"), actor_id="api-contract", session_id="api-contract-session")
        service_adapter.initialize(config)
        server = build_server("127.0.0.1", 0, config)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            task = {
                "task_id": "api-contract-valid",
                "task_type": "agent_file_operations",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
                "secrets_involved": False,
            }
            status, success = _request(port, "POST", "/evaluate", task)
            assert status == 200, success
            _assert_base_contract(success)
            assert success["ok"] is True and success["error"] is None, success
            assert set(success["data"]) == EXPECTED_SUCCESS_DATA_KEYS, success
            assert isinstance(success["data"]["normalized_reason"], dict), success

            status, error = _request(port, "POST", "/evaluate", {"task_id": "missing"})
            assert status == 400, error
            _assert_base_contract(error)
            assert error["ok"] is False and error["data"] is None, error
            assert error["error"] == {"code": "MISSING_FIELD"}, error

            status, unknown = _request(port, "POST", "/unknown", task)
            assert status == 404, unknown
            _assert_base_contract(unknown)
            assert unknown["error"] == {"code": "UNKNOWN_ENDPOINT"}, unknown

            status, method = _request(port, "DELETE", "/evaluate")
            assert status == 405, method
            _assert_base_contract(method)
            assert method["error"] == {"code": "METHOD_NOT_ALLOWED"}, method

            status, invalid_json = _request(port, "POST", "/evaluate", headers={"content-type": "application/json"}, raw=b"{bad")
            assert status == 400, invalid_json
            _assert_base_contract(invalid_json)
            assert invalid_json["error"] == {"code": "INVALID_JSON"}, invalid_json

            status, invalid_content_type = _request(port, "POST", "/evaluate", headers={"content-type": "text/plain"}, raw=b"{}")
            assert status == 415, invalid_content_type
            _assert_base_contract(invalid_content_type)
            assert invalid_content_type["error"] == {"code": "INVALID_CONTENT_TYPE"}, invalid_content_type

            status, repeat = _request(port, "POST", "/evaluate", dict(task, task_id="api-contract-valid-2"))
            assert status == 200, repeat
            _assert_base_contract(repeat)
            assert _shape(success) == _shape(repeat), (success, repeat)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    print("PASS api_contract_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
