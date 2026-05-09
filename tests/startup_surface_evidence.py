#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tomllib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPECTED_RELEASE = "v0.11.8_STABLE"
EXPECTED_BASE = "v0.11.7_STABLE"
def main():
    pyproject = tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    assert scripts["gategraph"] == "src.cli:main"
    assert scripts["gategraph-server"] == "src.server:main"
    import src.cli as cli, src.server as server
    assert hasattr(cli, "main")
    assert hasattr(server, "main")
    metadata = json.loads((ROOT/"RELEASE_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["release"] == EXPECTED_RELEASE
    assert metadata["base"] == EXPECTED_BASE
    assert metadata["startup_surface_scope"] is True
    assert metadata["governance_logic_changed"] is False
    assert metadata["runtime_logic_changed"] is False
    doc = (ROOT/"docs"/"STARTUP_SURFACE.md").read_text(encoding="utf-8")
    for phrase in ["Canonical start paths", "python -m pip install -e .", "gategraph --help", "No telemetry stack"]:
        assert phrase in doc
    print(json.dumps({"startup_surface": {"release": EXPECTED_RELEASE, "base": EXPECTED_BASE, "cli_main": "present", "server_main": "present"}}, indent=2, sort_keys=True))
    print("PASS startup_surface_evidence")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
