"""
WHY: database.py owns local persistence setup so runtime code can stay deterministic.
INV: schema is initialized from a single SQL file; seed rules are idempotent.
SEC: no secrets or external services are used in the PoC.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "gategraph.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> None:
    conn = get_connection(path)
    with conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.close()


def reset_db(path: Path | None = None) -> None:
    target = path or DB_PATH
    if target.exists():
        target.unlink()
    init_db(target)


def seed_rules(conn: sqlite3.Connection) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rules = [
        (
            "RULE-001", "1.0.0", ["agent_file_operations"], ["read_files"], "low",
            "low", "allow", 10,
            "Read-only local file analysis is allowed when no higher risk applies.", 1, now,
        ),
        (
            "RULE-002", "1.0.0", ["agent_file_operations"], ["write_files", "delete_files"], "high",
            "high", "require_approval", 20,
            "Persistent file side effects require human approval.", 1, now,
        ),
        (
            "RULE-003", "1.0.0", ["untrusted_input"], ["read_files", "api_call"], "medium",
            "medium", "require_review", 10,
            "Untrusted content may be data, but must not become instructions.", 1, now,
        ),
        (
            "RULE-004", "1.0.0", ["agent_file_operations"], ["write_files"], "high",
            "high", "require_approval", 30,
            "Higher-priority write gate for deterministic conflict testing.", 1, now,
        ),
        (
            "RULE-005", "1.0.0", ["critical_risk"], ["read_files", "write_files", "delete_files", "api_call"], "critical",
            "critical", "require_approval", 100,
            "Critical risk must never be allowed automatically.", 1, now,
        ),
        (
            "RULE-006", "1.0.0", ["unknown_or_empty"], ["unknown_capability", "__empty__"], "low",
            "high", "block", 100,
            "Unknown or empty capabilities fail closed.", 1, now,
        ),
    ]
    with conn:
        for rule in rules:
            conn.execute(
                """
                INSERT OR IGNORE INTO rules
                  (rule_id, version, scope, trigger_caps, risk_threshold, severity,
                   decision, priority, rationale, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule[0], rule[1], json.dumps(rule[2]), json.dumps(rule[3]),
                    rule[4], rule[5], rule[6], rule[7], rule[8], rule[9], rule[10],
                ),
            )
