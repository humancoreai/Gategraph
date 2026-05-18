from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "RELEASE_METADATA.json"
DOC = ROOT / "docs" / "CONCURRENCY_SCOPE_STATEMENT.md"


def main() -> int:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")
    release = metadata["release"]
    base = metadata["base"]
    status = metadata["status"]

    checks = []
    def check(name: str, ok: bool, detail=None):
        checks.append((name, ok, detail or {}))
        print(("✓" if ok else "✗"), name, detail or {})

    required_phrases = [
        release,
        base,
        status,
        "single-node deterministic governance baseline",
        "SQLite persistence is treated as thread-owned",
        "no intentional cross-thread connection reuse",
        "distributed runtime execution",
        "multi-node clustering",
        "shared SQLite handles across threads",
        "descriptive only",
        "does not add runtime authority",
        "capability scopes",
    ]

    check("metadata_scope_declared", metadata.get("concurrency_scope_statement_scope") is True, {"release": release})
    check("doc_present", DOC.exists(), {"path": str(DOC.relative_to(ROOT))})
    missing = [phrase for phrase in required_phrases if phrase not in doc]
    check("scope_terms_present", not missing, {"missing": missing})
    forbidden = ["PostgreSQL migration complete", "cluster ready", "shared connection pool authority", "runtime authority added"]
    found = [phrase for phrase in forbidden if phrase in doc]
    check("no_enterprise_or_authority_claims", not found, {"found": found})
    check("runtime_authority_unchanged", metadata.get("runtime_authority_changed") is False and metadata.get("new_runtime_capability") is False, {})

    failed = [name for name, ok, _ in checks if not ok]
    print("CONCURRENCY SCOPE STATEMENT EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    if failed:
        raise AssertionError(failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
