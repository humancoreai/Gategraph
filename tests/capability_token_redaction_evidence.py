"""
WHY: capability tokens are authorization material; audit may reference them, never store them.
INV: events/audit JSON contains token_id + token_hash only, not raw token objects, signatures,
     signing input, Authorization headers, bearer values, or signing secrets.
SEC: Base64/JSON serialization is not protection; audit redaction is mandatory.
"""
from __future__ import annotations

import json, os, re, sys, tempfile
from dataclasses import asdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.database import get_connection, init_db, seed_rules
from src.governance import evaluate_task
from src.enforcement import enforce
from src.runtime_path_assertions import service_adapter_context
from src.capability_token import token_audit_ref, token_hash

BASE64ISH_RE = re.compile(r"[A-Za-z0-9_-]{40,}={0,2}")

def _fresh_conn():
    tmp = tempfile.TemporaryDirectory(); db = Path(tmp.name) / "gategraph_redaction.db"
    init_db(db); conn = get_connection(db); seed_rules(conn); return tmp, conn

def _event_blob(conn) -> str:
    rows = conn.execute("SELECT event_id, type, input_json, evaluation_json, decision_json FROM events ORDER BY timestamp, event_id").fetchall()
    return json.dumps([dict(row) for row in rows], sort_keys=True, default=str)

def _assert_no_forbidden(blob: str, *, token) -> None:
    forbidden = [
        token.signature,
        json.dumps(asdict(token), sort_keys=True, default=str),
        f"Bearer {token.signature}",
        "Authorization",
        "signing_input",
        "gategraph-local-dev-token-signing-secret",
        "gategraph-local-dev-token-signing-secret-v2",
    ]
    leaked = [v for v in forbidden if v and v in blob]
    assert not leaked, f"audit leaked forbidden token/auth material: {leaked[:3]}"
    for match in BASE64ISH_RE.findall(blob):
        if match.startswith("sha256") or match.startswith("TOK-"):
            continue
        assert match != token.signature, "raw token signature/base64-like token material leaked into audit"

def test_token_issue_audit_uses_redacted_reference() -> dict:
    tmp, conn = _fresh_conn()
    try:
        result = evaluate_task(conn, task_id="RED-AUDIT-ISSUE", task_type="file_operation", requested_capabilities=["read_files"], input_source="local", trusted_entry_context=service_adapter_context())
        assert result.token is not None
        blob = _event_blob(conn); ref = token_audit_ref(result.token)
        assert ref["token_id"] in blob and ref["token_hash"] in blob
        assert token_hash(result.token).startswith("sha256:")
        _assert_no_forbidden(blob, token=result.token)
        return {"token_id": result.token.token_id, "token_hash_observed": ref["token_hash"] in blob}
    finally:
        conn.close(); tmp.cleanup()

def test_enforcement_audit_uses_redacted_reference() -> dict:
    tmp, conn = _fresh_conn()
    try:
        result = evaluate_task(conn, task_id="RED-AUDIT-ENFORCE", task_type="file_operation", requested_capabilities=["read_files"], input_source="local", trusted_entry_context=service_adapter_context())
        assert result.token is not None
        enf = enforce(conn, result.token, "read_files", result.task_id, result.correlation_id)
        assert enf.allowed is True
        blob = _event_blob(conn)
        assert "enforcement_allowed" in blob and result.token.token_id in blob and token_hash(result.token) in blob
        _assert_no_forbidden(blob, token=result.token)
        return {"allowed": enf.allowed, "token_hash_observed": token_hash(result.token) in blob}
    finally:
        conn.close(); tmp.cleanup()

def main() -> int:
    tests = [("token_issue_audit_uses_redacted_reference", test_token_issue_audit_uses_redacted_reference), ("enforcement_audit_uses_redacted_reference", test_enforcement_audit_uses_redacted_reference)]
    failed=[]; print("CAPABILITY TOKEN REDACTION EVIDENCE")
    for name, fn in tests:
        try: print("✓", name, fn())
        except Exception as exc: failed.append(name); print("✗", name, repr(exc))
    print(f"Summary: {{'passed': {len(tests)-len(failed)}, 'failed': {len(failed)}}}")
    if failed: return 1
    print("PASS capability_token_redaction_evidence"); return 0
if __name__ == "__main__": raise SystemExit(main())
