"""
WHY: Review workflow turns advisory Pattern Engine output into explicit human decisions.
INV: this module never applies proposals. Approval means "approved for manual action", not runtime change.
SEC: no rule/policy/secret/token/budget/action mutation is performed here.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


ALLOWED_REVIEW_DECISIONS = {"approved_for_manual_action", "rejected"}
PENDING_STATUS = "pending_review"


@dataclass(frozen=True)
class ReviewItem:
    proposal_id: str
    proposal_type: str
    reason: str
    proposed_change: str
    priority: str
    score: float
    status: str
    confidence: float


@dataclass(frozen=True)
class ReviewDecision:
    review_id: str
    proposal_id: str
    reviewer_id: str
    decision: str
    rationale: str
    created_at: str


class ReviewWorkflowError(ValueError):
    pass


def list_pending_reviews(conn: sqlite3.Connection, *, limit: int = 50) -> List[ReviewItem]:
    """Returns pending proposals ordered for human review."""
    rows = conn.execute(
        """
        SELECT proposal_id, proposal_type, reason, proposed_change, priority, score, status, confidence
        FROM proposals
        WHERE status = ?
        ORDER BY
            CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END,
            score DESC,
            created_at ASC
        LIMIT ?
        """,
        (PENDING_STATUS, limit),
    ).fetchall()
    return [
        ReviewItem(
            proposal_id=row["proposal_id"],
            proposal_type=row["proposal_type"],
            reason=row["reason"],
            proposed_change=row["proposed_change"],
            priority=row["priority"],
            score=float(row["score"]),
            status=row["status"],
            confidence=float(row["confidence"]),
        )
        for row in rows
    ]


def decide_proposal(
    conn: sqlite3.Connection,
    *,
    proposal_id: str,
    reviewer_id: str,
    decision: str,
    rationale: str,
) -> ReviewDecision:
    """
    Records an explicit review decision.

    INV: even approved proposals are only marked approved_for_manual_action. No runtime
    governance state changes occur here.
    """
    if decision not in ALLOWED_REVIEW_DECISIONS:
        raise ReviewWorkflowError(f"unsupported review decision: {decision}")
    if not reviewer_id.strip():
        raise ReviewWorkflowError("reviewer_id is required")
    if not rationale.strip():
        raise ReviewWorkflowError("rationale is required")

    row = conn.execute("SELECT proposal_id, status FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    if row is None:
        raise ReviewWorkflowError(f"proposal not found: {proposal_id}")
    if row["status"] != PENDING_STATUS:
        raise ReviewWorkflowError(f"proposal is not pending review: {proposal_id} status={row['status']}")

    review = ReviewDecision(
        review_id=f"REV-{uuid.uuid4().hex[:12].upper()}",
        proposal_id=proposal_id,
        reviewer_id=reviewer_id,
        decision=decision,
        rationale=rationale,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with conn:
        conn.execute(
            """
            INSERT INTO proposal_review_decisions
                (review_id, proposal_id, reviewer_id, decision, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (review.review_id, review.proposal_id, review.reviewer_id, review.decision, review.rationale, review.created_at),
        )
        conn.execute("UPDATE proposals SET status = ? WHERE proposal_id = ?", (decision, proposal_id))
    return review


def get_review_decision(conn: sqlite3.Connection, proposal_id: str) -> Optional[ReviewDecision]:
    row = conn.execute(
        """
        SELECT review_id, proposal_id, reviewer_id, decision, rationale, created_at
        FROM proposal_review_decisions
        WHERE proposal_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (proposal_id,),
    ).fetchone()
    if row is None:
        return None
    return ReviewDecision(
        review_id=row["review_id"],
        proposal_id=row["proposal_id"],
        reviewer_id=row["reviewer_id"],
        decision=row["decision"],
        rationale=row["rationale"],
        created_at=row["created_at"],
    )
