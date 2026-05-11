import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.15.2_CANDIDATE"
BASE = "v0.15.1_STABLE"
REQUIRED_DEFERRED = [
    "Auth/TLS built into GateGraph",
    "KMS / managed secret backend",
    "Multi-node governance",
    "External agent-framework integration",
    "Customer-system assessment agent",
    "Public internet deployment",
]

def main():
    doc = (ROOT / "docs" / "SCOPE_BACKLOG.md").read_text(encoding="utf-8")
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))

    assert RELEASE in doc
    assert BASE in doc
    assert "Current Scope" in doc
    assert "Deferred Scope" in doc
    assert "Scope Rule" in doc
    assert metadata.get("scope_backlog_triage_scope") is True
    assert metadata.get("production_boundary_unchanged") is True

    missing = [item for item in REQUIRED_DEFERRED if item not in doc]
    assert not missing, missing

    assert "may enter scope only through a future Candidate" in doc
    assert "human approval before Stable promotion" in doc

    print({"release": RELEASE, "deferred_items": len(REQUIRED_DEFERRED)})
    print("PASS scope_backlog_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")

if __name__ == "__main__":
    main()
