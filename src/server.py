"""
WHY: server.py exposes GateGraph as a minimal HTTP adapter for integrations.
INV: Server mode never decides; /evaluate calls service_adapter, which calls governance.py.
SEC: only explicit endpoints are exposed, request bodies are bounded, and errors fail closed.
"""
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from src import service_adapter
from src.config_loader import AppConfig, load_config

MAX_BODY_BYTES = 64 * 1024
REQUIRED_EVALUATE_FIELDS = {"task_id", "task_type", "requested_capabilities", "input_source", "data_sensitivity"}


class RequestValidationError(ValueError):
    def __init__(self, code: str, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST, stage: str = "request_validation"):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.stage = stage


class GateGraphHandler(BaseHTTPRequestHandler):
    server_version = "GateGraphHTTP/0.8.34"

    def do_GET(self) -> None:
        if self.path == "/status":
            self._send_json(HTTPStatus.OK, service_adapter.status(self._config()))
            return
        if self.path == "/monitoring":
            self._send_json(HTTPStatus.OK, {"ok": True, "monitoring": service_adapter.monitoring(self._config())})
            return
        self._send_error(HTTPStatus.NOT_FOUND, "unknown_endpoint", "unknown endpoint", "routing")

    def do_POST(self) -> None:
        if self.path != "/evaluate":
            self._send_error(HTTPStatus.NOT_FOUND, "unknown_endpoint", "unknown endpoint", "routing")
            return
        try:
            body = self._read_json_body()
            self._validate_evaluate_body(body)
            self._send_json(HTTPStatus.OK, service_adapter.evaluate_request(self._config(), body))
        except RequestValidationError as exc:
            self._send_error(exc.status, exc.code, exc.message, exc.stage)
        except Exception:
            # SEC: Do not expose stack traces or internal exception details across the service boundary.
            self._send_error(HTTPStatus.BAD_REQUEST, "evaluation_failed", "request could not be evaluated", "service_adapter")

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
        self._send_error(HTTPStatus(code), "unsupported_method", "method not allowed", "routing")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _config(self) -> AppConfig:
        return self.server.gategraph_config  # type: ignore[attr-defined]

    def _method_not_allowed(self) -> None:
        self._send_error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "method not allowed", "routing")

    def _read_json_body(self) -> dict[str, Any]:
        raw_length = self.headers.get("content-length")
        try:
            length = int(raw_length or "0")
        except ValueError:
            raise RequestValidationError("invalid_content_length", "content-length must be an integer") from None
        if length <= 0:
            raise RequestValidationError("empty_body", "request body must not be empty")
        if length > MAX_BODY_BYTES:
            raise RequestValidationError("body_too_large", "request body too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        if "application/json" not in self.headers.get("content-type", "").lower():
            raise RequestValidationError("invalid_content_type", "content-type must be application/json", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise RequestValidationError("invalid_json", "request body must be valid JSON") from None
        if not isinstance(data, dict):
            raise RequestValidationError("invalid_json_root", "request body must be a JSON object")
        return data

    def _validate_evaluate_body(self, body: dict[str, Any]) -> None:
        missing = sorted(REQUIRED_EVALUATE_FIELDS - set(body))
        if missing:
            raise RequestValidationError("missing_required_fields", f"missing required fields: {missing}")
        if not isinstance(body.get("requested_capabilities"), list):
            raise RequestValidationError("invalid_requested_capabilities", "requested_capabilities must be a list")
        if "projected_cost_units" in body:
            try:
                projected = int(body["projected_cost_units"])
            except (TypeError, ValueError):
                raise RequestValidationError("invalid_projected_cost", "projected_cost_units must be an integer") from None
            if projected <= 0:
                raise RequestValidationError("invalid_projected_cost", "projected_cost_units must be positive")

    def _send_error(self, status: HTTPStatus, code: str, message: str, stage: str) -> None:
        self._send_json(status, {"ok": False, "error": {"code": code, "message": message}, "stage": stage})

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(int(status))
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def build_server(host: str, port: int, config: AppConfig) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), GateGraphHandler)
    server.gategraph_config = config  # type: ignore[attr-defined]
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
