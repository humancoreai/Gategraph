"""
WHY: Test evidence is generated outside the core so Governance/Enforcement/Runtime semantics stay unchanged.
INV: this module only reads existing DB records and writes JSON evidence files under tests/logs/.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _rows(conn, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def collect_task_evidence(conn, task_id: str) -> Dict[str, Any]:
    events = _rows(
        conn,
        """
        SELECT event_id, type, timestamp, task_id, actor_layer, actor_component,
               input_json, evaluation_json, decision_json
        FROM events
        WHERE task_id = ?
        ORDER BY timestamp, event_id
        """,
        (task_id,),
    )
    for event in events:
        event["input"] = _json_loads(event.pop("input_json", None))
        event["evaluation"] = _json_loads(event.pop("evaluation_json", None))
        event["decision"] = _json_loads(event.pop("decision_json", None))

    runtime_decisions = _rows(
        conn,
        """
        SELECT decision_id, task_id, step_id, decision, reason, created_at
        FROM runtime_decisions
        WHERE task_id = ?
        ORDER BY created_at, decision_id
        """,
        (task_id,),
    )
    runtime_steps = _rows(
        conn,
        """
        SELECT step_id, task_id, step_index, actor_id, action_type,
               action_signature, cost_units, timestamp
        FROM runtime_steps
        WHERE task_id = ?
        ORDER BY step_index, timestamp
        """,
        (task_id,),
    )
    decisions = _rows(
        conn,
        """
        SELECT decision_id, task_id, event_id, status, final_caps_json, reason,
               matched_rules_json, created_at
        FROM decisions
        WHERE task_id = ?
        ORDER BY created_at, decision_id
        """,
        (task_id,),
    )
    for decision in decisions:
        decision["final_caps"] = _json_loads(decision.pop("final_caps_json", None))
        decision["matched_rules"] = _json_loads(decision.pop("matched_rules_json", None))

    tokens = _rows(
        conn,
        """
        SELECT token_id, decision_id, task_id, capabilities, issued_at, expires_at, revoked
        FROM capability_tokens
        WHERE task_id = ?
        ORDER BY issued_at, token_id
        """,
        (task_id,),
    )
    for token in tokens:
        token["capabilities"] = _json_loads(token.get("capabilities"))
        token["revoked"] = bool(token.get("revoked"))

    return {
        "task_id": task_id,
        "events": events,
        "runtime_decisions": runtime_decisions,
        "runtime_steps": runtime_steps,
        "governance_decisions": decisions,
        "capability_tokens": tokens,
        "audit_refs": {
            "event_ids": [e["event_id"] for e in events],
            "runtime_decision_ids": [d["decision_id"] for d in runtime_decisions],
            "runtime_step_ids": [s["step_id"] for s in runtime_steps],
            "governance_decision_ids": [d["decision_id"] for d in decisions],
            "token_ids": [t["token_id"] for t in tokens],
        },
    }


def collect_global_evidence(conn) -> Dict[str, Any]:
    proposals = _rows(
        conn,
        """
        SELECT proposal_id, proposal_type, target_rule_id, reason, proposed_change,
               supporting_events, confidence, confidence_basis, status, created_at
        FROM proposals
        ORDER BY created_at, proposal_id
        """,
    )
    for proposal in proposals:
        proposal["supporting_events"] = _json_loads(proposal.get("supporting_events"))
        proposal["proposed_change"] = _json_loads(proposal.get("proposed_change"))
    return {"proposals": proposals}



def collect_session_evidence(conn, session_id: str) -> Dict[str, Any]:
    budgets = _rows(
        conn,
        """
        SELECT session_id, max_session_cost_units, max_session_tasks,
               max_agent_cost_units, created_at
        FROM session_budgets
        WHERE session_id = ?
        """,
        (session_id,),
    )
    links = _rows(
        conn,
        """
        SELECT session_id, task_id, actor_id, created_at
        FROM session_task_links
        WHERE session_id = ?
        ORDER BY created_at, task_id
        """,
        (session_id,),
    )
    decisions = _rows(
        conn,
        """
        SELECT decision_id, session_id, task_id, actor_id, projected_cost_units,
               decision, reason, created_at
        FROM session_budget_decisions
        WHERE session_id = ?
        ORDER BY created_at, decision_id
        """,
        (session_id,),
    )
    return {
        "session_id": session_id,
        "session_budgets": budgets,
        "session_task_links": links,
        "session_budget_decisions": decisions,
        "audit_refs": {
            "session_budget_decision_ids": [d["decision_id"] for d in decisions],
            "linked_task_ids": [l["task_id"] for l in links],
        },
    }

@dataclass
class EvidenceScenarioResult:
    test_name: str
    description: str
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    passed: bool
    severity: str = "info"
    notes: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceRunLog:
    run_id: str
    started_at: str
    finished_at: Optional[str] = None
    summary: Dict[str, int] = field(default_factory=lambda: {"total": 0, "passed": 0, "failed": 0, "findings": 0})
    tests: List[EvidenceScenarioResult] = field(default_factory=list)

    def add(self, result: EvidenceScenarioResult) -> None:
        self.tests.append(result)
        self.summary["total"] += 1
        if result.passed:
            self.summary["passed"] += 1
        else:
            self.summary["failed"] += 1
        if result.severity in {"low", "medium", "high", "critical"}:
            self.summary["findings"] += 1

    def finish(self) -> None:
        self.finished_at = utc_now_iso()

    def write(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{self.run_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        return path
