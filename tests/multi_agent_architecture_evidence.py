"""
WHY: v0.9.2 is an architecture/boundary phase; evidence must prove the boundary claims are explicit.
INV: This test verifies documentation constraints only and introduces no runtime governance behavior.
SEC: Multi-agent terms must not imply self-elevation, hidden communication or distributed governance.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/MULTI_AGENT_SSOT.md",
    "docs/MULTI_MODE_SSOT.md",
    "docs/DELEGATION_BOUNDARY.md",
    "docs/MULTI_AGENT_BUDGET_AUTHORITY.md",
    "docs/MULTI_AGENT_REPLAY_AUDIT.md",
    "docs/EMERGENCE_BOUNDARIES.md",
]

REQUIRED_TERMS = {
    "docs/MULTI_AGENT_SSOT.md": [
        "runtime identity",
        "not a policy authority",
        "not a budget owner",
        "Governance remains central",
    ],
    "docs/MULTI_MODE_SSOT.md": [
        "descriptive profiles",
        "can only narrow or clarify permissions",
        "governance bypass",
    ],
    "docs/DELEGATION_BOUNDARY.md": [
        "fresh governance decision",
        "equal or narrower",
        "Delegation loops must fail closed",
        "lineage cycle",
    ],
    "docs/MULTI_AGENT_BUDGET_AUTHORITY.md": [
        "Budget authority remains central",
        "may not",
        "mint budget",
        "implicit pooled budgets",
    ],
    "docs/MULTI_AGENT_REPLAY_AUDIT.md": [
        "Replay must never infer hidden state",
        "causal",
        "agent_id",
        "mode_id",
    ],
    "docs/EMERGENCE_BOUNDARIES.md": [
        "Forbidden Paths",
        "hidden agent-to-agent communication",
        "budget farming",
        "distributed governance shards",
    ],
}

FORBIDDEN_POSITIVE_CLAIMS = [
    "agents may create policy",
    "agents can expand budget",
    "distributed governance is supported",
    "self-orchestration is enabled",
    "hidden communication is allowed",
    "capability broadening is allowed",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> None:
    missing = [rel for rel in REQUIRED_DOCS if not (ROOT / rel).exists()]
    assert not missing, f"missing multi-agent architecture docs: {missing}"

    for rel, terms in REQUIRED_TERMS.items():
        text = read(rel)
        missing_terms = [term for term in terms if term.lower() not in text.lower()]
        assert not missing_terms, f"{rel} missing terms: {missing_terms}"

    combined = "\n".join(read(rel) for rel in REQUIRED_DOCS).lower()
    leaked_claims = [claim for claim in FORBIDDEN_POSITIVE_CLAIMS if claim in combined]
    assert not leaked_claims, f"forbidden positive claims found: {leaked_claims}"

    assert "Governance decides" in read("INVARIANTS.md") or "governance remains central" in combined
    assert "Replay must never infer hidden state" in read("docs/MULTI_AGENT_REPLAY_AUDIT.md")
    assert "Any path that cannot be reconstructed, budgeted, and explained must be blocked" in read("docs/EMERGENCE_BOUNDARIES.md")

    print("PASS multi_agent_architecture_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")


if __name__ == "__main__":
    main()
