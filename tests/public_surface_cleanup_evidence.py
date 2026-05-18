import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.17.6_CANDIDATE"
BASE = "v0.17.5_STABLE"

FORBIDDEN_README_FRAGMENTS = [
    "v0.14.6 Candidate Scope",
    "v0.14.7 Candidate Scope",
    "v0.14.8 Candidate Scope",
    "Base stable: **v0.14.7_STABLE**",
]

def main():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))

    assert readme.count("Current release:") == 1
    assert RELEASE in readme
    assert BASE in readme
    assert "What GateGraph is not" in readme
    assert "Current production boundary" in readme
    assert "docs/SCOPE_BACKLOG.md" in readme
    assert metadata.get("public_surface_cleanup_scope") is True
    assert metadata.get("runtime_logic_changed") is False
    assert metadata.get("governance_logic_changed") is False

    forbidden = [fragment for fragment in FORBIDDEN_README_FRAGMENTS if fragment in readme]
    assert not forbidden, forbidden

    print({"release": RELEASE, "base": BASE, "checked": "README public surface"})
    print("PASS public_surface_cleanup_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")

if __name__ == "__main__":
    main()
