"""
WHY: Raw guard reasons are good for debugging but unstable for automation and reports.
INV: normalization never changes decisions; it only maps existing stage/reason into stable explain fields.
SEC: matching uses explicit stage + canonical reason keys, not broad substring order.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Tuple


@dataclass(frozen=True)
class NormalizedReason:
    code: str
    category: str
    severity: str
    stage: str
    message: str
    raw_reason: str
    priority: int


# Canonical reason keys are explicit prefixes emitted by the guards.
_REASON_BY_STAGE_AND_KEY: Dict[Tuple[str, str], Tuple[str, str, str, int, str]] = {
    ("enforcement", "no capability token provided"): ("ENF_NO_TOKEN", "authorization", "critical", 100, "Action blocked because no valid capability token was provided."),
    ("enforcement", "capability token revoked"): ("ENF_TOKEN_REVOKED", "authorization", "critical", 100, "Action blocked because the capability token was revoked."),
    ("enforcement", "capability token expired"): ("ENF_TOKEN_EXPIRED", "authorization", "high", 90, "Action blocked because the capability token expired."),
    ("enforcement", "capability token invalid signature"): ("ENF_INVALID_SIGNATURE", "authorization", "critical", 100, "Action blocked because the capability token signature is invalid."),
    ("enforcement", "capability token unknown signing key"): ("ENF_UNKNOWN_SIGNING_KEY", "authorization", "critical", 100, "Action blocked because the token signing key is not trusted by this node."),
    ("enforcement", "capability token claim mismatch"): ("ENF_CLAIM_MISMATCH", "authorization", "critical", 100, "Action blocked because persisted and presented token claims differ."),
    ("enforcement", "capability token not found"): ("ENF_TOKEN_NOT_FOUND", "authorization", "critical", 100, "Action blocked because the capability token was not found."),
    ("session_budget", "no session budget exists"): ("SES_NO_BUDGET", "session_budget", "critical", 80, "Session budget is missing; execution fails closed."),
    ("session_budget", "max_session_cost_units exceeded"): ("SES_COST_LIMIT", "session_budget", "high", 75, "Session cost budget was exceeded."),
    ("session_budget", "max_session_tasks exceeded"): ("SES_TASK_LIMIT", "session_budget", "high", 74, "Session task budget was exceeded."),
    ("session_budget", "max_agent_cost_units exceeded"): ("SES_AGENT_COST_LIMIT", "session_budget", "high", 73, "Agent-level session cost budget was exceeded."),
    ("session_budget", "invalid projected_cost_units"): ("SES_INVALID_COST", "session_budget", "critical", 76, "Projected cost must be a positive integer; execution fails closed."),
    ("runtime_guard", "no runtime budget exists"): ("RT_NO_BUDGET", "runtime_budget", "critical", 70, "Runtime budget is missing; execution fails closed."),
    ("runtime_guard", "max_runtime_seconds exceeded"): ("RT_RUNTIME_LIMIT", "runtime_budget", "high", 65, "Per-task runtime limit was exceeded."),
    ("runtime_guard", "max_steps exceeded"): ("RT_STEP_LIMIT", "runtime_budget", "high", 64, "Per-task step limit was exceeded."),
    ("runtime_guard", "max_cost_units exceeded"): ("RT_COST_LIMIT", "runtime_budget", "high", 63, "Per-task cost budget was exceeded."),
    ("runtime_guard", "repeated_action_limit exceeded"): ("RT_REPEATED_ACTION", "loop_control", "medium", 60, "Repeated action limit was exceeded."),
    ("runtime_guard", "invalid cost_units"): ("RT_INVALID_COST", "runtime_budget", "critical", 66, "Runtime cost must be a positive integer; execution fails closed."),
    ("pattern_engine", "pending_review"): ("PAT_PROPOSAL_ONLY", "pattern_safety", "info", 30, "Pattern Engine produced proposal-only output pending review."),
    ("action_ready", "all guards passed"): ("OK_ACTION_READY", "ok", "info", 0, "All guards passed; action may proceed."),
}


def _canonical_key(raw_reason: str) -> str:
    reason = (raw_reason or "").strip().lower()
    # WHY: guard reasons use stable prefixes followed by variable details such as "32 > 30".
    if ":" in reason:
        reason = reason.split(":", 1)[0].strip()
    if " for signature " in reason:
        reason = reason.split(" for signature ", 1)[0].strip()
    return reason


def normalize_reason(stage: str, raw_reason: str) -> NormalizedReason:
    stage_norm = (stage or "unknown").strip().lower()
    reason_key = _canonical_key(raw_reason)

    mapped = _REASON_BY_STAGE_AND_KEY.get((stage_norm, reason_key))
    if mapped:
        code, category, severity, priority, message = mapped
        return NormalizedReason(
            code=code,
            category=category,
            severity=severity,
            stage=stage_norm,
            message=message,
            raw_reason=raw_reason,
            priority=priority,
        )

    fallback_code = f"{stage_norm.upper()}_UNCLASSIFIED" if stage_norm != "unknown" else "UNKNOWN_REASON"
    return NormalizedReason(
        code=fallback_code,
        category="unclassified",
        severity="medium",
        stage=stage_norm,
        message="Unclassified guard reason; raw reason must be inspected.",
        raw_reason=raw_reason,
        priority=50,
    )


def normalize_as_dict(stage: str, raw_reason: str) -> Dict[str, object]:
    return asdict(normalize_reason(stage, raw_reason))
