"""
WHY: evidence that token key rotation is explicit and fail-closed.
INV: new tokens use the active key; old tokens remain valid only while their key stays trusted.
SEC: unknown key ids and signing-key tampering must not pass enforcement.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules
from src.governance import evaluate_task
from src.enforcement import enforce

KEYRING = {"rot-v2": "secret-v2", "rot-v1": "secret-v1"}

@contextmanager
def key_env(active: str, keyring: Dict[str, str]):
    old_active = os.environ.get("GATEGRAPH_TOKEN_ACTIVE_KEY_ID")
    old_keyring = os.environ.get("GATEGRAPH_TOKEN_KEYRING_JSON")
    os.environ["GATEGRAPH_TOKEN_ACTIVE_KEY_ID"] = active
    os.environ["GATEGRAPH_TOKEN_KEYRING_JSON"] = json.dumps(keyring, sort_keys=True)
    try:
        yield
    finally:
        if old_active is None:
            os.environ.pop("GATEGRAPH_TOKEN_ACTIVE_KEY_ID", None)
        else:
            os.environ["GATEGRAPH_TOKEN_ACTIVE_KEY_ID"] = old_active
        if old_keyring is None:
            os.environ.pop("GATEGRAPH_TOKEN_KEYRING_JSON", None)
        else:
            os.environ["GATEGRAPH_TOKEN_KEYRING_JSON"] = old_keyring


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_key_rotation_", suffix=".db", delete=False)
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


def scenario_new_tokens_use_active_key():
    conn, db = fresh_conn(); task_id = "ROT-ACTIVE"
    try:
        with key_env("rot-v2", KEYRING):
            r = allowed_read_token(conn, task_id)
            e = enforce(conn, r.token, "read_files", task_id, r.correlation_id)
            return (r.token.signing_key_id == "rot-v2" and e.allowed), {"kid": r.token.signing_key_id, "allowed": e.allowed}
    finally:
        close_conn(conn, db)


def scenario_legacy_key_still_verifies_while_trusted():
    conn, db = fresh_conn(); task_id = "ROT-LEGACY"
    try:
        with key_env("rot-v1", KEYRING):
            r = allowed_read_token(conn, task_id)
        with key_env("rot-v2", KEYRING):
            e = enforce(conn, r.token, "read_files", task_id, r.correlation_id)
            return (r.token.signing_key_id == "rot-v1" and e.allowed), {"kid": r.token.signing_key_id, "allowed": e.allowed}
    finally:
        close_conn(conn, db)


def scenario_legacy_key_blocks_after_retirement():
    conn, db = fresh_conn(); task_id = "ROT-RETIRED"
    try:
        with key_env("rot-v1", KEYRING):
            r = allowed_read_token(conn, task_id)
        with key_env("rot-v2", {"rot-v2": "secret-v2"}):
            e = enforce(conn, r.token, "read_files", task_id, r.correlation_id)
            return (not e.allowed and "unknown signing key" in e.reason), {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def scenario_signing_key_id_tamper_blocks():
    conn, db = fresh_conn(); task_id = "ROT-KID-TAMPER"
    try:
        with key_env("rot-v2", KEYRING):
            r = allowed_read_token(conn, task_id)
            forged = replace(r.token, signing_key_id="rot-v1")
            e = enforce(conn, forged, "read_files", task_id, r.correlation_id)
            return (not e.allowed and "claim mismatch" in e.reason), {"allowed": e.allowed, "reason": e.reason}
    finally:
        close_conn(conn, db)


def main() -> int:
    scenarios = [
        ("new_tokens_use_active_key", scenario_new_tokens_use_active_key),
        ("legacy_key_still_verifies_while_trusted", scenario_legacy_key_still_verifies_while_trusted),
        ("legacy_key_blocks_after_retirement", scenario_legacy_key_blocks_after_retirement),
        ("signing_key_id_tamper_blocks", scenario_signing_key_id_tamper_blocks),
    ]
    failures = []
    print("KEY ROTATION EVIDENCE")
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
