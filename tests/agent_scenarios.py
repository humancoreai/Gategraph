"""
WHY: agent scenarios validate realistic orchestration behavior without adding multi-agent runtime.
INV: require_review permits analysis-only reads but never side effects.
"""
import os
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
        ("Agent reads repo files", ["read_files"], "local", "internal", False, "read_files", "allow"),
        ("Agent proposes patch only", ["read_files"], "local", "internal", False, "read_files", "allow"),
        ("Agent attempts direct write", ["write_files"], "local", "internal", False, "write_files", "block"),
        ("Agent attempts delete", ["delete_files"], "local", "internal", False, "delete_files", "block"),
        ("Agent reads untrusted doc", ["read_files"], "untrusted", "internal", False, "read_files", "analysis_only"),
        ("Agent follows untrusted instruction to write", ["write_files"], "untrusted", "internal", False, "write_files", "block"),
        ("Agent handles secret config", ["read_files"], "local", "secret", False, "read_files", "block"),
        ("Agent handles explicit secret", ["read_files"], "local", "internal", True, "read_files", "block"),
        ("Agent external API call", ["api_call"], "external", "internal", False, "api_call", "block"),
        ("Agent unknown tool request", ["spawn_shell"], "local", "internal", False, "spawn_shell", "block"),
        ("Agent mixed read and write", ["read_files", "write_files"], "local", "internal", False, "write_files", "block"),
        ("Agent prompt injection string as untrusted read", ["read_files"], "untrusted", "internal", False, "read_files", "analysis_only"),
    ]

    allowed = blocked = unexpected_allows = invariant_violations = 0
    rows = []

    for i, (name, caps, source, sensitivity, secrets, action, posture) in enumerate(scenarios, 1):
        task_id = f"AGENT-{i:02d}"
        result = evaluate_task(
            conn,
            task_id=task_id,
            task_type="agent_operation",
            requested_capabilities=caps,
            input_source=source,
            data_sensitivity=sensitivity,
            secrets_involved=secrets,
        )
        enf = enforce(conn, result.token, action, task_id, result.correlation_id)
        allowed += int(enf.allowed)
        blocked += int(not enf.allowed)

        violation = False
        if action in ("write_files", "delete_files", "api_call", "spawn_shell") and enf.allowed:
            violation = True
        if result.risk_level == "critical" and enf.allowed:
            violation = True
        if posture == "block" and enf.allowed:
            violation = True
        if posture in ("allow", "analysis_only") and not enf.allowed:
            violation = True

        if violation:
            unexpected_allows += int(enf.allowed)
            invariant_violations += 1

        rows.append((name, result.risk_level, result.final_decision, "allowed" if enf.allowed else "blocked", result.selected_rule_id, "VIOLATION" if violation else "ok"))

    print("AGENT SCENARIO SIMULATION v0.8.12")
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
