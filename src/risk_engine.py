"""
WHY: Risk Engine is stateless — same input always produces same output
INV: priority order is fixed and must not be changed without spec update
SEC: fail-closed — unknown or boundary-crossing inputs never get downgraded silently
"""

from dataclasses import dataclass
from typing import List


RISK_LEVELS = ("low", "medium", "high", "critical")
VALID_INPUT_SOURCES = {"local", "external", "untrusted"}
VALID_DATA_SENSITIVITY = {"public", "internal", "confidential", "secret"}


@dataclass(frozen=True)
class RiskResult:
    risk_level: str
    reason: str


def classify(
    requested_capabilities: List[str],
    input_source: str,
    data_sensitivity: str = "internal",
    secrets_involved: bool = False,
) -> RiskResult:
    """
    INV: highest applicable risk wins; no later rule may downgrade a prior classification.
    SEC: unknown enum values are at least medium — never silently treated as safe.
    """
    caps = set(requested_capabilities)

    # Priority 1 — explicit secrets are always critical.
    if secrets_involved:
        return RiskResult(
            risk_level="critical",
            reason="secrets_involved=True — escalates unconditionally to critical",
        )

    # Priority 2 — secret sensitivity is critical even without explicit secret flag.
    if data_sensitivity == "secret":
        return RiskResult(
            risk_level="critical",
            reason="data_sensitivity=secret — treat as critical",
        )

    # Priority 3 — unknown enum values require review instead of silent allow.
    if input_source not in VALID_INPUT_SOURCES:
        return RiskResult(
            risk_level="medium",
            reason=f"unknown input_source={input_source!r} — requires review",
        )

    if data_sensitivity not in VALID_DATA_SENSITIVITY:
        return RiskResult(
            risk_level="medium",
            reason=f"unknown data_sensitivity={data_sensitivity!r} — requires review",
        )

    # Priority 4 — persistent side-effect capabilities.
    destructive = {"write_files", "delete_files", "modify_config"}
    if destructive & caps:
        return RiskResult(
            risk_level="high",
            reason=f"destructive capability requested: {sorted(destructive & caps)}",
        )

    # Priority 5 — external API calls cross the local trust boundary.
    if "api_call" in caps and input_source == "external":
        return RiskResult(
            risk_level="medium",
            reason="api_call with input_source=external — external boundary crossing",
        )

    # Priority 6 — untrusted input must be treated as data, never instruction.
    if input_source == "untrusted":
        return RiskResult(
            risk_level="medium",
            reason="input_source=untrusted — data must not be treated as instruction",
        )

    # SEC: default is low only when all elevated conditions are explicitly absent.
    return RiskResult(risk_level="low", reason="no elevated risk factors detected")
