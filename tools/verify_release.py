"""
WHY: Reviewers need a local, deterministic way to verify a release ZIP.
INV: Verification is read-only and never repairs packages silently.
SEC: Manifest, archive content, hashes and deterministic ZIP metadata are checked fail-closed.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

VERSION = "v0.16.7_STABLE"
EXPECTED_PREFIX = f"GateGraph_{VERSION}/"
FIXED_ZIP_DT = (2026, 1, 1, 0, 0, 0)
FORBIDDEN_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode", "dist"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".db", ".csv", ".zip", ".tmp", ".temp", ".log"}
FORBIDDEN_NAMES = {"gategraph.db", "gategraph.db-journal", "gategraph.db-wal", "gategraph.db-shm", ".DS_Store", "Thumbs.db"}
REQUIRED = {
    "tests/release_status_token_centralization_evidence.py",
    "docs/RELEASE_STATUS_TOKEN_CENTRALIZATION.md",
    "registry/release_status_token_registry.json",
    "registry/failure_root_cause_grouping.json",
    "tests/fresh_clone_surface_validation_evidence.py",
    "tests/artifact_determinism_evidence.py",
    "tests/failure_root_cause_grouping_evidence.py",
    "docs/FRESH_CLONE_SURFACE_VALIDATION.md",
    "docs/ARTIFACT_DETERMINISM.md",
    "docs/FAILURE_ROOT_CAUSE_GROUPING.md",
    "VERSION.md",
    "RELEASE_METADATA.json",
    "RELEASE_MANIFEST.json",
    "TRUST_MODEL.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "RELEASE_PROCESS.md",
    "LICENSE",
    "tools/build_release.py",
    "tools/verify_release.py",
    "tests/caller_boundary_evidence.py",
    "tests/release_integrity_evidence.py",
    "tests/runtime_boundary_hardening_evidence.py",
    "tests/freeze_runtime_invariant_evidence.py",
    "tests/api_boundary_split_evidence.py",
    "tests/runtime_chain_order_evidence.py",
    "tests/multi_agent_architecture_evidence.py",
    "docs/MULTI_AGENT_SSOT.md",
    "docs/MULTI_MODE_SSOT.md",
    "docs/DELEGATION_BOUNDARY.md",
    "docs/MULTI_AGENT_BUDGET_AUTHORITY.md",
    "docs/MULTI_AGENT_REPLAY_AUDIT.md",
    "docs/EMERGENCE_BOUNDARIES.md",
    "docs/GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md",
    "docs/INVARIANT_REGISTRY.md",
    "docs/BOUNDARY_REFERENCES.md",
    "docs/RELEASE_REPRODUCIBILITY.md",
    "docs/RUNTIME_BOUNDARY_HARDENING.md",
    "docs/RUNTIME_CHAIN_ASSERTIONS.md",
    "docs/RUNTIME_SURFACE_FREEZE.md",
    "docs/OPERATIONAL_BOUNDARY_TIGHTENING.md",
    "tests/startup_shutdown_semantics_evidence.py",
    "tests/runtime_surface_consistency_evidence.py",
    "tests/surface_freeze_coupling_evidence.py",
    "src/runtime_path_assertions.py",
    "src/runtime_chain_assertions.py",
    "src/api_boundary.py",
    "tests/governance_freeze_evidence.py",
    "SECURITY_MODEL.md",
    "OWASP_AGENTIC_AI_MAPPING.md",
    "KNOWN_LIMITATIONS.md",
    "docs/RELEASE_v0.16.7_STABLE.md",
    "tests/release_claim_consistency_evidence.py",
    "src/security/__init__.py",
    "src/security/token_redaction.py",
    "tests/token_exposure_evidence.py",
    "CONTEXT_GOVERNANCE_MODEL.md",
    "gategraph/__init__.py",
    "gategraph/context/__init__.py",
    "gategraph/context/context_classifier.py",
    "gategraph/context/context_boundary.py",
    "tests/context_poisoning_evidence.py",
    "tests/instruction_data_separation_evidence.py",
    "tests/context_provenance_evidence.py",
    "docs/RELEASE_v0.16.7_STABLE.md",
    "docs/GOVERNANCE_SURFACE_FREEZE.md",
    "contracts/governance_decision.schema.json",
    "contracts/normalized_reason.schema.json",
    "contracts/monitoring_export.schema.json",
    "contracts/capability_token_claims.schema.json",
    "tests/surface_contract_registry_evidence.py",
    "tests/semantic_boundary_evidence.py",
    "src/recovery_foundation.py",
    "tests/recovery_foundation_evidence.py",
    "tests/replay_recovery_consistency_evidence.py",
    "tests/surface_recovery_consistency_evidence.py",
    "tests/recovery_idempotency_evidence.py",
    "tests/replay_order_determinism_evidence.py",
    "tests/recovery_surface_registry_evidence.py",
    "tests/release_surface_sync_evidence.py",
    "tests/replay_reference_integrity_evidence.py",
    "tests/recovery_replay_finality_evidence.py",
    "docs/RECOVERY_FOUNDATION.md",
    "docs/RECOVERY_REPLAY_FINALITY.md",
    "src/semantic_registry_lock.py",
    "registry/semantic_registry_lock.json",
    "registry/semantic_object_types.json",
    "registry/invariant_surface_registry.json",
    "tests/semantic_registry_lock_evidence.py",
    "tests/release_manifest_coverage_evidence.py",
    "docs/RELEASE_v0.16.7_STABLE.md",
    "registry/schema_governance_registry.json",
    "docs/SCHEMA_GOVERNANCE.md",
    "docs/RELEASE_v0.16.7_STABLE.md",
    "tests/schema_governance_evidence.py",
    "tests/cross_registry_integrity_evidence.py",
    "tests/deterministic_export_contract_evidence.py",
    "tests/schema_drift_visibility_evidence.py",
    "tests/freeze_snapshot_determinism_evidence.py",
    "tests/replay_provenance_consistency_evidence.py",
    "tests/governance_mutation_visibility_evidence.py",
    "tests/dependency_visibility_evidence.py",
    "tests/governance_lineage_snapshot_evidence.py",
    "tests/evidence_provenance_registry_evidence.py",
    "docs/EVIDENCE_PROVENANCE.md",
    "registry/governance_lineage.json",
    "registry/evidence_provenance_registry.json",
    "registry/release_state_transition_registry.json",
    "tests/release_state_transition_evidence.py",
    "tests/promotion_surface_symmetry_evidence.py",
    "tests/candidate_stable_surface_parity_evidence.py",
    "registry/governance_integrity_graph.json",
    "docs/GOVERNANCE_INTEGRITY_GRAPH.md",
    "tests/governance_integrity_graph_evidence.py",
    "tests/orphan_governance_artifact_evidence.py",
    "tests/governance_impact_visibility_evidence.py",
    "tests/integrity_graph_freeze_evidence.py",
    "tests/deterministic_governance_diff_evidence.py",
    "docs/RELEASE_STATE_TRANSITION.md",
    "tests/evidence_failure_classification_evidence.py",
    "registry/evidence_failure_classification.json",
    "docs/EVIDENCE_FAILURE_CLASSIFICATION.md",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_name(full_name: str) -> str:
    return full_name.removeprefix(EXPECTED_PREFIX)


def _entry_errors(name: str, date_time: tuple[int, int, int, int, int, int]) -> list[str]:
    errors: list[str] = []
    rel = _relative_name(name)
    path = Path(rel)
    parts = path.parts
    if not name.startswith(EXPECTED_PREFIX):
        errors.append(f"entry outside expected prefix: {name}")
    if not rel or rel.endswith("/"):
        errors.append(f"directory/empty entry found: {name}")
    if any(part.startswith(".") for part in parts) and rel != ".gitignore" and not rel.startswith(".github/workflows/"):
        errors.append(f"hidden entry found: {name}")
    if set(parts) & FORBIDDEN_PARTS:
        errors.append(f"forbidden path part found: {name}")
    if path.name in FORBIDDEN_NAMES:
        errors.append(f"forbidden file name found: {name}")
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        errors.append(f"forbidden suffix found: {name}")
    if rel.startswith("tests/logs/") and path.name != ".gitkeep":
        errors.append(f"test log artifact found: {name}")
    if date_time != FIXED_ZIP_DT:
        errors.append(f"non-deterministic timestamp: {name}")
    return errors


def verify(zip_path: Path) -> dict:
    errors: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        infos = zf.infolist()
        names = [i.filename for i in infos]
        if not names:
            errors.append("zip is empty")
        if len(names) != len(set(names)):
            errors.append("zip contains duplicate entries")
        if names != sorted(names):
            errors.append("zip entries are not lexicographically sorted")
        for info in infos:
            errors.extend(_entry_errors(info.filename, info.date_time))

        rel_names = [_relative_name(name) for name in names if name.startswith(EXPECTED_PREFIX)]
        missing_required = sorted(REQUIRED - set(rel_names))
        if missing_required:
            errors.append(f"missing required entries: {missing_required}")

        manifest_name = f"{EXPECTED_PREFIX}RELEASE_MANIFEST.json"
        if manifest_name not in names:
            errors.append("missing release manifest")
            manifest = None
        else:
            manifest = json.loads(zf.read(manifest_name).decode("utf-8"))

        if manifest is not None:
            if manifest.get("release") != VERSION:
                errors.append("manifest release mismatch")
            entries = manifest.get("files", [])
            if not isinstance(entries, list) or not entries:
                errors.append("manifest file list is empty or invalid")
                entries = []
            manifest_paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
            if len(manifest_paths) != len(set(manifest_paths)):
                errors.append("manifest contains duplicate paths")
            if manifest.get("file_count") != len(entries):
                errors.append("manifest file_count mismatch")

            zip_declared_paths = set(rel_names) - {"RELEASE_MANIFEST.json"}
            manifest_path_set = set(p for p in manifest_paths if isinstance(p, str))
            missing_in_zip = sorted(manifest_path_set - zip_declared_paths)
            undeclared_in_manifest = sorted(zip_declared_paths - manifest_path_set)
            if missing_in_zip:
                errors.append(f"manifest paths missing in zip: {missing_in_zip}")
            if undeclared_in_manifest:
                errors.append(f"zip contains undeclared files: {undeclared_in_manifest}")

            for entry in entries:
                if not isinstance(entry, dict):
                    errors.append("manifest contains non-object entry")
                    continue
                p = entry.get("path")
                full = f"{EXPECTED_PREFIX}{p}"
                if not isinstance(p, str) or full not in names:
                    continue
                data = zf.read(full)
                if len(data) != entry.get("size"):
                    errors.append(f"size mismatch: {p}")
                if sha256_bytes(data) != entry.get("sha256"):
                    errors.append(f"hash mismatch: {p}")
    return {"passed": not errors, "errors": errors, "entry_count": len(names) if 'names' in locals() else 0}


def main(argv: list[str]) -> int:
    zip_path = Path(argv[1]) if len(argv) > 1 else Path("dist") / f"GateGraph_{VERSION}.zip"
    result = verify(zip_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

# RELEASE_BASE = "v0.16.7_STABLE"

# Base: v0.16.7_STABLE

# Base: v0.16.6_STABLE
