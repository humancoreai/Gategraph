"""
WHY: Pattern Engine turns repeated audit evidence into proposals, not automatic rule changes.
INV: this module never writes to rules; it only creates pending proposals.
SEC: proposals are advisory and require human review before affecting Governance behavior.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCHEMA_VERSION = "0.8.19"
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
    priority: str
    score: float
    score_basis: str
    status: str = "pending_review"


@dataclass(frozen=True)
class PatternRunResult:
    proposals_created: int
    proposals: List[PatternProposal]


@dataclass(frozen=True)
class PatternObservation:
    event_id: str
    task_id: str
    event_type: str
    stage: str
    capability: str
    bucket: str
    raw_reason: str
    severity: str


def analyze_rejections(
    conn: sqlite3.Connection,
    *,
    min_events: int = DEFAULT_MIN_EVENTS,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> PatternRunResult:
    """Backward-compatible entry point for enforcement-only rejection patterns."""
    observations = [obs for obs in _collect_observations(conn) if obs.event_type == "enforcement_rejection"]
    return _create_proposals_from_observations(
        conn,
        observations,
        proposal_type="repeated_enforcement_rejection",
        min_events=min_events,
        confidence_threshold=confidence_threshold,
    )


def analyze_audit_patterns(
    conn: sqlite3.Connection,
    *,
    min_events: int = DEFAULT_MIN_EVENTS,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> PatternRunResult:
    """
    Scans audit evidence across Enforcement, Runtime/Session, HTTP Policy, and Secret stages.

    INV: this function creates proposal records only. It never updates rules, tokens,
    budgets, policies, secrets, or decisions.
    """
    observations = _collect_observations(conn)
    return _create_proposals_from_observations(
        conn,
        observations,
        proposal_type="repeated_guard_pattern",
        min_events=min_events,
        confidence_threshold=confidence_threshold,
    )


def _collect_observations(conn: sqlite3.Connection) -> List[PatternObservation]:
    rows = conn.execute(
        """
        SELECT event_id, task_id, type, input_json, evaluation_json, decision_json
        FROM events
        ORDER BY timestamp ASC
        """
    ).fetchall()

    observations: List[PatternObservation] = []
    for row in rows:
        input_data = _loads(row["input_json"])
        evaluation = _loads(row["evaluation_json"])
        decision = _loads(row["decision_json"])
        obs = _observation_from_event(row, input_data, evaluation, decision)
        if obs is not None:
            observations.append(obs)
    return observations


def _observation_from_event(row: sqlite3.Row, input_data: Dict[str, Any], evaluation: Dict[str, Any], decision: Dict[str, Any]) -> Optional[PatternObservation]:
    event_type = row["type"]
    capability = str(input_data.get("requested_capability") or "unknown")

    if event_type == "enforcement_rejection":
        raw_reason = str(decision.get("reason") or "unknown")
        bucket = _bucket(capability=capability, stage="enforcement", reason=raw_reason)
        return PatternObservation(row["event_id"], row["task_id"], event_type, "enforcement", capability, bucket, raw_reason, _severity_for("enforcement", bucket))

    if event_type == "external_api_call" and decision.get("status") == "blocked":
        stage, raw_reason = _blocked_external_api_stage(evaluation, decision)
        bucket = _bucket(capability=capability, stage=stage, reason=raw_reason)
        return PatternObservation(row["event_id"], row["task_id"], event_type, stage, capability, bucket, raw_reason, _severity_for(stage, bucket))

    return None


def _blocked_external_api_stage(evaluation: Dict[str, Any], decision: Dict[str, Any]) -> Tuple[str, str]:
    http_policy = evaluation.get("http_policy") or {}
    if isinstance(http_policy, dict) and http_policy.get("allowed") is False:
        return "http_policy", str(http_policy.get("reason") or decision.get("response_summary") or "http policy blocked")

    secret_resolution = evaluation.get("secret_resolution") or {}
    if isinstance(secret_resolution, dict) and secret_resolution.get("allowed") is False:
        return "secret_provider", str(secret_resolution.get("reason") or decision.get("response_summary") or "secret provider blocked")

    stage = str(evaluation.get("pipeline_stage") or "external_api")
    reason = str(evaluation.get("pipeline_reason") or decision.get("response_summary") or "external api blocked")
    return stage, reason


def _create_proposals_from_observations(
    conn: sqlite3.Connection,
    observations: List[PatternObservation],
    *,
    proposal_type: str,
    min_events: int,
    confidence_threshold: float,
) -> PatternRunResult:
    if len(observations) < min_events:
        return PatternRunResult(proposals_created=0, proposals=[])

    grouped: Dict[Tuple[str, str, str], List[PatternObservation]] = {}
    for obs in observations:
        key = (obs.stage, obs.capability, obs.bucket)
        grouped.setdefault(key, []).append(obs)

    proposals: List[PatternProposal] = []
    total_relevant = len(observations)
    for key, items in grouped.items():
        if len(items) < min_events:
            continue
        confidence = len(items) / total_relevant
        if confidence < confidence_threshold:
            continue
        score, priority, score_basis = _score_pattern(items, confidence=confidence)
        proposal = _create_pattern_proposal(
            conn,
            proposal_type=proposal_type,
            stage=key[0],
            capability=key[1],
            bucket=key[2],
            observations=items,
            confidence=confidence,
            total_relevant=total_relevant,
            priority=priority,
            score=score,
            score_basis=score_basis,
        )
        proposals.append(proposal)

    return PatternRunResult(proposals_created=len(proposals), proposals=proposals)


def _bucket(*, capability: str, stage: str = "enforcement", reason: str) -> str:
    reason = (reason or "").lower()
    if stage == "enforcement":
        if "no capability token" in reason:
            return "missing_token"
        if "expired" in reason:
            return "expired_token"
        if "revoked" in reason:
            return "revoked_token"
        if "not granted" in reason:
            return "capability_not_granted"
        if "bound to task" in reason:
            return "cross_task_reuse"
        if "invalid signature" in reason:
            return "invalid_signature"
        if "claim mismatch" in reason:
            return "claim_mismatch"
        if "unknown signing key" in reason:
            return "unknown_signing_key"
    if stage == "http_policy":
        if "scheme" in reason:
            return "http_scheme_blocked"
        if "method" in reason:
            return "http_method_blocked"
        if "host" in reason or "allowlisted" in reason or "endpoint" in reason:
            return "http_endpoint_blocked"
    if stage == "secret_provider":
        if "not found" in reason:
            return "secret_ref_missing"
        if "disabled" in reason:
            return "secret_ref_disabled"
        if "scope mismatch" in reason:
            return "secret_scope_mismatch"
        if "unavailable" in reason:
            return "secret_value_unavailable"
    if stage in {"session_budget", "runtime_guard", "runtime_budget"}:
        if "cost" in reason:
            return "budget_cost_pressure"
        if "step" in reason:
            return "runtime_step_pressure"
        if "repeated" in reason:
            return "runtime_repetition_pressure"
    return "other_rejection"


def _severity_for(stage: str, bucket: str) -> str:
    if stage == "enforcement" and bucket in {"invalid_signature", "claim_mismatch", "cross_task_reuse", "unknown_signing_key"}:
        return "critical"
    if stage == "secret_provider":
        return "high"
    if stage == "http_policy":
        return "high"
    if "budget" in stage or "runtime" in stage:
        return "medium"
    return "medium"



def _score_pattern(observations: List[PatternObservation], *, confidence: float) -> Tuple[float, str, str]:
    """
    Converts repeated audit evidence into reviewer priority and score.

    INV: scoring changes proposal triage only; it never changes runtime decisions.
    WHY: humans need ordering without granting the Pattern Engine authority.
    """
    severity_rank = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
    max_severity = max((severity_rank.get(obs.severity, 0.5) for obs in observations), default=0.5)
    support_factor = min(len(observations) / 10.0, 1.0)
    bounded_confidence = max(0.0, min(confidence, 1.0))
    raw_score = (0.50 * max_severity) + (0.30 * bounded_confidence) + (0.20 * support_factor)
    score = round(raw_score * 100.0, 2)
    priority = _priority_for_score(score)
    severities = sorted({obs.severity for obs in observations})
    basis = (
        f"score={score}; priority={priority}; severity={','.join(severities)}; "
        f"support={len(observations)}; confidence={round(bounded_confidence, 4)}"
    )
    return score, priority, basis


def _priority_for_score(score: float) -> str:
    if score >= 85.0:
        return "P0"
    if score >= 70.0:
        return "P1"
    if score >= 50.0:
        return "P2"
    return "P3"

def _create_pattern_proposal(
    conn: sqlite3.Connection,
    *,
    proposal_type: str,
    stage: str,
    capability: str,
    bucket: str,
    observations: List[PatternObservation],
    confidence: float,
    total_relevant: int,
    priority: str,
    score: float,
    score_basis: str,
) -> PatternProposal:
    proposal_id = f"RUP-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    event_ids = [obs.event_id for obs in observations]
    severities = sorted({obs.severity for obs in observations})
    reason = (
        f"Repeated guard pattern detected: stage={stage!r}, capability={capability!r}, "
        f"bucket={bucket!r}, severity={','.join(severities)}."
    )
    proposed_change = _proposed_change_for(stage, bucket)

    proposal = PatternProposal(
        proposal_id=proposal_id,
        proposal_type=proposal_type,
        target_rule_id=None,
        reason=reason,
        proposed_change=proposed_change,
        supporting_events=event_ids,
        confidence=round(confidence, 4),
        confidence_basis=f"{len(event_ids)}/{total_relevant} matching audit observations; stage={stage}; bucket={bucket}",
        priority=priority,
        score=score,
        score_basis=score_basis,
    )

    _insert_proposal(conn, proposal, now)
    return proposal


def _proposed_change_for(stage: str, bucket: str) -> str:
    base = "Proposal only: require human review before any rule, policy, budget, or secret change. "
    if stage == "http_policy":
        return base + "Review whether callers are misconfigured or whether an explicit endpoint policy should be added; do not widen allowlists automatically."
    if stage == "secret_provider":
        return base + "Review secret reference scope/provider setup; never expose or log raw secret values."
    if stage == "enforcement":
        return base + "Review token issuance flow, task binding, and requested capabilities; do not auto-grant capabilities."
    if stage in {"session_budget", "runtime_guard", "runtime_budget"}:
        return base + "Review task design and budget sizing; do not auto-raise limits."
    return base + "Review repeated audit evidence and decide whether documentation, caller behavior, or governance rules need adjustment."


def _insert_proposal(conn: sqlite3.Connection, proposal: PatternProposal, created_at: str) -> None:
    with conn:
        conn.execute(
            """
            INSERT INTO proposals (
                proposal_id, schema_version, proposal_type, target_rule_id,
                reason, proposed_change, supporting_events, confidence,
                confidence_basis, priority, score, score_basis, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                proposal.priority,
                proposal.score,
                proposal.score_basis,
                proposal.status,
                created_at,
            ),
        )


def _loads(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def count_proposals(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]


def active_rule_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM rules WHERE active = 1").fetchone()[0]
