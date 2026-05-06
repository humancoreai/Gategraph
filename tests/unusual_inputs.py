"""
WHY: unusual input simulation checks robustness without expanding system scope.
INV: invalid/unknown/ambiguous input must never produce unsafe allow.
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
        ("empty capabilities", [], "local", "internal", False, "read_files"),
        ("unknown capability", ["format_drive"], "local", "internal", False, "format_drive"),
        ("mixed read+write", ["read_files", "write_files"], "local", "internal", False, "write_files"),
        ("duplicate capabilities", ["read_files", "read_files"], "local", "internal", False, "read_files"),
        ("case mismatch capability", ["Write_Files"], "local", "internal", False, "Write_Files"),
        ("none-like source string", ["read_files"], "", "internal", False, "read_files"),
        ("strange input source", ["read_files"], "alien", "internal", False, "read_files"),
        ("unknown sensitivity", ["read_files"], "local", "topsecret", False, "read_files"),
        ("secret + untrusted read", ["read_files"], "untrusted", "secret", False, "read_files"),
        ("secrets + unknown cap", ["unknown_action"], "local", "internal", True, "unknown_action"),
        ("api external uppercase", ["api_call"], "EXTERNAL", "internal", False, "api_call"),
        ("long capability name", ["x" * 500], "local", "internal", False, "x" * 500),
    ]

    allowed = blocked = unsafe_allows = invariant_violations = 0
    rows = []

    for i, (name, caps, source, sensitivity, secrets, action) in enumerate(scenarios, 1):
        task_id = f"UNUSUAL-{i:02d}"
        try:
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

            unsafe = False
            if action not in ("read_files",) and enf.allowed:
                unsafe = True
            if result.risk_level == "critical" and enf.allowed:
                unsafe = True
            if "write_files" in caps and enf.allowed:
                unsafe = True
            if unsafe:
                unsafe_allows += 1
                invariant_violations += 1

            rows.append((name, result.risk_level, result.final_decision, "allowed" if enf.allowed else "blocked", result.selected_rule_id, "UNSAFE" if unsafe else "ok"))
        except Exception as e:
            blocked += 1
            rows.append((name, "exception", "blocked", "blocked", "-", type(e).__name__))

    print("UNUSUAL INPUT SIMULATION v0.4.5")
    print(f"Runs: {len(scenarios)}")
    print(f"Events: {event_logger.count_events(conn)}")
    print(f"Allowed: {allowed}")
    print(f"Blocked/Gated/Errored: {blocked}")
    print(f"Unsafe allows: {unsafe_allows}")
    print(f"Invariant violations: {invariant_violations}")
    print()
    for row in rows:
        print(" | ".join(str(x) for x in row))

    conn.close()
    if invariant_violations:
        raise SystemExit(1)

if __name__ == "__main__":
    run()
