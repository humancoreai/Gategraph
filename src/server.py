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


class GateGraphHandler(BaseHTTPRequestHandler):
    server_version = "GateGraphHTTP/0.8.33"

    def do_GET(self) -> None:
        if self.path == "/status":
            self._send_json(HTTPStatus.OK, service_adapter.status(self._config()))
            return
        if self.path == "/monitoring":
            self._send_json(HTTPStatus.OK, {"ok": True, "monitoring": service_adapter.monitoring(self._config())})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "unknown endpoint"})

    def do_POST(self) -> None:
        if self.path != "/evaluate":
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "unknown endpoint"})
            return
        try:
            self._send_json(HTTPStatus.OK, service_adapter.evaluate_request(self._config(), self._read_json_body()))
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})

    def do_PUT(self) -> None:
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "error": "method not allowed"})

    def do_DELETE(self) -> None:
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "error": "method not allowed"})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _config(self) -> AppConfig:
        return self.server.gategraph_config  # type: ignore[attr-defined]

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            raise ValueError("empty request body")
        if length > MAX_BODY_BYTES:
            raise ValueError("request body too large")
        if "application/json" not in self.headers.get("content-type", "").lower():
            raise ValueError("content-type must be application/json")
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")
        return data

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
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
