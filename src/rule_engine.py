"""
WHY: Rule Engine must be fully deterministic — same input, same rules -> same output.
INV: sort order (severity DESC, decision DESC, priority DESC, rule_id ASC) is canonical.
SEC: conflict resolution always escalates, never downgrades.
"""

import json
from dataclasses import dataclass
from typing import List, Optional
import sqlite3

DECISION_RANK = {
    "block": 50,
    "require_approval": 40,
    "require_review": 30,
    "warn": 20,
    "allow": 10,
}

SEVERITY_RANK = {
    "critical": 40,
    "high": 30,
    "medium": 20,
    "low": 10,
}


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    severity: str
    decision: str
    priority: int
    rationale: str


@dataclass(frozen=True)
class RuleEngineResult:
    final_decision: str
    selected_rule_id: Optional[str]
    matched_rules: List[RuleMatch]
    conflict_resolved: bool


def evaluate(conn: sqlite3.Connection, requested_capabilities: List[str], risk_level: str) -> RuleEngineResult:
    rows = conn.execute(
        """
        SELECT rule_id, severity, decision, priority, trigger_caps, risk_threshold, rationale
        FROM rules WHERE active = 1
        """
    ).fetchall()

    requested = set(requested_capabilities) if requested_capabilities else {"__empty__"}
    matched: List[RuleMatch] = []

    for row in rows:
        trigger_caps = set(json.loads(row["trigger_caps"]))
        capability_match = bool(trigger_caps & requested)
        risk_sufficient = SEVERITY_RANK.get(risk_level, 0) >= SEVERITY_RANK.get(row["risk_threshold"], 0)
        if capability_match and risk_sufficient:
            matched.append(RuleMatch(row["rule_id"], row["severity"], row["decision"], row["priority"], row["rationale"]))

    # SEC: any unknown requested capability fails closed via synthetic block match.
    known_caps = {"read_files", "write_files", "delete_files", "api_call"}
    if requested and not requested <= (known_caps | {"__empty__"}):
        matched.append(RuleMatch("RULE-SYNTH-UNKNOWN", "high", "block", 10_000, "unknown capability — fail-closed"))

    if not matched:
        return RuleEngineResult("block", None, [], False)

    sorted_rules = sorted(
        matched,
        key=lambda r: (
            -SEVERITY_RANK.get(r.severity, 0),
            -DECISION_RANK.get(r.decision, 0),
            -r.priority,
            r.rule_id,
        ),
    )
    selected = sorted_rules[0]
    return RuleEngineResult(selected.decision, selected.rule_id, matched, len(matched) > 1)
