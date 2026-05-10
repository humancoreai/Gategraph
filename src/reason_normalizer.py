"""
WHY: Raw guard reasons are good for debugging but unstable for automation and reports.
INV: normalization never changes decisions; it only maps existing stage/reason into stable explain fields.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class NormalizedReason:
    code: str
    category: str
    severity: str
    stage: str
    message: str
    raw_reason: str
    priority: int


_REASON_MAP = [
    ("enforcement", "no capability token", "ENF_NO_TOKEN", "authorization", "critical", 100, "Action blocked because no valid capability token was provided."),
    ("enforcement", "revoked", "ENF_TOKEN_REVOKED", "authorization", "critical", 100, "Action blocked because the capability token was revoked."),
    ("enforcement", "expired", "ENF_TOKEN_EXPIRED", "authorization", "high", 90, "Action blocked because the capability token expired."),
    ("session_budget", "no session budget", "SES_NO_BUDGET", "session_budget", "critical", 80, "Session budget is missing; execution fails closed."),
    ("session_budget", "max_session_cost_units", "SES_COST_LIMIT", "session_budget", "high", 75, "Session cost budget was exceeded."),
    ("session_budget", "max_session_tasks", "SES_TASK_LIMIT", "session_budget", "high", 74, "Session task budget was exceeded."),
    ("session_budget", "max_agent_cost_units", "SES_AGENT_COST_LIMIT", "session_budget", "high", 73, "Agent-level session cost budget was exceeded."),
    ("runtime_guard", "no runtime budget", "RT_NO_BUDGET", "runtime_budget", "critical", 70, "Runtime budget is missing; execution fails closed."),
    ("runtime_guard", "max_runtime_seconds", "RT_RUNTIME_LIMIT", "runtime_budget", "high", 65, "Per-task runtime limit was exceeded."),
    ("runtime_guard", "max_steps", "RT_STEP_LIMIT", "runtime_budget", "high", 64, "Per-task step limit was exceeded."),
    ("runtime_guard", "max_cost_units", "RT_COST_LIMIT", "runtime_budget", "high", 63, "Per-task cost budget was exceeded."),
    ("runtime_guard", "repeated_action_limit", "RT_REPEATED_ACTION", "loop_control", "medium", 60, "Repeated action limit was exceeded."),
    ("pattern_engine", "pending_review", "PAT_PROPOSAL_ONLY", "pattern_safety", "info", 30, "Pattern Engine produced proposal-only output pending review."),
    ("action_ready", "all guards passed", "OK_ACTION_READY", "ok", "info", 0, "All guards passed; action may proceed."),
]


def normalize_reason(stage: str, raw_reason: str) -> NormalizedReason:
    stage_norm = (stage or "unknown").strip().lower()
    reason_norm = (raw_reason or "").strip().lower()

    for expected_stage, fragment, code, category, severity, priority, message in _REASON_MAP:
        if stage_norm == expected_stage and fragment in reason_norm:
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
