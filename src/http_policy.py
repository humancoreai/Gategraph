"""
WHY: outbound HTTP integrations need a deterministic allowlist before any transport side effect.
INV: network-capable endpoints are fail-closed unless an active policy explicitly allows host/path/method.
SEC: policy evaluation happens after Enforcement/Guards but before secret resolution and transport execution.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_ALLOWED_SCHEMES = {"https"}


@dataclass(frozen=True)
class HTTPPolicy:
    policy_id: str
    allowed_host: str
    allowed_path_prefixes: List[str]
    allowed_methods: List[str]
    active: bool


@dataclass(frozen=True)
class HTTPPolicyDecision:
    allowed: bool
    reason: str
    policy_id: Optional[str] = None


def ensure_http_policy_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_endpoint_policies (
            policy_id TEXT PRIMARY KEY,
            allowed_host TEXT NOT NULL,
            allowed_path_prefixes TEXT NOT NULL,
            allowed_methods TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_endpoint_policies_active ON api_endpoint_policies(active)")
    conn.commit()


def register_api_endpoint_policy(
    conn: sqlite3.Connection,
    *,
    policy_id: str,
    allowed_host: str,
    allowed_path_prefixes: List[str],
    allowed_methods: List[str],
    active: bool = True,
) -> HTTPPolicy:
    ensure_http_policy_schema(conn)
    host = (allowed_host or "").strip().lower()
    if not host or "/" in host or ":" in host:
        raise ValueError("allowed_host must be a bare lowercase host, without scheme, path, or port")
    prefixes = [p.strip() for p in allowed_path_prefixes if isinstance(p, str) and p.strip().startswith("/")]
    if not prefixes:
        raise ValueError("at least one path prefix starting with '/' is required")
    methods = sorted({m.strip().upper() for m in allowed_methods if isinstance(m, str) and m.strip()})
    if not methods or not set(methods).issubset(_ALLOWED_METHODS):
        raise ValueError(f"allowed_methods must be a subset of {sorted(_ALLOWED_METHODS)}")
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO api_endpoint_policies
              (policy_id, allowed_host, allowed_path_prefixes, allowed_methods, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (policy_id, host, json.dumps(prefixes), json.dumps(methods), 1 if active else 0, now),
        )
    return HTTPPolicy(policy_id, host, prefixes, methods, active)


def evaluate_http_policy(conn: sqlite3.Connection, *, endpoint: str, method: str) -> HTTPPolicyDecision:
    """
    Returns allow only for explicitly registered HTTPS host/path/method combinations.
    Relative /mock endpoints are treated as local deterministic mocks, not outbound HTTP.
    """
    ensure_http_policy_schema(conn)
    ep = (endpoint or "").strip()
    meth = (method or "").strip().upper()
    if ep.startswith("/mock/"):
        return HTTPPolicyDecision(True, "local mock endpoint allowed", policy_id="local-mock")
    if meth not in _ALLOWED_METHODS:
        return HTTPPolicyDecision(False, f"http method not allowed: {method}")

    parsed = urlparse(ep)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return HTTPPolicyDecision(False, f"http scheme not allowed: {parsed.scheme or 'missing'}")
    if not parsed.hostname:
        return HTTPPolicyDecision(False, "http host missing")
    host = parsed.hostname.lower()
    path = parsed.path or "/"

    rows = conn.execute(
        "SELECT * FROM api_endpoint_policies WHERE active = 1 AND allowed_host = ?",
        (host,),
    ).fetchall()
    for row in rows:
        prefixes = list(json.loads(row["allowed_path_prefixes"]))
        methods = list(json.loads(row["allowed_methods"]))
        if meth in methods and any(path.startswith(prefix) for prefix in prefixes):
            return HTTPPolicyDecision(True, "http policy allowed", policy_id=row["policy_id"])
    return HTTPPolicyDecision(False, f"http endpoint not allowlisted: {host}{path}")
