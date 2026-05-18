"""
WHY: server.py exposes GateGraph as a minimal HTTP adapter for integrations.
INV: Server mode never decides; /evaluate calls service_adapter, which calls governance.py.
SEC: only explicit endpoints are exposed, request bodies are bounded, and errors fail closed.
"""
from __future__ import annotations

import argparse
import json
import socket
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from src import response_normalizer, service_adapter
from src.config_loader import AppConfig, load_config

MAX_BODY_BYTES = 64 * 1024
REQUIRED_EVALUATE_FIELDS = {"task_id", "task_type", "requested_capabilities", "input_source", "data_sensitivity", "secrets_involved"}


class RequestValidationError(ValueError):
    def __init__(self, code: str, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST, stage: str = "request_validation"):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.stage = stage


class GateGraphHandler(BaseHTTPRequestHandler):
    server_version = "v0.17.5_STABLE"

    def setup(self) -> None:
        super().setup()
        # SEC: Bound malformed or truncated reads so worker threads do not linger.
        self.request.settimeout(2.0)


    def do_GET(self) -> None:
        if self.path == "/status":
            self._send_json(HTTPStatus.OK, response_normalizer.wrap_data(service_adapter.status(self._config()), stage="server"))
            return
        if self.path == "/monitoring":
            self._send_json(HTTPStatus.OK, response_normalizer.wrap_data({"monitoring": service_adapter.monitoring(self._config())}, stage="server"))
            return
        self._send_error(HTTPStatus.NOT_FOUND, "UNKNOWN_ENDPOINT", "routing")

    def do_POST(self) -> None:
        if self.path != "/evaluate":
            self._send_error(HTTPStatus.NOT_FOUND, "UNKNOWN_ENDPOINT", "routing")
            return
        try:
            body = self._read_json_body()
            self._validate_evaluate_body(body)
            self._send_json(HTTPStatus.OK, response_normalizer.success(self._evaluate_serialized(body), stage="core"))
        except RequestValidationError as exc:
            self._send_error(exc.status, exc.code, exc.stage)
        except Exception:
            # SEC: Do not expose stack traces or internal exception details across the service boundary.
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "server")

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def do_OPTIONS(self) -> None:
        self._method_not_allowed()

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:  # type: ignore[override]
        # SEC: BaseHTTPRequestHandler would emit HTML. Keep every failure JSON and fail-closed.
        self._send_error(HTTPStatus(code), "METHOD_NOT_ALLOWED", "routing")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _config(self) -> AppConfig:
        return self.server.gategraph_config  # type: ignore[attr-defined]

    def _method_not_allowed(self) -> None:
        self._send_error(HTTPStatus.METHOD_NOT_ALLOWED, "METHOD_NOT_ALLOWED", "routing")

    def _read_json_body(self) -> dict[str, Any]:
        raw_length = self.headers.get("content-length")
        try:
            length = int(raw_length or "0")
        except ValueError:
            raise RequestValidationError("INVALID_JSON", "content-length must be an integer") from None
        if length <= 0:
            raise RequestValidationError("INVALID_JSON", "request body must not be empty")
        if length > MAX_BODY_BYTES:
            # SEC: Reject oversize bodies before parsing; close makes teardown deterministic.
            self.close_connection = True
            raise RequestValidationError("PAYLOAD_TOO_LARGE", "request body too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        if "application/json" not in self.headers.get("content-type", "").lower():
            raise RequestValidationError("INVALID_CONTENT_TYPE", "content-type must be application/json", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        try:
            raw = self.rfile.read(length)
        except (TimeoutError, socket.timeout, OSError):
            self.close_connection = True
            raise RequestValidationError("INVALID_JSON", "request body was not fully received") from None
        if len(raw) != length:
            self.close_connection = True
            raise RequestValidationError("INVALID_JSON", "request body was not fully received")
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise RequestValidationError("INVALID_JSON", "request body must be valid JSON") from None
        if not isinstance(data, dict):
            raise RequestValidationError("INVALID_JSON", "request body must be a JSON object")
        return data

    def _evaluate_serialized(self, body: dict[str, Any]) -> dict[str, Any]:
        # INV: Adapter-level serialization protects the single SQLite node without changing governance.
        with self.server.evaluate_lock:  # type: ignore[attr-defined]
            return service_adapter.evaluate_request(self._config(), body)

    def _validate_evaluate_body(self, body: dict[str, Any]) -> None:
        missing = sorted(REQUIRED_EVALUATE_FIELDS - set(body))
        if missing:
            raise RequestValidationError("MISSING_FIELD", f"missing required fields: {missing}")
        if not isinstance(body.get("requested_capabilities"), list):
            raise RequestValidationError("INVALID_JSON", "requested_capabilities must be a list")
        if "projected_cost_units" in body:
            try:
                projected = int(body["projected_cost_units"])
            except (TypeError, ValueError):
                raise RequestValidationError("INVALID_JSON", "projected_cost_units must be an integer") from None
            if projected <= 0:
                raise RequestValidationError("INVALID_JSON", "projected_cost_units must be positive")

    def _send_error(self, status: HTTPStatus, code: str, stage: str) -> None:
        self._send_json(status, response_normalizer.error(code, stage=stage))

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(int(status))
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.send_header("connection", "close")
        try:
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, TimeoutError, socket.timeout, OSError):
            # EDGE: Client aborts are transport failures, not governance failures.
            self.close_connection = True
            return
        self.close_connection = True


class GateGraphHTTPServer(ThreadingHTTPServer):
    # SEC: Local adapter hardening only; this is not an internet-facing connection limiter.
    daemon_threads = True
    request_queue_size = 16


def build_server(host: str, port: int, config: AppConfig) -> ThreadingHTTPServer:
    server = GateGraphHTTPServer((host, port), GateGraphHandler)
    server.gategraph_config = config  # type: ignore[attr-defined]
    server.evaluate_lock = threading.Lock()  # type: ignore[attr-defined]
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gategraph-server", description="GateGraph minimal server adapter")
    parser.add_argument("--config", default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    if args.host in {"0.0.0.0", "::"}:
        print("WARNING: public bind requested; use only behind an explicitly protected boundary.", flush=True)
    config = load_config(args.config)
    server = build_server(args.host, args.port, config)
    try:
        print(json.dumps({"ok": True, "host": args.host, "port": args.port, "mode": config.mode}, indent=2), flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Release surface: GateGraphHTTP/v0.17.5_STABLE

# HTTP compatibility surface: GateGraphHTTP/0.14.9
