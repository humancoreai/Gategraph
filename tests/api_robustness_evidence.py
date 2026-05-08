"""
WHY: Phase 5 proves the HTTP adapter stays deterministic under realistic edge pressure.
INV: These tests must not require API schema changes or governance-core changes.
SEC: malformed transport/input cases must fail closed with normalized JSON errors.
"""
from __future__ import annotations

import http.client
import json
import os
import socket
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src import response_normalizer, service_adapter
from src.config_loader import AppConfig
from src.server import MAX_BODY_BYTES, build_server


VALID_TASK = {
    "task_id": "api-robustness-valid",
    "task_type": "agent_file_operations",
    "requested_capabilities": ["read_files"],
    "input_source": "local",
    "data_sensitivity": "internal",
    "secrets_involved": False,
}


def _request(port: int, method: str = "POST", path: str = "/evaluate", body=None, headers=None, raw: bytes | None = None, timeout: float = 5.0):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    payload = raw if raw is not None else (None if body is None else json.dumps(body).encode("utf-8"))
    conn.request(method, path, body=payload, headers=headers or ({"content-type": "application/json"} if payload else {}))
    res = conn.getresponse()
    text = res.read().decode("utf-8")
    conn.close()
    data = json.loads(text)
    response_normalizer.assert_contract(data)
    return res.status, data


def _shape(payload: dict) -> dict:
    data = payload.get("data")
    error = payload.get("error")
    return {
        "top": sorted(payload.keys()),
        "ok": payload.get("ok"),
        "data_keys": sorted(data.keys()) if isinstance(data, dict) else None,
        "error_keys": sorted(error.keys()) if isinstance(error, dict) else None,
        "error_code": error.get("code") if isinstance(error, dict) else None,
        "meta_keys": sorted(payload.get("meta", {}).keys()),
        "meta_stage": payload.get("meta", {}).get("stage"),
        "schema_version": payload.get("meta", {}).get("schema_version"),
    }


def _abort_request(port: int) -> None:
    sock = socket.create_connection(("127.0.0.1", port), timeout=2)
    sock.close()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        config = AppConfig(mode="server", db_path=str(Path(tmp) / "api_robustness.db"), actor_id="api-robustness", session_id="api-robustness-session")
        service_adapter.initialize(config)
        server = build_server("127.0.0.1", 0, config)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = [pool.submit(_request, port, body=dict(VALID_TASK, task_id=f"api-robustness-parallel-{i}")) for i in range(12)]
                parallel = [future.result() for future in as_completed(futures)]
            assert len(parallel) == 12, parallel
            for status, payload in parallel:
                assert status == 200, payload
                assert payload["ok"] is True, payload
            assert len({_shape(payload).__repr__() for _, payload in parallel}) == 1, parallel

            large_body = b'{"x":"' + (b"a" * (MAX_BODY_BYTES + 1)) + b'"}'
            status, too_large = _request(port, raw=large_body, headers={"content-type": "application/json"})
            assert status == 413, too_large
            assert too_large["error"] == {"code": "PAYLOAD_TOO_LARGE"}, too_large

            status, invalid_json = _request(port, raw=b'{"task_id":', headers={"content-type": "application/json"})
            assert status == 400, invalid_json
            assert invalid_json["error"] == {"code": "INVALID_JSON"}, invalid_json

            status, invalid_type = _request(port, raw=b"{}", headers={"content-type": "text/plain"})
            assert status == 415, invalid_type
            assert invalid_type["error"] == {"code": "INVALID_CONTENT_TYPE"}, invalid_type

            baseline_status, baseline = _request(port, body=dict(VALID_TASK, task_id="api-robustness-baseline"))
            assert baseline_status == 200, baseline
            _abort_request(port)
            time.sleep(0.2)
            after_status, after_abort = _request(port, body=dict(VALID_TASK, task_id="api-robustness-after-abort"))
            assert after_status == 200, after_abort
            assert _shape(baseline) == _shape(after_abort), (baseline, after_abort)
        finally:
            pass

    print("PASS api_robustness_evidence", flush=True)
    print("Summary: {'passed': 1, 'failed': 0}", flush=True)
    os._exit(0)


if __name__ == "__main__":
    rc = main()
    os._exit(rc)
