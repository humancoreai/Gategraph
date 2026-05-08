"""
WHY: Risk Engine is stateless — same input always produces same output.
INV: priority order is fixed and must not be changed without spec update.
SEC: highest applicable risk wins; no downgrade after classification.
"""

from dataclasses import dataclass
from typing import List

RISK_LEVELS = ("low", "medium", "high", "critical")


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
    INV: critical checks happen before side-effect checks.
    SEC: secrets and secret sensitivity are absolute critical signals.
    """
    if secrets_involved:
        return RiskResult("critical", "secrets_involved=True — escalates unconditionally to critical")

    if data_sensitivity == "secret":
        return RiskResult("critical", "data_sensitivity=secret — escalates unconditionally to critical")

    destructive = {"write_files", "delete_files"}
    if destructive & set(requested_capabilities):
        return RiskResult("high", f"destructive capability requested: {sorted(destructive & set(requested_capabilities))}")

    if input_source == "untrusted":
        return RiskResult("medium", "input_source=untrusted — data must not be treated as instruction")

    if input_source not in {"local", "external", "untrusted"}:
        return RiskResult("medium", f"unknown input_source={input_source} — fail to medium")

    return RiskResult("low", "no elevated risk factors detected")
