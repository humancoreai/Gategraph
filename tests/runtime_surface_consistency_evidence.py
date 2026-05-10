#!/usr/bin/env python3
"""
WHY: Config/runtime mismatches must be detected without adding new runtime policy.
INV: Detection-only evidence; no governance, enforcement or adapter logic is changed.
SEC: Unknown modes, unknown sections and invalid budgets fail closed before execution.
"""
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPECTED_RELEASE = "v0.13.1_CANDIDATE"
EXPECTED_BASE = "v0.13.0_STABLE"


def expect_error(text: str, fragment: str) -> None:
    from src.config_loader import _config_from_dict, _parse_simple_yaml

    try:
        _config_from_dict(_parse_simple_yaml(text))
    except ValueError as exc:
        assert fragment in str(exc), str(exc)
        return
    raise AssertionError(f"config unexpectedly accepted; expected error containing {fragment!r}")


def main() -> int:
    from src.config_loader import load_config

    cfg = load_config(ROOT / "config.example.yaml")
    assert cfg.mode == "single_node"
    assert cfg.db_path == "gategraph.db"
    assert cfg.system_budget_units > 0
    assert cfg.runtime_budget.max_steps > 0

    expect_error("mode: invalid\n", "only mode")
    expect_error("mode: single_node\nruntime_budget:\n  max_steps: 0\n", "must be positive")
    expect_error("mode: single_node\nruntime_budget:\n  unknown: 1\n", "unknown keys")
    expect_error("mode: single_node\nsession_budget: nope\n", "must be a mapping")

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == "0.13.1"
    scripts = pyproject["project"]["scripts"]
    assert scripts == {"gategraph": "src.cli:main", "gategraph-server": "src.server:main"}

    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["release"] == EXPECTED_RELEASE
    assert metadata["base"] == EXPECTED_BASE
    assert metadata["status"] == "candidate"
    assert metadata["runtime_surface_scope"] is True
    for key in ["governance_logic_changed", "runtime_logic_changed", "enforcement_logic_changed", "new_runtime_capability", "new_agentic_behavior", "new_adapter", "distributed_governance"]:
        assert metadata[key] is False, key

    doc = (ROOT / "docs" / "OPERATIONAL_BOUNDARY_TIGHTENING.md").read_text(encoding="utf-8")
    for phrase in ["Unsupported runtime mutations", "Unsupported startup overrides", "Unsupported config bypasses"]:
        assert phrase in doc

    print(json.dumps({
        "runtime_surface_consistency": {
            "release": EXPECTED_RELEASE,
            "mode": cfg.mode,
            "entry_points": sorted(scripts),
            "detection_only": True,
        }
    }, indent=2, sort_keys=True))
    print("PASS runtime_surface_consistency_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
