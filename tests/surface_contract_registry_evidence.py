#!/usr/bin/env python3
"""
WHY: Governance surfaces need explicit drift evidence before they are treated as stable integration points.
INV: Surface contracts are descriptive compatibility artifacts; they never authorize, mutate, or execute governance.
SEC: Contract drift fails closed so hidden field/type changes cannot silently become operator or runtime assumptions.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "contracts"
EXPECTED_VERSION = "0.13.4"
EXPECTED_CONTRACTS = {
    "governance_decision.schema.json": {"surface": "governance_decision", "required_fields": {"decision_id": "string", "task_id": "string", "decision": "string", "risk_level": "string", "selected_rule_id": "string_or_null", "matched_rule_ids": "array[string]", "token_issued": "boolean", "event_id": "string", "schema_version": "string"}},
    "normalized_reason.schema.json": {"surface": "normalized_reason", "required_fields": {"code": "string", "category": "string", "severity": "string", "stage": "string", "message": "string", "raw_reason": "string", "priority": "integer"}},
    "monitoring_export.schema.json": {"surface": "monitoring_export", "required_fields": {"schema_version": "string", "generated_at": "string", "summary": "object", "incidents": "array[object]", "alerts": "array[object]", "aggregated_alerts": "array[object]", "budget_snapshot": "object"}},
    "capability_token_claims.schema.json": {"surface": "capability_token_claims", "required_fields": {"token_id": "string", "task_id": "string", "actor_id": "string", "capabilities": "object", "budget_scope_id": "string_or_null", "expires_at": "string", "kid": "string", "signature": "string"}},
}


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["release"] == "v0.13.4_CANDIDATE"
    assert metadata["status"] == "candidate"
    assert metadata["base"] == "v0.13.3_STABLE"
    assert metadata["surface_contract_registry_scope"] is True
    assert metadata["surface_contract_version"] == EXPECTED_VERSION
    assert metadata["governance_logic_changed"] is False
    assert metadata["runtime_logic_changed"] is False
    assert metadata["enforcement_logic_changed"] is False
    checked = []
    for filename, expected in EXPECTED_CONTRACTS.items():
        path = CONTRACT_DIR / filename
        assert path.exists(), f"missing contract: {filename}"
        contract = json.loads(path.read_text(encoding="utf-8"))
        assert contract.get("schema_version") == EXPECTED_VERSION, filename
        assert contract.get("surface") == expected["surface"], filename
        assert contract.get("status") == "frozen_stable", filename
        assert contract.get("required_fields") == expected["required_fields"], filename
        if filename == "governance_decision.schema.json":
            assert contract.get("optional_fields", {}).get("block_reason") == "string_or_null", filename
        assert contract.get("description"), filename
        checked.append(contract["surface"])
    docs = (ROOT / "docs" / "GOVERNANCE_SURFACE_FREEZE.md").read_text(encoding="utf-8")
    assert "must not become a second source of governance authority" in docs
    assert "no LLM-based enforcement" in docs
    print({"surface_contract_registry": {"version": EXPECTED_VERSION, "checked": checked}})
    print("PASS surface_contract_registry_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
