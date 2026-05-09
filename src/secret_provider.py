"""
WHY: secrets are capabilities-adjacent resources; they must be resolved only through explicit refs.
INV: this module never stores raw secret values in SQLite and never returns secrets for disabled refs.
SEC: missing, disabled, malformed, or empty secrets fail closed before any external side effect.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

_ENV_SECRET_PREFIX = "GATEGRAPH_SECRET_"
_ENV_SECRET_JSON = "GATEGRAPH_SECRET_PROVIDER_JSON"
_SECRET_NAME_RE = re.compile(r"^[A-Z0-9_]{1,80}$")


@dataclass(frozen=True)
class SecretRef:
    secret_ref_id: str
    provider: str
    secret_name: str
    allowed_endpoint_prefixes: List[str]
    allowed_capabilities: List[str]
    active: bool


@dataclass(frozen=True)
class SecretResolution:
    allowed: bool
    reason: str
    secret_value: Optional[str] = None
    secret_ref: Optional[SecretRef] = None


def ensure_secret_schema(conn: sqlite3.Connection) -> None:
    """WHY: additive schema keeps existing PoC DBs compatible while secrets stay reference-only."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS secret_refs (
            secret_ref_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            secret_name TEXT NOT NULL,
            allowed_endpoint_prefixes TEXT NOT NULL,
            allowed_capabilities TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_secret_refs_active ON secret_refs(active)")


def register_env_secret_ref(
    conn: sqlite3.Connection,
    *,
    secret_ref_id: str,
    secret_name: str,
    allowed_endpoint_prefixes: List[str],
    allowed_capabilities: Optional[List[str]] = None,
    active: bool = True,
) -> SecretRef:
    """
    Registers a reference to an environment-provided secret; the raw value is never persisted.
    SEC: secret_name must be a constrained env-safe identifier, not an arbitrary variable expression.
    """
    ensure_secret_schema(conn)
    name = (secret_name or "").strip().upper()
    if not _SECRET_NAME_RE.match(name):
        raise ValueError("secret_name must match ^[A-Z0-9_]{1,80}$")
    prefixes = [p for p in allowed_endpoint_prefixes if isinstance(p, str) and p.strip()]
    if not prefixes:
        raise ValueError("at least one allowed endpoint prefix is required")
    caps = allowed_capabilities or ["api_call"]
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO secret_refs
              (secret_ref_id, provider, secret_name, allowed_endpoint_prefixes, allowed_capabilities, active, created_at)
            VALUES (?, 'env', ?, ?, ?, ?, ?)
            """,
            (secret_ref_id, name, json.dumps(prefixes), json.dumps(caps), 1 if active else 0, now),
        )
    return SecretRef(secret_ref_id, "env", name, prefixes, caps, active)


def load_secret_ref(conn: sqlite3.Connection, secret_ref_id: str) -> Optional[SecretRef]:
    ensure_secret_schema(conn)
    row = conn.execute("SELECT * FROM secret_refs WHERE secret_ref_id = ?", (secret_ref_id,)).fetchone()
    if row is None:
        return None
    return SecretRef(
        secret_ref_id=row["secret_ref_id"],
        provider=row["provider"],
        secret_name=row["secret_name"],
        allowed_endpoint_prefixes=list(json.loads(row["allowed_endpoint_prefixes"])),
        allowed_capabilities=list(json.loads(row["allowed_capabilities"])),
        active=bool(row["active"]),
    )


def resolve_secret_for_api(
    conn: sqlite3.Connection,
    *,
    secret_ref_id: Optional[str],
    endpoint: str,
    requested_capability: str,
) -> SecretResolution:
    """
    SEC: returns a secret only after ref, endpoint scope, capability scope, and provider value are valid.
    The caller must invoke this only after Enforcement and all Guards have passed.
    """
    if not secret_ref_id:
        return SecretResolution(True, "no secret required")

    ref = load_secret_ref(conn, secret_ref_id)
    if ref is None:
        return SecretResolution(False, f"secret ref not found: {secret_ref_id}")
    if not ref.active:
        return SecretResolution(False, f"secret ref disabled: {secret_ref_id}", secret_ref=ref)
    if requested_capability not in ref.allowed_capabilities:
        return SecretResolution(False, f"secret capability not allowed: {requested_capability}", secret_ref=ref)
    if not any((endpoint or "").startswith(prefix) for prefix in ref.allowed_endpoint_prefixes):
        return SecretResolution(False, f"secret endpoint scope mismatch: {endpoint}", secret_ref=ref)

    value = _resolve_env_secret(ref.secret_name)
    if not value:
        return SecretResolution(False, f"secret value unavailable: {ref.secret_name}", secret_ref=ref)
    return SecretResolution(True, "secret resolved", secret_value=value, secret_ref=ref)


def _resolve_env_secret(secret_name: str) -> Optional[str]:
    # Preferred local format: GATEGRAPH_SECRET_PROVIDER_JSON='{"API_KEY":"value"}'
    raw_json = os.environ.get(_ENV_SECRET_JSON)
    if raw_json:
        try:
            parsed: Dict[str, object] = json.loads(raw_json)
            value = parsed.get(secret_name)
            if isinstance(value, str) and value:
                return value
        except Exception:
            return None

    value = os.environ.get(f"{_ENV_SECRET_PREFIX}{secret_name}")
    return value if value else None
