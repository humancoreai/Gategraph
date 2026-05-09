"""
SEC: Token and Authorization material must never be copied into audit, explain,
monitoring, evidence, or operator-facing views. Base64 is not redaction.
INV: Safe references are one-way fingerprints plus explicit ids only.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import is_dataclass, asdict
from typing import Any

HASH_PREFIX_LEN = 12
SAFE_TOKEN_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]{2,127}$")

SENSITIVE_KEY_FRAGMENTS = (
    "authorization",
    "bearer",
    "raw_token",
    "token_value",
    "access_token",
    "refresh_token",
    "id_token",
    "signature",
    "signing_input",
    "secret_value",
    "secret_material",
    "api_key_value",
    "password",
)

SAFE_KEY_EXACT = {
    "token_id",
    "token_hash",
    "key_id",
    "kid",
    "signing_key_id",
    "secret_ref_id",
    "secret_name",
    "secret_status",
    "requires_secret",
}


class RedactionError(ValueError):
    """Raised when sensitive material cannot be safely represented."""


def _sha256_prefix(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:HASH_PREFIX_LEN].upper()


def redact_token_value(value: str) -> dict[str, str]:
    """Return a non-reversible reference for opaque token material.

    The raw token is not included, partially copied, or base64 encoded. Empty or
    non-string values fail closed because an audit-safe representation cannot be
    proven.
    """
    if not isinstance(value, str) or not value.strip():
        raise RedactionError("unexpected token format")
    return {"redacted": "[REDACTED_TOKEN]", "token_hash": _sha256_prefix(value)}


def redact_authorization_header(value: str) -> dict[str, str]:
    """Redact an Authorization header without preserving bearer payloads."""
    if not isinstance(value, str) or not value.strip():
        raise RedactionError("unexpected authorization header format")
    parts = value.strip().split(None, 1)
    scheme = parts[0].lower()
    if scheme not in {"bearer", "basic"} or len(parts) != 2 or not parts[1].strip():
        raise RedactionError("unsupported authorization header format")
    return {"redacted": f"{scheme.title()} [REDACTED]", "header_hash": _sha256_prefix(value)}


def safe_token_reference(token: Any) -> dict[str, str]:
    """Build an audit-safe reference from a token-like object.

    Only stable identifiers and one-way hash material are returned. The token
    signature, serialized token object, and signing input remain excluded.
    """
    token_id = str(getattr(token, "token_id", "") or "")
    kid = str(getattr(token, "signing_key_id", "") or getattr(token, "kid", "") or "")
    task_id = str(getattr(token, "task_id", "") or "")
    decision_id = str(getattr(token, "decision_id", "") or "")
    if not token_id or not kid or not SAFE_TOKEN_ID_RE.match(token_id):
        raise RedactionError("unexpected token reference format")
    material = ":".join([token_id, kid, task_id, decision_id])
    return {"token_id": token_id, "token_hash": _sha256_prefix(material), "key_id": kid}


def _sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    if normalized in SAFE_KEY_EXACT:
        return False
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def redact_sensitive_value(value: Any) -> Any:
    """Recursively remove known sensitive fields from reviewer-facing payloads."""
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        sanitized: dict[Any, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _sensitive_key(key_text):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = redact_sensitive_value(item)
        return sanitized
    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive_value(item) for item in value]
    return value
