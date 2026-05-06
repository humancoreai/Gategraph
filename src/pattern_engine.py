"""
WHY: Pattern Engine turns repeated audit evidence into proposals, not automatic rule changes.
INV: this module never writes to rules; it only creates pending proposals.
SEC: proposals are advisory and require human review before affecting Governance behavior.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


SCHEMA_VERSION = "0.7"
DEFAULT_MIN_EVENTS = 3
DEFAULT_CONFIDENCE_THRESHOLD = 0.75


@dataclass(frozen=True)
class PatternProposal:
    proposal_id: str
    proposal_type: str
    target_rule_id: Optional[str]
    reason: str
    proposed_change: str
    supporting_events: List[str]
    confidence: float
    confidence_basis: str
    status: str = "pending_review"


@dataclass(frozen=True)
class PatternRunResult:
    proposals_created: int
    proposals: List[PatternProposal]


def analyze_rejections(
    conn: sqlite3.Connection,
    *,
    min_events: int = DEFAULT_MIN_EVENTS,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> PatternRunResult:
    rows = conn.execute(
        """
        SELECT event_id, input_json, decision_json
        FROM events
        WHERE type = 'enforcement_rejection'
        ORDER BY timestamp ASC
        """
    ).fetchall()

    if len(rows) < min_events:
        return PatternRunResult(proposals_created=0, proposals=[])

    grouped = {}
    for row in rows:
        input_data = json.loads(row["input_json"])
        decision_data = json.loads(row["decision_json"])
        cap = input_data.get("requested_capability", "unknown")
        reason = decision_data.get("reason", "unknown")
        key = _bucket(capability=cap, reason=reason)
        grouped.setdefault(key, []).append(row["event_id"])

    proposals: List[PatternProposal] = []
    total_relevant = len(rows)

    for key, event_ids in grouped.items():
        if len(event_ids) < min_events:
            continue
        confidence = len(event_ids) / total_relevant
        if confidence < confidence_threshold:
            continue

        capability, reason_bucket = key
        proposal = _create_rejection_proposal(
            conn,
            capability=capability,
            reason_bucket=reason_bucket,
            supporting_events=event_ids,
            confidence=confidence,
            total_relevant=total_relevant,
        )
        proposals.append(proposal)

    return PatternRunResult(proposals_created=len(proposals), proposals=proposals)


def _bucket(*, capability: str, reason: str) -> tuple[str, str]:
    reason = reason.lower()
    if "no capability token" in reason:
        return capability, "missing_token"
    if "expired" in reason:
        return capability, "expired_token"
    if "revoked" in reason:
        return capability, "revoked_token"
    if "not granted" in reason:
        return capability, "capability_not_granted"
    if "bound to task" in reason:
        return capability, "cross_task_reuse"
    return capability, "other_rejection"


def _create_rejection_proposal(
    conn: sqlite3.Connection,
    *,
    capability: str,
    reason_bucket: str,
    supporting_events: List[str],
    confidence: float,
    total_relevant: int,
) -> PatternProposal:
    proposal_id = f"RUP-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    reason = f"Repeated enforcement rejections for capability={capability!r}, bucket={reason_bucket!r}."
    proposed_change = (
        "Review whether task prompts, capability requests, or rules should be clarified. "
        "Do not auto-change rules."
    )

    proposal = PatternProposal(
        proposal_id=proposal_id,
        proposal_type="repeated_enforcement_rejection",
        target_rule_id=None,
        reason=reason,
        proposed_change=proposed_change,
        supporting_events=supporting_events,
        confidence=round(confidence, 4),
        confidence_basis=f"{len(supporting_events)}/{total_relevant} matching rejection events",
    )

    with conn:
        conn.execute(
            """
            INSERT INTO proposals (
                proposal_id, schema_version, proposal_type, target_rule_id,
                reason, proposed_change, supporting_events, confidence,
                confidence_basis, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal.proposal_id,
                SCHEMA_VERSION,
                proposal.proposal_type,
                proposal.target_rule_id,
                proposal.reason,
                proposal.proposed_change,
                json.dumps(proposal.supporting_events),
                proposal.confidence,
                proposal.confidence_basis,
                proposal.status,
                now,
            ),
        )

    return proposal


def count_proposals(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]


def active_rule_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM rules WHERE active = 1").fetchone()[0]
