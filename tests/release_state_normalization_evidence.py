from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import release_state_normalizer as normalizer

def main() -> int:
    checks=[]
    report=normalizer.validate_release_state()
    checks.append(("release_state_normalized", report["ok"], report))
    state=normalizer.release_state_from_metadata()
    checks.append(("release_truth_exact", state == normalizer.EXPECTED, {"state": state, "expected": normalizer.EXPECTED}))
    constants=normalizer.load_json("registry/release_constant_registry.json")
    checks.append(("manifest_registry_parity", constants["constants"]["CURRENT_RELEASE"] == normalizer.EXPECTED["release"] and constants["constants"]["FUTURE_STABLE"] == normalizer.EXPECTED["future_stable"], constants["constants"]))
    mutation=copy.deepcopy(constants); mutation["constants"]["CURRENT_STATUS"]="stable"
    detected = mutation["constants"]["CURRENT_STATUS"] != normalizer.EXPECTED["status"]
    checks.append(("release_state_mutation_visible", detected, {"mutated_registry":"registry/release_constant_registry.json", "active_release_state": state}))
    failed=[name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        print(("✓" if ok else "✗") + f" {name}: {detail}")
    print("Summary:", {"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0
if __name__ == "__main__":
    raise SystemExit(main())
