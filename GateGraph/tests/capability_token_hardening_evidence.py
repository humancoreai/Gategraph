"""
WHY: evidence that Capability Tokens are integrity-checked at Enforcement.
INV: mutated, forged, replayed, or DB-tampered tokens fail closed before action.
SEC: this is the transition from plain in-memory grants toward boundary-ready tokens.
"""
from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules
from src.governance import evaluate_task
from src.enforcement import enforce
from src.capability_token import CapabilityToken


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_token_hardening_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        seed_rules(conn)
    return conn, db_path


def close_conn(conn, db_path: Path) -> None:
    conn.close()
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


def allowed_read_token(conn, task_id: str):
    result = evaluate_task(
        conn,
        task_id=task_id,
        task_type="file_operation",
        requested_capabilities=["read_files"],
        input_source="local",
    )
    assert result.token is not None
    return result


def scenario_valid_signed_token_allows():
    conn, db = fresh_conn(); task_id = "TOK-HAPPY"
    try:
        r = allowed_read_token(conn, task_id)
        e = enforce(conn, r.token, "read_files", task_id, r.correlation_id)
        return e.allowed and e.reason == "capability granted", {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def scenario_mutated_capabilities_block():
    conn, db = fresh_conn(); task_id = "TOK-MUTATED-CAPS"
    try:
        r = allowed_read_token(conn, task_id)
        forged = replace(r.token, capabilities={"read_files": True, "api_call": True})
        e = enforce(conn, forged, "api_call", task_id, r.correlation_id)
        return (not e.allowed and "capability token claim mismatch" in e.reason), {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def scenario_mutated_signature_block():
    conn, db = fresh_conn(); task_id = "TOK-BAD-SIG"
    try:
        r = allowed_read_token(conn, task_id)
        forged = replace(r.token, signature="0" * 64)
        e = enforce(conn, forged, "read_files", task_id, r.correlation_id)
        return (not e.allowed and "capability token invalid signature" in e.reason), {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def scenario_db_signature_tamper_blocks():
    conn, db = fresh_conn(); task_id = "TOK-DB-TAMPER"
    try:
        r = allowed_read_token(conn, task_id)
        with conn:
            conn.execute("UPDATE capability_tokens SET signature=? WHERE token_id=?", ("bad", r.token.token_id))
        e = enforce(conn, r.token, "read_files", task_id, r.correlation_id)
        return (not e.allowed and "capability token invalid signature" in e.reason), {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def scenario_replay_to_other_task_blocks():
    conn, db = fresh_conn(); task_id = "TOK-REPLAY-A"
    try:
        r = allowed_read_token(conn, task_id)
        with conn:
            conn.execute("""
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES ('TOK-REPLAY-B', 'file_operation', '["read_files"]', 'local', 'internal', 0, datetime('now'))
            """)
        e = enforce(conn, r.token, "read_files", "TOK-REPLAY-B", r.correlation_id)
        return (not e.allowed and "bound to task" in e.reason), {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def main() -> int:
    scenarios = [
        ("valid_signed_token_allows", scenario_valid_signed_token_allows),
        ("mutated_capabilities_block", scenario_mutated_capabilities_block),
        ("mutated_signature_block", scenario_mutated_signature_block),
        ("db_signature_tamper_blocks", scenario_db_signature_tamper_blocks),
        ("replay_to_other_task_blocks", scenario_replay_to_other_task_blocks),
    ]
    failures = []
    print("CAPABILITY TOKEN HARDENING EVIDENCE")
    for name, fn in scenarios:
        passed, detail = fn()
        print(("✓" if passed else "✗"), name, detail)
        if not passed:
            failures.append(name)
    print(f"\nResult: {len(scenarios)-len(failures)}/{len(scenarios)} passed")
    if failures:
        print("Failures:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    os._exit(main())
