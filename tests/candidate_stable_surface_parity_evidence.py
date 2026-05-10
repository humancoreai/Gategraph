from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.12.7_STABLE"
EXPECTED_BASE = "v0.12.6_STABLE"
EXPECTED_STATUS = "stable"
SURFACES = ["README.md", "VERSION.md", "RELEASE_NOTES.md", "RELEASE_STATUS.md", "RELEASE_METADATA.json", "pyproject.toml", "tools/build_release.py", "tools/verify_release.py"]


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    meta = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    checks = []
    checks.append(check("metadata_state_consistent", meta.get("release") == EXPECTED_RELEASE and meta.get("base") == EXPECTED_BASE and meta.get("status") == EXPECTED_STATUS, {"release": meta.get("release"), "base": meta.get("base"), "status": meta.get("status")}))
    missing_release = []
    missing_base = []
    for rel in SURFACES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if EXPECTED_RELEASE not in text:
            missing_release.append(rel)
        if rel in {"README.md", "VERSION.md", "RELEASE_NOTES.md", "RELEASE_STATUS.md", "RELEASE_METADATA.json"} and EXPECTED_BASE not in text:
            missing_base.append(rel)
    checks.append(check("release_token_present_on_surfaces", not missing_release, {"missing": missing_release}))
    checks.append(check("base_token_present_on_release_surfaces", not missing_base, {"missing": missing_base}))
    forbidden = []
    for rel in SURFACES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "v0.12.7_CANDIDATE" in text:
            forbidden.append(rel)
    checks.append(check("no_candidate_token_in_stable", not forbidden, {"forbidden": forbidden}))
    checks.append(check("no_auto_transition_authority", meta.get("release_state_auto_promotion") is False and meta.get("release_state_auto_repair") is False, {"auto_promotion": meta.get("release_state_auto_promotion"), "auto_repair": meta.get("release_state_auto_repair")}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
