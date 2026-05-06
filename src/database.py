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


def ensure_runtime_schema(conn):
    """
    WHY: Runtime Guard tables are additive; safe to call after normal DB init.
    INV: this does not modify Governance Core tables.
    """
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS runtime_budgets (
        budget_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        max_steps INTEGER NOT NULL,
        max_runtime_seconds INTEGER NOT NULL,
        max_cost_units INTEGER NOT NULL,
        repeated_action_limit INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS runtime_steps (
        step_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        step_index INTEGER NOT NULL,
        actor_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        action_signature TEXT NOT NULL,
        cost_units INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS runtime_decisions (
        decision_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        step_id TEXT,
        decision TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_runtime_steps_task
        ON runtime_steps(task_id);

    CREATE INDEX IF NOT EXISTS idx_runtime_steps_signature
        ON runtime_steps(task_id, action_signature);

    CREATE INDEX IF NOT EXISTS idx_runtime_decisions_task
        ON runtime_decisions(task_id);
    """)


def ensure_pattern_schema(conn):
    """
    WHY: Pattern Engine is additive; proposals never mutate rules directly.
    INV: proposals remain pending until a human/reviewer explicitly decides.
    """
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS proposals (
        proposal_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL DEFAULT '0.7',
        proposal_type TEXT NOT NULL,
        target_rule_id TEXT,
        reason TEXT NOT NULL,
        proposed_change TEXT NOT NULL,
        supporting_events TEXT NOT NULL,
        confidence REAL NOT NULL,
        confidence_basis TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'P3',
        score REAL NOT NULL DEFAULT 0,
        score_basis TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending_review',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_proposals_status
        ON proposals(status);

    CREATE INDEX IF NOT EXISTS idx_proposals_target_rule
        ON proposals(target_rule_id);

    CREATE INDEX IF NOT EXISTS idx_proposals_priority
        ON proposals(priority, score);
    """)

    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(proposals)").fetchall()}
    additive_columns = {
        "priority": "TEXT NOT NULL DEFAULT 'P3'",
        "score": "REAL NOT NULL DEFAULT 0",
        "score_basis": "TEXT NOT NULL DEFAULT ''",
    }
    for column_name, column_def in additive_columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE proposals ADD COLUMN {column_name} {column_def}")


def ensure_review_schema(conn):
    """
    WHY: Review workflow stores explicit human/process decisions on advisory proposals.
    INV: review approval does not apply any rule, policy, budget, token, secret, or action change.
    """
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS proposal_review_decisions (
        review_id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        decision TEXT NOT NULL CHECK (decision IN ('approved_for_manual_action','rejected')),
        rationale TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
    );

    CREATE INDEX IF NOT EXISTS idx_proposal_review_decisions_proposal
        ON proposal_review_decisions(proposal_id);
    """)
