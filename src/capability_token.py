"""
WHY: capability tokens decouple decision from execution — enforcement never re-evaluates rules.
INV: a token can only grant capabilities explicitly allowed in the decision.
SEC: tokens expire and can be revoked; no persistent grant exists beyond expiry/revocation.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict

DEFAULT_TTL_SECONDS = 300


@dataclass(frozen=True)
class CapabilityToken:
    token_id: str
    decision_id: str
    task_id: str
    capabilities: Dict[str, bool]
    issued_at: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def allows(self, capability: str) -> bool:
        return self.capabilities.get(capability, False)


def issue_token(conn: sqlite3.Connection, decision_id: str, task_id: str, final_capabilities: Dict[str, bool], ttl_seconds: int = DEFAULT_TTL_SECONDS) -> CapabilityToken:
    token_id = f"TOK-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)
    conn.execute(
        """
        INSERT INTO capability_tokens
          (token_id, decision_id, task_id, capabilities, issued_at, expires_at, revoked)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (token_id, decision_id, task_id, json.dumps(final_capabilities), now.isoformat(), expires_at.isoformat()),
    )
    return CapabilityToken(token_id, decision_id, task_id, dict(final_capabilities), now, expires_at)


def issue_expired_token(conn: sqlite3.Connection, decision_id: str, task_id: str, final_capabilities: Dict[str, bool]) -> CapabilityToken:
    """
    WHY: test-only helper for timeout validation.
    SEC: production paths must use issue_token(); this is intentionally not called by governance.py.
    """
    token_id = f"TOK-EXPIRED-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    issued_at = now - timedelta(seconds=301)
    expires_at = now - timedelta(seconds=1)
    conn.execute(
        """
        INSERT INTO capability_tokens
          (token_id, decision_id, task_id, capabilities, issued_at, expires_at, revoked)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (token_id, decision_id, task_id, json.dumps(final_capabilities), issued_at.isoformat(), expires_at.isoformat()),
    )
    return CapabilityToken(token_id, decision_id, task_id, dict(final_capabilities), issued_at, expires_at)
