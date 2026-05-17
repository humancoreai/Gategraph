#!/usr/bin/env python3
from __future__ import annotations
import json, tomllib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.16.4_CANDIDATE"
EXPECTED_BASE = "v0.16.3_STABLE"
def main():
    cfg = ROOT/"config.example.yaml"
    assert cfg.exists()
    text = cfg.read_text(encoding="utf-8")
    required = ["mode:", "db_path:", "actor_id:", "system_budget_units:", "session_budget:", "flood_guard:", "runtime_budget:"]
    missing = [x for x in required if x not in text]
    assert not missing, missing
    pyproject = tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == "0.16.4"
    metadata = json.loads((ROOT/"RELEASE_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["release"] == EXPECTED_RELEASE
    assert metadata["base"] == EXPECTED_BASE
    assert metadata["config_consistency_scope"] is True
    assert metadata["runtime_logic_changed"] is False
    manifest = json.loads((ROOT/"RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    paths = [e["path"] for e in manifest["files"]]
    for path in ["pyproject.toml", "config.example.yaml", "docs/STARTUP_SURFACE.md", "tests/startup_surface_evidence.py", "tests/config_consistency_evidence.py"]:
        assert path in paths
    forbidden = [p for p in paths if p.startswith("dist/") or p.startswith("tests/logs/") or p == "ARTIFACTS.sha256" or p.endswith((".db",".csv",".pyc",".pyo",".log",".tmp",".zip"))]
    assert not forbidden, forbidden
    print(json.dumps({"config_consistency": {"release": EXPECTED_RELEASE, "base": EXPECTED_BASE, "manifest_files": len(paths)}}, indent=2, sort_keys=True))
    print("PASS config_consistency_evidence")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

# Current release surface: v0.16.4_CANDIDATE
