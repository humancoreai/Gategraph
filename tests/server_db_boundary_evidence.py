#!/usr/bin/env python3
"""
WHY: the local server adapter must serialize SQLite boundary access consistently.
INV: this evidence is static/source-level and does not add server runtime authority.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src" / "server.py"

def check(name: str, ok: bool, detail: object):
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok

def main() -> int:
    src = SERVER.read_text(encoding="utf-8")
    checks = [
        check("shared_db_boundary_lock_declared", "db_boundary_lock = threading.RLock()" in src, "db_boundary_lock"),
        check("evaluate_uses_db_boundary_lock", "with self.server.db_boundary_lock" in src and "evaluate_request" in src, "evaluate"),
        check("status_monitoring_use_db_boundary_lock", src.count("with self.server.db_boundary_lock") >= 3, src.count("with self.server.db_boundary_lock")),
        check("workers_not_daemon_cutoff", "daemon_threads = False" in src and "block_on_close = True" in src, "shutdown-boundary"),
        check("no_runtime_authority_added", "auto_promotion" not in src and "policy_mutation" not in src, "source"),
    ]
    failed = [name for name, ok in checks if not ok]
    print("SERVER DB BOUNDARY EVIDENCE REPORT")
    print({"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
