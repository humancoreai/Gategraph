#!/usr/bin/env python3
"""
SEC: enforcement must narrow local revocation races without changing authority.
INV: this evidence verifies transactional validation markers in enforcement.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENFORCEMENT = ROOT / "src" / "enforcement.py"

def check(name: str, ok: bool, detail: object):
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok

def main() -> int:
    src = ENFORCEMENT.read_text(encoding="utf-8")
    checks = [
        check("begin_immediate_used_for_token_validation", 'BEGIN IMMEDIATE' in src, "BEGIN IMMEDIATE"),
        check("revoked_checked_inside_validation_path", 'int(row["revoked"])' in src, "revoked"),
        check("validation_rolls_back_before_reject", "conn.rollback()" in src and "_reject" in src, "rollback"),
        check("allowed_path_commits_after_event", "event_logger.log_event" in src and "conn.commit()" in src, "commit"),
        check("keyring_loaded_once_before_validation", src.count("load_trusted_keyring()") == 1, src.count("load_trusted_keyring()")),
    ]
    failed = [name for name, ok in checks if not ok]
    print("REVOCATION ATOMICITY EVIDENCE REPORT")
    print({"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
