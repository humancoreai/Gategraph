"""
WHY: capability tokens decouple decision from execution — enforcement never re-evaluates rules.
INV: a token can only grant capabilities explicitly allowed in the decision.
SEC: tokens expire, can be revoked, and carry an HMAC signature over their immutable claims.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Mapping

DEFAULT_TTL_SECONDS = 300
DEFAULT_SIGNING_KEY_ID = "local-dev-v2"
_ENV_SECRET = "GATEGRAPH_TOKEN_SIGNING_SECRET"
_ENV_ACTIVE_KEY_ID = "GATEGRAPH_TOKEN_ACTIVE_KEY_ID"
_ENV_KEYRING_JSON = "GATEGRAPH_TOKEN_KEYRING_JSON"
_DEV_KEYRING = {
    # SEC: development-only deterministic secrets for local evidence tests.
    # Never use these defaults with real data, CI secrets, or production workloads.
    "local-dev-v2": "gategraph-local-dev-token-signing-secret-v2",
    "local-dev-v1": "gategraph-local-dev-token-signing-secret",
}


@dataclass(frozen=True)
class CapabilityToken:
    token_id: str
    decision_id: str
    task_id: str
    capabilities: Dict[str, bool]
    issued_at: datetime
    expires_at: datetime
    signature: str
    signing_key_id: str = DEFAULT_SIGNING_KEY_ID

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def allows(self, capability: str) -> bool:
        return self.capabilities.get(capability, False)


def _ensure_token_schema(conn: sqlite3.Connection) -> None:
    """WHY: additive migration keeps older local DBs readable during prototype iteration."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(capability_tokens)")}
    if "signature" not in cols:
        conn.execute("ALTER TABLE capability_tokens ADD COLUMN signature TEXT NOT NULL DEFAULT ''")
    if "signing_key_id" not in cols:
        conn.execute("ALTER TABLE capability_tokens ADD COLUMN signing_key_id TEXT NOT NULL DEFAULT 'local-dev-v1'")


def load_trusted_keyring() -> Dict[str, bytes]:
    """
    SEC: public keyring loader; callers that need deterministic per-decision behavior load once and pass it through.
    Format: GATEGRAPH_TOKEN_KEYRING_JSON='{"kid-a":"secret-a","kid-b":"secret-b"}'
    """
    raw = os.environ.get(_ENV_KEYRING_JSON)
    if raw:
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict) or not parsed:
                return {}
            return {str(k): str(v).encode("utf-8") for k, v in parsed.items() if str(k).strip() and str(v)}
        except Exception:
            return {}

    # Compatibility path for v0.8.8 single-key deployments.
    if os.environ.get(_ENV_SECRET):
        active = os.environ.get(_ENV_ACTIVE_KEY_ID, DEFAULT_SIGNING_KEY_ID)
        return {active: os.environ[_ENV_SECRET].encode("utf-8")}

    # Local deterministic default keeps evidence tests reproducible; not a production secret store.
    return {kid: secret.encode("utf-8") for kid, secret in _DEV_KEYRING.items()}


def active_signing_key_id() -> str:
    return os.environ.get(_ENV_ACTIVE_KEY_ID, DEFAULT_SIGNING_KEY_ID)


def _signing_secret(signing_key_id: str, keyring: Optional[Mapping[str, bytes]] = None) -> Optional[bytes]:
    return (keyring or load_trusted_keyring()).get(signing_key_id)


def is_trusted_signing_key(signing_key_id: str, keyring: Optional[Mapping[str, bytes]] = None) -> bool:
    """SEC: public trust check so enforcement does not depend on private keyring internals."""
    return signing_key_id in (keyring or load_trusted_keyring())


def _canonical_claims(*, token_id: str, decision_id: str, task_id: str, capabilities: Dict[str, bool], issued_at: datetime, expires_at: datetime, signing_key_id: str) -> str:
    payload = {
        "token_id": token_id,
        "decision_id": decision_id,
        "task_id": task_id,
        "capabilities": {k: bool(capabilities[k]) for k in sorted(capabilities)},
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "signing_key_id": signing_key_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sign_claims(*, token_id: str, decision_id: str, task_id: str, capabilities: Dict[str, bool], issued_at: datetime, expires_at: datetime, signing_key_id: str = DEFAULT_SIGNING_KEY_ID, keyring: Optional[Mapping[str, bytes]] = None) -> str:
    secret = _signing_secret(signing_key_id, keyring)
    if secret is None:
        raise ValueError(f"unknown signing key id: {signing_key_id}")
    canonical = _canonical_claims(
        token_id=token_id,
        decision_id=decision_id,
        task_id=task_id,
        capabilities=capabilities,
        issued_at=issued_at,
        expires_at=expires_at,
        signing_key_id=signing_key_id,
    )
    return hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(token: CapabilityToken, persisted_signature: Optional[str] = None, keyring: Optional[Mapping[str, bytes]] = None) -> bool:
    try:
        expected = sign_claims(
            token_id=token.token_id,
            decision_id=token.decision_id,
            task_id=token.task_id,
            capabilities=token.capabilities,
            issued_at=token.issued_at,
            expires_at=token.expires_at,
            signing_key_id=token.signing_key_id,
            keyring=keyring,
        )
    except Exception:
        return False
    if not hmac.compare_digest(expected, token.signature or ""):
        return False
    if persisted_signature is not None and not hmac.compare_digest(token.signature or "", persisted_signature or ""):
        return False
    return True


def _insert_token(conn: sqlite3.Connection, token: CapabilityToken, revoked: int = 0) -> CapabilityToken:
    _ensure_token_schema(conn)
    conn.execute(
        """
        INSERT INTO capability_tokens
          (token_id, decision_id, task_id, capabilities, issued_at, expires_at, revoked, signature, signing_key_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            token.token_id,
            token.decision_id,
            token.task_id,
            json.dumps(token.capabilities, sort_keys=True),
            token.issued_at.isoformat(),
            token.expires_at.isoformat(),
            revoked,
            token.signature,
            token.signing_key_id,
        ),
    )
    return token


def issue_token(conn: sqlite3.Connection, decision_id: str, task_id: str, final_capabilities: Dict[str, bool], ttl_seconds: int = DEFAULT_TTL_SECONDS) -> CapabilityToken:
    token_id = f"TOK-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)
    signing_key_id = active_signing_key_id()
    signature = sign_claims(token_id=token_id, decision_id=decision_id, task_id=task_id, capabilities=final_capabilities, issued_at=now, expires_at=expires_at, signing_key_id=signing_key_id)
    token = CapabilityToken(token_id, decision_id, task_id, dict(final_capabilities), now, expires_at, signature, signing_key_id)
    return _insert_token(conn, token)


def issue_expired_token(conn: sqlite3.Connection, decision_id: str, task_id: str, final_capabilities: Dict[str, bool]) -> CapabilityToken:
    """
    WHY: test-only helper for timeout validation.
    SEC: production paths must use issue_token(); this is intentionally not called by governance.py.
    """
    token_id = f"TOK-EXPIRED-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    issued_at = now - timedelta(seconds=301)
    expires_at = now - timedelta(seconds=1)
    signing_key_id = active_signing_key_id()
    signature = sign_claims(token_id=token_id, decision_id=decision_id, task_id=task_id, capabilities=final_capabilities, issued_at=issued_at, expires_at=expires_at, signing_key_id=signing_key_id)
    token = CapabilityToken(token_id, decision_id, task_id, dict(final_capabilities), issued_at, expires_at, signature, signing_key_id)
    return _insert_token(conn, token)


issue_expired_token.__test_only__ = True
