"""
WHY: v0.9.1 is a boundary/release integrity closure; release integrity must be testable.
INV: This evidence is read-only and verifies documentation/package consistency without new governance behavior.
SEC: Hidden files and generated runtime artifacts must not enter official release packages.
"""
from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.16.6_STABLE"
BASE = "v0.16.5_STABLE"

REQUIRED_ROOT_FILES = [
    "README.md",
    "VERSION.md",
    "RELEASE_STATUS.md",
    "RELEASE_NOTES.md",
    "RELEASE_METADATA.json",
    "RELEASE_MANIFEST.json",
    "EXTERNAL_REVIEW.md",
    "ARCHITECTURE.md",
    "INVARIANTS.md",
    "NON_SCOPE.md",
    "RELEASE_CONTENT_RULES.md",
    "TRUST_MODEL.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "RELEASE_PROCESS.md",
    "LICENSE",
    "tools/build_release.py",
    "tools/verify_release.py",
    ".gitignore",
]

REQUIRED_SCOPE_FREEZE_TERMS = [
    "autonomous policy changes",
    "self-governance",
    "automatic optimization",
    "machine-learning based risk prediction",
    "adaptive intelligence",
]

FORBIDDEN_POSITIVE_CLAIMS = [
    "is an autonomous governance system",
    "is an adaptive ai safety layer",
    "is a self-correcting intelligence system",
    "is a production enterprise platform",
]

FORBIDDEN_RELEASE_SUFFIXES = {".db", ".csv", ".pyc", ".pyo", ".zip"}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_verify_module():
    spec = importlib.util.spec_from_file_location("verify_release", ROOT / "tools" / "verify_release.py")
    assert spec and spec.loader, "could not load verify_release.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_release", ROOT / "tools" / "build_release.py")
    assert spec and spec.loader, "could not load build_release.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    missing = [name for name in REQUIRED_ROOT_FILES if not (ROOT / name).exists()]
    assert not missing, f"missing required milestone files: {missing}"

    version = read("VERSION.md")
    status = read("RELEASE_STATUS.md")
    assert VERSION in version, "VERSION.md missing release identifier"
    assert BASE in version, "VERSION.md missing base identifier"
    assert VERSION in status, "RELEASE_STATUS.md missing release identifier"
    assert BASE in status, "RELEASE_STATUS.md missing base identifier"

    metadata = json.loads(read("RELEASE_METADATA.json"))
    assert metadata["phase"] in status, "RELEASE_STATUS.md missing phase label"
    assert metadata["release"] == VERSION
    assert metadata["base"] == BASE
    assert metadata["governance_logic_changed"] is False
    assert metadata["new_governance_features"] is False
    assert metadata["scope_freeze"] is True
    assert metadata["distributed_governance"] is False
    assert metadata["self_orchestration"] is False

    non_scope = read("NON_SCOPE.md").lower()
    missing_terms = [term for term in REQUIRED_SCOPE_FREEZE_TERMS if term not in non_scope]
    assert not missing_terms, f"missing scope-freeze terms: {missing_terms}"

    combined_docs = "\n".join(read(name) for name in [
        "README.md",
        "EXTERNAL_REVIEW.md",
        "ARCHITECTURE.md",
        "INVARIANTS.md",
        "NON_SCOPE.md",
        "RELEASE_NOTES.md",
    ]).lower()
    leaked_claims = [claim for claim in FORBIDDEN_POSITIVE_CLAIMS if claim in combined_docs]
    assert not leaked_claims, f"forbidden positive capability claims found: {leaked_claims}"

    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    assert manifest["release"] == VERSION
    assert manifest["base"] == BASE
    assert manifest["deterministic_packaging"] is True
    paths = [entry["path"] for entry in manifest["files"]]
    assert paths == sorted(paths), "release manifest file order is not deterministic"
    assert "src/governance.py" in paths
    assert "tests/evidence_ci.py" in paths
    assert "tests/milestone_release_evidence.py" in paths
    assert "tests/caller_boundary_evidence.py" in paths
    assert "tests/release_integrity_evidence.py" in paths
    assert "tests/runtime_boundary_hardening_evidence.py" in paths
    assert "tests/runtime_chain_order_evidence.py" in paths
    assert "pyproject.toml" in paths
    assert "docs/DEPLOYMENT_BOUNDARY.md" in paths
    assert "tests/packaging_integrity_evidence.py" in paths
    assert "tests/install_surface_evidence.py" in paths
    assert "tests/multi_agent_architecture_evidence.py" in paths
    assert "docs/MULTI_AGENT_SSOT.md" in paths
    assert "docs/MULTI_MODE_SSOT.md" in paths
    assert "docs/MODE_BOUNDARY_SURFACE.md" in paths
    assert "tests/mode_boundary_surface_evidence.py" in paths
    assert "docs/DELEGATION_BOUNDARY.md" in paths
    assert "docs/MULTI_AGENT_BUDGET_AUTHORITY.md" in paths
    assert "docs/MULTI_AGENT_REPLAY_AUDIT.md" in paths
    assert "docs/EMERGENCE_BOUNDARIES.md" in paths
    assert "docs/RUNTIME_BOUNDARY_HARDENING.md" in paths
    assert "docs/RUNTIME_CHAIN_ASSERTIONS.md" in paths
    assert "src/runtime_path_assertions.py" in paths
    assert "src/runtime_chain_assertions.py" in paths
    assert "TRUST_MODEL.md" in paths
    assert "CONTEXT_GOVERNANCE_MODEL.md" in paths
    assert "gategraph/context/context_classifier.py" in paths
    assert "gategraph/context/context_boundary.py" in paths
    assert "gategraph/context/context_lifecycle.py" in paths
    assert "docs/CONTEXT_LIFECYCLE_MODEL.md" in paths
    forbidden_manifest = [
        p for p in paths
        if Path(p).suffix.lower() in FORBIDDEN_RELEASE_SUFFIXES
        or (any(part.startswith(".") for part in Path(p).parts) and p != ".gitignore" and not p.startswith(".github/workflows/"))
    ]
    assert not forbidden_manifest, f"forbidden manifest entries found: {forbidden_manifest}"

    ci_manifest = read("tests/evidence_ci.py")
    assert "milestone_release_evidence" in ci_manifest
    assert "caller_boundary_evidence" in ci_manifest
    assert "release_integrity_evidence" in ci_manifest
    assert "multi_agent_architecture_evidence" in ci_manifest
    assert "runtime_boundary_hardening_evidence" in ci_manifest
    assert "runtime_chain_order_evidence" in ci_manifest
    assert "mode_boundary_surface_evidence" in ci_manifest
    assert "context_poisoning_evidence" in ci_manifest
    assert "instruction_data_separation_evidence" in ci_manifest
    assert "context_provenance_evidence" in ci_manifest
    assert "context_lifecycle_evidence" in ci_manifest
    assert "context_replay_explain_boundary_evidence" in ci_manifest
    assert "context_freeze_coupling_evidence" in ci_manifest

    zip_path = ROOT / "dist" / f"GateGraph_{VERSION}.zip"
    if zip_path.exists():
        # WHY: Evidence CI may start from a downloaded candidate with a stale or user-modified
        # dist ZIP. Rebuild before verifying so milestone evidence checks the current tree,
        # while release_integrity_evidence remains the canonical packaging gate.
        builder = load_build_module()
        build_rc = builder.main()
        assert build_rc == 0, "build_release did not complete before milestone zip verification"
        verifier = load_verify_module()
        result = verifier.verify(zip_path)
        assert result["passed"], result["errors"]
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert names == sorted(names), "zip entries are not sorted"
        assert all(name.startswith(f"GateGraph_{VERSION}/") for name in names), "zip entry outside release root prefix"

    print("PASS milestone_release_evidence")


if __name__ == "__main__":
    main()

# Current release surface: v0.16.6_STABLE
