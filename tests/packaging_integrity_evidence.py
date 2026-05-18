#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.17.0_CANDIDATE"
EXPECTED_BASE = "v0.16.9_STABLE"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"

    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["name"] == "gategraph"
    assert project["version"] == "0.17.0"
    assert project["requires-python"] == ">=3.11"
    assert project.get("dependencies", []) == []

    scripts = project.get("scripts", {})
    assert scripts["gategraph"] == "src.cli:main"
    assert scripts["gategraph-server"] == "src.server:main"

    metadata = json.loads(read("RELEASE_METADATA.json"))
    assert metadata["release"] == EXPECTED_RELEASE
    assert metadata["base"] == EXPECTED_BASE
    assert metadata["packaging_scope"] is True
    assert metadata["governance_logic_changed"] is False
    assert metadata["runtime_logic_changed"] is False
    assert metadata["enforcement_logic_changed"] is False
    assert metadata["new_agentic_behavior"] is False
    assert metadata["distributed_governance"] is False

    readme = read("README.md")
    assert "Base stable: **v0.16.9_STABLE**" in readme
    assert "Canonical runtime namespace" in readme
    assert "`src/` package is the canonical runtime/governance surface" in readme
    assert "OWASP_AGENTIC_AI_MAPPING.md" in readme

    deploy = read("docs/DEPLOYMENT_BOUNDARY.md")
    required_phrases = [
        "Single-node CLI execution",
        "Local/protected HTTP server",
        "Direct public internet exposure",
        "Packaging must not create an alternative governance path",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in deploy]
    assert not missing, f"deployment boundary missing phrases: {missing}"

    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    assert manifest["release"] == EXPECTED_RELEASE
    assert manifest["base"] == EXPECTED_BASE
    paths = [entry["path"] for entry in manifest["files"]]
    assert "pyproject.toml" in paths
    assert "docs/DEPLOYMENT_BOUNDARY.md" in paths
    assert "tests/packaging_integrity_evidence.py" in paths
    assert "tests/install_surface_evidence.py" in paths
    assert "SECURITY_MODEL.md" in paths
    assert "OWASP_AGENTIC_AI_MAPPING.md" in paths
    assert "KNOWN_LIMITATIONS.md" in paths
    assert "src/security/token_redaction.py" in paths
    assert "tests/token_exposure_evidence.py" in paths
    assert "src/multi_agent_delegation.py" in paths
    assert "tests/multi_agent_delegation_boundary_evidence.py" in paths
    assert "docs/MULTI_AGENT_DELEGATION_BOUNDARY.md" in paths
    assert "CONTEXT_GOVERNANCE_MODEL.md" in paths
    assert "gategraph/context/context_classifier.py" in paths
    assert "gategraph/context/context_boundary.py" in paths
    assert "tests/context_poisoning_evidence.py" in paths
    assert "tests/instruction_data_separation_evidence.py" in paths
    assert "tests/context_provenance_evidence.py" in paths
    assert "tests/release_content_hygiene_evidence.py" in paths
    assert "docs/GOVERNANCE_SURFACE_FREEZE.md" in paths
    assert "contracts/governance_decision.schema.json" in paths
    assert "contracts/normalized_reason.schema.json" in paths
    assert "contracts/monitoring_export.schema.json" in paths
    assert "contracts/capability_token_claims.schema.json" in paths
    assert "tests/surface_contract_registry_evidence.py" in paths
    assert "tests/semantic_boundary_evidence.py" in paths
    assert "src/recovery_foundation.py" in paths
    assert "tests/recovery_foundation_evidence.py" in paths
    assert "docs/RECOVERY_FOUNDATION.md" in paths
    assert not any(Path(path).name.upper().startswith("STARTPROMPT") for path in paths)

    forbidden = [
        path for path in paths
        if Path(path).name.upper().startswith("STARTPROMPT")
        or path.startswith("dist/")
        or path.startswith("tests/logs/")
        or path == "ARTIFACTS.sha256"
        or path.endswith((".db", ".csv", ".pyc", ".pyo", ".log", ".tmp", ".zip"))
    ]
    assert not forbidden, f"forbidden package artifacts in manifest: {forbidden}"

    print(json.dumps({
        "packaging_integrity": {
            "release": EXPECTED_RELEASE,
            "base": EXPECTED_BASE,
            "package": project["name"],
            "version": project["version"],
            "entry_points": scripts,
            "manifest_files": len(paths),
        }
    }, indent=2, sort_keys=True))
    print("PASS packaging_integrity_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
