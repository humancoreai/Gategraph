"""
WHY: Proves Phase 3 server hardening without changing governance behavior.
INV: The server remains an adapter; hardening validates the boundary only.
SEC: malformed inputs, unsafe methods, oversized bodies, and HTML errors fail closed.
"""
from __future__ import annotations

import http.client
import json
import tempfile
import threading
from pathlib import Path

from src.config_loader import AppConfig
from src.server import MAX_BODY_BYTES, build_server
from src import service_adapter


def _request(port: int, method: str, path: str, body=None, headers=None, raw: bytes | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    if raw is not None:
        payload = raw
    elif body is None:
        payload = None
    else:
        payload = json.dumps(body).encode("utf-8")
    conn.request(method, path, body=payload, headers=headers or ({"content-type": "application/json"} if payload else {}))
    res = conn.getresponse()
    raw_data = res.read().decode("utf-8")
    data = json.loads(raw_data)
    conn.close()
    return res.status, res.getheader("content-type"), data


def _assert_error(status: int, data: dict, expected_status: int, expected_code: str) -> None:
    assert status == expected_status, data
    assert data["ok"] is False, data
    assert data["error"]["code"] == expected_code, data
    assert "message" in data["error"], data
    assert "stage" in data, data
    assert "Traceback" not in json.dumps(data), data


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "server_hardening.db")
        config = AppConfig(mode="server", db_path=db, actor_id="server-hardening", session_id="server-hardening-session")
        service_adapter.initialize(config)
        server = build_server("127.0.0.1", 0, config)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            valid_task = {
                "task_id": "server-hardening-valid",
                "task_type": "agent_file_operations",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
            }
            status, content_type, data = _request(port, "POST", "/evaluate", valid_task)
            assert status == 200 and content_type and content_type.startswith("application/json"), data
            assert data["ok"] is True and "decision" in data, data

            status_before, _, before = _request(port, "GET", "/status")
            assert status_before == 200 and before["ok"] is True, before
            _request(port, "GET", "/monitoring")
            _request(port, "GET", "/status")
            status_after, _, after = _request(port, "GET", "/status")
            assert status_after == 200 and after["counts"] == before["counts"], (before, after)

            error_cases = [
                ("POST", "/evaluate", None, {"content-type": "text/plain"}, b"{}", 415, "invalid_content_type"),
                ("POST", "/evaluate", None, {"content-type": "application/json"}, b"{bad", 400, "invalid_json"),
                ("POST", "/evaluate", {"task_id": "missing"}, None, None, 400, "missing_required_fields"),
                ("POST", "/evaluate", dict(valid_task, requested_capabilities="read_files"), None, None, 400, "invalid_requested_capabilities"),
                ("POST", "/evaluate", None, {"content-type": "application/json"}, b"{" + (b" " * (MAX_BODY_BYTES + 1)), 413, "body_too_large"),
                ("POST", "/unknown", valid_task, None, None, 404, "unknown_endpoint"),
                ("DELETE", "/evaluate", None, None, None, 405, "method_not_allowed"),
                ("PATCH", "/evaluate", None, None, None, 405, "method_not_allowed"),
            ]
            for method, path, body, headers, raw, expected_status, expected_code in error_cases:
                status, content_type, data = _request(port, method, path, body=body, headers=headers, raw=raw)
                assert content_type and content_type.startswith("application/json"), (method, path, content_type, data)
                _assert_error(status, data, expected_status, expected_code)

        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    print("PASS server_hardening_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
