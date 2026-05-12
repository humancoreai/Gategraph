from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.release_constants import load_release_constants


def check(name: str, ok: bool, detail: dict):
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "registry" / "release_constant_registry.json").read_text(encoding="utf-8"))
    constants = load_release_constants(ROOT)

    checks = []

    checks.append(check(
        "constants_match_metadata",
        constants["CURRENT_RELEASE"] == metadata["release"]
        and constants["CURRENT_BASE"] == metadata["base"]
        and constants["CURRENT_STATUS"] == metadata["status"],
        {"constants": constants, "metadata_release": metadata["release"]}
    ))

    checks.append(check(
        "stable_token_matches_current_release",
        constants["FUTURE_STABLE"] == constants["CURRENT_RELEASE"],
        {"future_stable": constants["FUTURE_STABLE"]}
    ))

    checks.append(check(
        "registry_descriptive_only",
        registry["runtime_authority"] is False
        and registry["auto_repair"] is False
        and registry["auto_promotion"] is False,
        {
            "runtime_authority": registry["runtime_authority"],
            "auto_repair": registry["auto_repair"],
            "auto_promotion": registry["auto_promotion"],
        }
    ))

    failed = [name for name, ok, _ in checks if not ok]

    print("RELEASE CONSTANT REGISTRY EVIDENCE REPORT")
    print({"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
