from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    doc = (ROOT / "docs" / "EVIDENCE_LIFECYCLE_CLEANUP.md").read_text(encoding="utf-8")
    failures = []
    checks = []

    def check(name: str, ok: bool, detail: dict | None = None) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail or {}})
        print(("✓" if ok else "✗"), name, detail or {})
        if not ok:
            failures.append(name)

    check("metadata_current_release", metadata.get("release") == "v0.17.6_STABLE" and metadata.get("status") == "stable", {"release": metadata.get("release"), "status": metadata.get("status")})
    check("cleanup_scope_declared", metadata.get("cleanup_lifecycle_scope") is True and metadata.get("evidence_lifecycle_cleanup_scope") is True, {})
    check("descriptive_only_no_authority", all(metadata.get(k) is False for k in ["runtime_logic_changed", "governance_logic_changed", "enforcement_logic_changed", "new_runtime_capability", "new_governance_features"]), {})
    required = ["started", "completed", "timeout", "cleanup_attempted", "cleanup_confirmed", "process_group_killed"]
    check("cleanup_markers_documented", all(marker in doc for marker in required), {"markers": required})
    check("doc_declares_no_runtime_authority", "No runtime authority" in doc and "No policy mutation" in doc and "No auto-promotion" in doc, {})

    print("EVIDENCE LIFECYCLE CLEANUP REPORT")
    print({"passed": len(checks) - len(failures), "failed": len(failures), "failed_checks": failures})
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
