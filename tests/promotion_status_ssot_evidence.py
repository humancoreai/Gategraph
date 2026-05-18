import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXPECTED_RELEASE = "v0.16.9_STABLE"
EXPECTED_BASE = "v0.16.8_STABLE"
EXPECTED_STATUS = "candidate" if EXPECTED_RELEASE.endswith("_CANDIDATE") else "stable"

def main():
    meta = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    assert meta["release"] == EXPECTED_RELEASE
    assert meta["base"] == EXPECTED_BASE
    assert meta["status"] == EXPECTED_STATUS
    assert meta.get("promotion_status_ssot_scope") is True

    from src import promotion_pipeline
    report = promotion_pipeline.promotion_pipeline_report()
    assert report["release"] == meta["release"]
    assert report["base"] == meta["base"]
    assert report["status"] == meta["status"]

    print({"release": report["release"], "base": report["base"], "status": report["status"], "ssot": "RELEASE_METADATA.json"})
    print("PASS promotion_status_ssot_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")

if __name__ == "__main__":
    main()
