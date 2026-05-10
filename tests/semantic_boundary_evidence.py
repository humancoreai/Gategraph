#!/usr/bin/env python3
"""
WHY: Surface documentation can accidentally become implied authority unless the semantic boundary is tested.
INV: Contracts, monitoring and explain surfaces remain descriptive/read-only and cannot mutate governance or runtime state.
SEC: Untrusted or external content remains data; no contract field may introduce hidden execution, repair or policy-update semantics.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "contracts"
FORBIDDEN_TERMS = {"auto_repair", "auto_execute", "execute_policy", "mutate_policy", "self_update", "llm_enforcement", "semantic_score", "trusted_instruction"}


def walk_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key)
            yield from walk_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_values(item)
    else:
        yield str(obj)


def main() -> int:
    contracts = sorted(CONTRACT_DIR.glob("*.schema.json"))
    assert contracts, "no contracts found"
    checked = []
    for path in contracts:
        payload = json.loads(path.read_text(encoding="utf-8"))
        text_values = "\n".join(walk_values(payload)).lower()
        for term in FORBIDDEN_TERMS:
            assert term not in text_values, f"forbidden semantic authority term in {path.name}: {term}"
        assert payload.get("description"), f"missing descriptive boundary: {path.name}"
        assert payload.get("status") == "frozen_stable", path.name
        if payload.get("surface") == "monitoring_export":
            assert payload.get("mutability") == "read_only"
            assert "automatic mitigation" in payload.get("non_scope", [])
        if payload.get("surface") == "capability_token_claims":
            security = payload.get("security", {})
            assert "never log full token values" in security.get("audit_logging", "")
            assert "task/scope" in security.get("replay_boundary", "")
        checked.append(path.name)
    notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "No governance logic change" in notes
    assert "No runtime/enforcement behavior change" in notes
    assert "No autonomous policy update" in notes
    assert "No semantic scoring or memory system" in notes
    print({"semantic_boundary": {"checked_contracts": checked, "authority": "descriptive_only"}})
    print("PASS semantic_boundary_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
