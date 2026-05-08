"""
WHY: The governance freeze snapshot must be reviewable without adding runtime behavior.
INV: This evidence only verifies documentation integrity and invariant traceability.
SEC: Missing or duplicated critical invariants fail closed.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

REQUIRED_DOCS = [
    "GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md",
    "INVARIANT_REGISTRY.md",
    "BOUNDARY_REFERENCES.md",
    "RELEASE_REPRODUCIBILITY.md",
]

REQUIRED_INVARIANTS = [f"INV-{i:03d}" for i in range(1, 16)]
REQUIRED_BOUNDARIES = ["BOUNDARY-001", "BOUNDARY-002", "BOUNDARY-003", "BOUNDARY-004"]
FORBIDDEN_CLAIMS = [
    "autonomous planning added",
    "distributed governance: yes",
    "adapter execution: yes",
    "self-orchestration added",
]


def read_doc(name: str) -> str:
    path = DOCS / name
    assert path.exists(), f"missing freeze document: {name}"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"empty freeze document: {name}"
    return text


def main() -> None:
    docs = {name: read_doc(name) for name in REQUIRED_DOCS}
    registry = docs["INVARIANT_REGISTRY.md"]
    boundaries = docs["BOUNDARY_REFERENCES.md"]
    snapshot = docs["GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md"]

    ids = re.findall(r"INV-\d{3}", registry)
    unique_ids = sorted(set(ids))
    assert unique_ids == REQUIRED_INVARIANTS, f"invariant registry mismatch: {unique_ids}"
    assert len(ids) == len(unique_ids), "duplicate invariant IDs found"

    missing_boundaries = [b for b in REQUIRED_BOUNDARIES if b not in boundaries]
    assert not missing_boundaries, f"missing boundary references: {missing_boundaries}"

    for term in ["Fail-closed", "Replay", "append-only", "Adapter", "Governance"]:
        assert term.lower() in (snapshot + registry + boundaries).lower(), f"missing freeze term: {term}"

    combined = "\n".join(docs.values()).lower()
    leaked = [claim for claim in FORBIDDEN_CLAIMS if claim in combined]
    assert not leaked, f"forbidden capability claim found: {leaked}"

    print("PASS governance_freeze_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")


if __name__ == "__main__":
    main()
