"""
WHY: usage simulation validates normal everyday flows after semantic fixes.
INV: no write/delete/api_call executes without approval; require_review is analysis-only.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection, seed_rules
from src.governance import evaluate_task
from src.enforcement import enforce
import src.event_logger as event_logger

def reset_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "governance.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()
    conn = get_connection()
    with conn:
        seed_rules(conn)
    return conn

def run():
    conn = reset_db()
    scenarios = [
        ("local README read", ["read_files"], "local", "internal", False, "read_files"),
        ("local source read", ["read_files"], "local", "internal", False, "read_files"),
        ("write patch", ["write_files"], "local", "internal", False, "write_files"),
        ("delete request", ["delete_files"], "local", "internal", False, "delete_files"),
        ("untrusted doc read", ["read_files"], "untrusted", "internal", False, "read_files"),
        ("secret config read", ["read_files"], "local", "secret", False, "read_files"),
        ("external api call", ["api_call"], "external", "internal", False, "api_call"),
        ("public local read", ["read_files"], "local", "public", False, "read_files"),
        ("secrets involved read", ["read_files"], "local", "internal", True, "read_files"),
        ("unknown action", ["unknown_action"], "local", "internal", False, "unknown_action"),
    ]

    allowed = blocked = unexpected_allows = invariant_violations = 0
    rows = []

    for i, (name, caps, source, sensitivity, secrets, action) in enumerate(scenarios, start=1):
        task_id = f"USAGE-{i:02d}"
        result = evaluate_task(
            conn,
            task_id=task_id,
            task_type="file_operation",
            requested_capabilities=caps,
            input_source=source,
            data_sensitivity=sensitivity,
            secrets_involved=secrets,
        )
        enf = enforce(conn, result.token, action, task_id, result.correlation_id)
        allowed += int(enf.allowed)
        blocked += int(not enf.allowed)

        if action in ("write_files", "delete_files", "api_call") and enf.allowed:
            unexpected_allows += 1
            invariant_violations += 1
        if result.risk_level == "critical" and enf.allowed:
            unexpected_allows += 1
            invariant_violations += 1

        rows.append((name, result.risk_level, result.final_decision, "allowed" if enf.allowed else "blocked", result.selected_rule_id))

    print("USAGE SIMULATION v0.8.12")
    print(f"Runs: {len(scenarios)}")
    print(f"Events: {event_logger.count_events(conn)}")
    print(f"Allowed: {allowed}")
    print(f"Blocked/Gated: {blocked}")
    print(f"Unexpected allows: {unexpected_allows}")
    print(f"Invariant violations: {invariant_violations}")
    print()
    for row in rows:
        print(" | ".join(str(x) for x in row))
    conn.close()
    if invariant_violations:
        raise SystemExit(1)

if __name__ == "__main__":
    run()
