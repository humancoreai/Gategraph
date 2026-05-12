"""
WHY: Final consolidation must verify release structure without adding governance behavior.
INV: This evidence script is read-only; it checks metadata and manifest shape only.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ROOT = [
    "VERSION.md",
    "RELEASE_STATUS.md",
    "RELEASE_NOTES.md",
    "README.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "PRODUCTION.md",
    "src",
    "tests",
]

REQUIRED_EVIDENCE = [
    "drift_detection_evidence",
    "governance_archive_replay_evidence",
    "archive_integrity_replay_consistency_evidence",
    "operator_export_evidence",
    "governance_freeze_evidence",
    "runtime_boundary_hardening_evidence",
    "api_boundary_split_evidence",
    "freeze_runtime_invariant_evidence",
    "runtime_chain_order_evidence",
    "startup_surface_evidence",
    "config_consistency_evidence",
    "mode_boundary_surface_evidence",
    "token_exposure_evidence",
    "multi_agent_delegation_boundary_evidence",
    "context_poisoning_evidence",
    "instruction_data_separation_evidence",
    "context_provenance_evidence",
    "context_lifecycle_evidence",
    "context_replay_explain_boundary_evidence",
    "context_freeze_coupling_evidence",
]

FORBIDDEN_RELEASE_FIELDS = [
    "risk_level",
    "severity",
    "recommended_action",
    "requires_attention",
]


def main() -> None:
    missing = [name for name in REQUIRED_ROOT if not (ROOT / name).exists()]
    assert not missing, f"missing required release entries: {missing}"

    version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
    status = (ROOT / "RELEASE_STATUS.md").read_text(encoding="utf-8")
    assert "v0.15.8_CANDIDATE" in version
    assert "v0.15.7_STABLE" in version
    assert "Stale-token revocation after controlled rule hardening" in status

    manifest = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    missing_evidence = [name for name in REQUIRED_EVIDENCE if name not in manifest]
    assert not missing_evidence, f"missing late-stage evidence entries: {missing_evidence}"

    combined = (version + "\n" + status).lower()
    leaked = [field for field in FORBIDDEN_RELEASE_FIELDS if field in combined]
    assert not leaked, f"forbidden normative release fields found: {leaked}"

    print("PASS final_consolidation_evidence")


if __name__ == "__main__":
    main()

# Current release surface: v0.15.8_CANDIDATE
