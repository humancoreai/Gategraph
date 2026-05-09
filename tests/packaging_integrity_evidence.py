#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.11.1_CANDIDATE"
EXPECTED_BASE = "v0.11.0_STABLE"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"

    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["name"] == "gategraph"
    assert project["version"] == "0.11.1"
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

    forbidden = [
        path for path in paths
        if path.startswith("dist/")
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
