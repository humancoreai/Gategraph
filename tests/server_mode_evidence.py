"""
WHY: Proves server mode is an adapter over the same evaluation path as CLI/service code.
INV: The server test must not introduce special server-side decisions.
SEC: invalid methods/endpoints and malformed bodies fail closed.
"""
from __future__ import annotations

import http.client
import json
import tempfile
import threading
from pathlib import Path

from src.config_loader import AppConfig
from src.server import build_server
from src import service_adapter


def _request(port: int, method: str, path: str, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    payload = None if body is None else json.dumps(body).encode("utf-8")
    conn.request(method, path, body=payload, headers=headers or ({"content-type": "application/json"} if payload else {}))
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    conn.close()
    return res.status, data


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "server_mode.db")
        config = AppConfig(mode="server", db_path=db, actor_id="server-test", session_id="server-session")
        server = build_server("127.0.0.1", 0, config)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            task = {
                "task_id": "server-eval-read",
                "task_type": "agent_file_operations",
                "requested_capabilities": ["read_files"],
                "input_source": "local",
                "data_sensitivity": "internal",
            }
            expected = service_adapter.evaluate_request(config, dict(task, task_id="direct-eval-read"))
            status, actual = _request(port, "POST", "/evaluate", task)
            assert status == 200, actual
            assert actual["ok"] is True
            assert actual["data"]["decision"] == expected["decision"]
            assert actual["data"]["normalized_reason"]["risk_level"] == expected["risk_level"]
            assert actual["data"]["normalized_reason"]["selected_rule_id"] == expected["selected_rule_id"]
            assert actual["data"]["normalized_reason"]["matched_rule_ids"] == expected["matched_rule_ids"]

            status, data = _request(port, "GET", "/status")
            assert status == 200 and data["ok"] is True and "counts" in data["data"]

            status, data = _request(port, "GET", "/monitoring")
            assert status == 200 and data["ok"] is True and "summary" in data["data"]["monitoring"]

            status, data = _request(port, "DELETE", "/evaluate")
            assert status == 405 and data["ok"] is False

            status, data = _request(port, "POST", "/evaluate", {"requested_capabilities": "read_files"})
            assert status == 400 and data["ok"] is False
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    print("PASS server_mode_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
