"""
WHY: test loop is deterministic — no random state, no external dependencies.
INV: isolated and accumulated modes exercise both clean-room and persistent event behavior.
SEC: tests target fail-closed behavior, token revocation, task binding, and critical-risk gating.
"""

import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import DB_PATH, get_connection, init_db, reset_db, seed_rules
from src.governance import evaluate_task
from src.enforcement import enforce
from src.capability_token import issue_expired_token
from src import event_logger


@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str
    invariant_violations: List[str] = field(default_factory=list)


@dataclass
class TestReport:
    mode: str
    results: List[TestResult] = field(default_factory=list)
    idempotency_hits: int = 0
    blocked_enforcements: int = 0
    unexpected_allows: int = 0

    def add(self, result: TestResult) -> None:
        self.results.append(result)
        self.unexpected_allows += sum(1 for v in result.invariant_violations if "allow" in v.lower())

    @property
    def invariant_violations(self) -> int:
        return sum(len(r.invariant_violations) for r in self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return len(self.results) - self.passed


def fresh_conn():
    reset_db()
    conn = get_connection()
    seed_rules(conn)
    return conn


def require(condition: bool, message: str, failures: List[str]) -> None:
    if not condition:
        failures.append(message)


def finish(name: str, failures: List[str], violations: List[str] | None = None) -> TestResult:
    violations = violations or []
    passed = not failures and not violations
    return TestResult(name, passed, "; ".join(failures) if failures else "all checks passed", violations)


def test_01_allowed_read(conn, report):
    r = evaluate_task(conn, task_id="T01", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    e = enforce(conn, r.token, "read_files", "T01", r.correlation_id)
    f=[]; v=[]
    require(r.risk_level == "low", f"risk {r.risk_level} != low", f)
    require(r.final_decision == "allow", f"decision {r.final_decision} != allow", f)
    require(e.allowed, f"read was blocked: {e.reason}", f)
    report.add(finish("01 allowed read", f, v))


def test_02_write_requires_approval(conn, report):
    r = evaluate_task(conn, task_id="T02", task_type="file_operation", requested_capabilities=["write_files"], input_source="local")
    e = enforce(conn, r.token, "write_files", "T02", r.correlation_id)
    f=[]; v=[]
    require(r.risk_level == "high", f"risk {r.risk_level} != high", f)
    require(r.final_decision == "require_approval", f"decision {r.final_decision} != require_approval", f)
    require(r.token is None, "token issued for require_approval", f)
    require(not e.allowed, "write allowed without approval", f)
    if e.allowed: v.append("unexpected allow: write without approval")
    else: report.blocked_enforcements += 1
    report.add(finish("02 write requires approval", f, v))


def test_03_delete_requires_approval(conn, report):
    r = evaluate_task(conn, task_id="T03", task_type="file_operation", requested_capabilities=["delete_files"], input_source="local")
    e = enforce(conn, r.token, "delete_files", "T03", r.correlation_id)
    f=[]; v=[]
    require(r.risk_level == "high", f"risk {r.risk_level} != high", f)
    require(r.final_decision == "require_approval", f"decision {r.final_decision} != require_approval", f)
    require(not e.allowed, "delete allowed without approval", f)
    if e.allowed: v.append("unexpected allow: delete without approval")
    else: report.blocked_enforcements += 1
    report.add(finish("03 delete requires approval", f, v))


def test_04_secrets_critical(conn, report):
    r = evaluate_task(conn, task_id="T04", task_type="file_operation", requested_capabilities=["read_files"], input_source="local", secrets_involved=True)
    e = enforce(conn, r.token, "read_files", "T04", r.correlation_id)
    f=[]; v=[]
    require(r.risk_level == "critical", f"risk {r.risk_level} != critical", f)
    require(r.final_decision == "require_approval", f"decision {r.final_decision} != require_approval", f)
    require(not e.allowed, "critical secret read allowed automatically", f)
    if e.allowed: v.append("unexpected allow: critical secrets")
    else: report.blocked_enforcements += 1
    report.add(finish("04 secrets critical gated", f, v))


def test_05_secret_sensitivity_critical(conn, report):
    r = evaluate_task(conn, task_id="T05", task_type="file_operation", requested_capabilities=["read_files"], input_source="local", data_sensitivity="secret")
    e = enforce(conn, r.token, "read_files", "T05", r.correlation_id)
    f=[]; v=[]
    require(r.risk_level == "critical", f"risk {r.risk_level} != critical", f)
    require(r.final_decision == "require_approval", f"decision {r.final_decision} != require_approval", f)
    require(not e.allowed, "secret sensitivity allowed automatically", f)
    if e.allowed: v.append("unexpected allow: secret sensitivity")
    else: report.blocked_enforcements += 1
    report.add(finish("05 secret sensitivity critical gated", f, v))


def test_06_untrusted_read_review(conn, report):
    r = evaluate_task(conn, task_id="T06", task_type="file_operation", requested_capabilities=["read_files"], input_source="untrusted")
    f=[]
    require(r.risk_level == "medium", f"risk {r.risk_level} != medium", f)
    require(r.final_decision in ("require_review", "block"), f"unexpected decision {r.final_decision}", f)
    report.add(finish("06 untrusted read review", f))


def test_07_idempotency(conn, report):
    key="idem-fixed-07"
    r1=evaluate_task(conn, task_id="T07", task_type="file_operation", requested_capabilities=["write_files"], input_source="local", idempotency_key=key)
    before=event_logger.count_events(conn)
    r2=evaluate_task(conn, task_id="T07", task_type="file_operation", requested_capabilities=["write_files"], input_source="local", idempotency_key=key)
    after=event_logger.count_events(conn)
    f=[]
    require(r1.event_id == r2.event_id, "duplicate retry returned different event", f)
    require(r2.was_duplicate, "retry did not mark duplicate", f)
    require(before == after, f"event count changed {before}->{after}", f)
    if r2.was_duplicate: report.idempotency_hits += 1
    report.add(finish("07 idempotency", f))


def test_08_unknown_capability(conn, report):
    r=evaluate_task(conn, task_id="T08", task_type="file_operation", requested_capabilities=["format_disk"], input_source="local")
    f=[]
    require(r.final_decision == "block", f"unknown capability decision {r.final_decision} != block", f)
    report.add(finish("08 unknown capability blocks", f))


def test_09_empty_capabilities(conn, report):
    r=evaluate_task(conn, task_id="T09", task_type="file_operation", requested_capabilities=[], input_source="local")
    f=[]
    require(r.final_decision == "block", f"empty capability decision {r.final_decision} != block", f)
    report.add(finish("09 empty capabilities block", f))


def test_10_expired_token(conn, report):
    # Create approved path manually and issue expired token.
    task="T10"; decision=f"DEC-{uuid.uuid4().hex[:8]}"
    with conn:
        conn.execute("INSERT OR IGNORE INTO tasks VALUES (?, 'file_operation', '[\"write_files\"]', 'local', 'internal', 0, datetime('now'))", (task,))
        conn.execute("INSERT OR IGNORE INTO events VALUES ('EVT-T10', '0.4', 'idem-t10', 'COR-T10', NULL, 'governance_decision', datetime('now'), ?, 'governance', 'rule_engine', '0.4.0', '{}', '{}', '{}')", (task,))
        conn.execute("INSERT OR IGNORE INTO decisions VALUES (?, ?, 'EVT-T10', 'require_approval', '{\"write_files\": true}', 'manual test approval', '[\"RULE-002\"]', datetime('now'))", (decision, task))
        tok=issue_expired_token(conn, decision, task, {"write_files": True})
    e=enforce(conn, tok, "write_files", task, "COR-T10")
    f=[]; v=[]
    require(tok.is_expired(), "token should be expired", f)
    require(not e.allowed, "expired token allowed", f)
    if e.allowed: v.append("unexpected allow: expired token")
    else: report.blocked_enforcements += 1
    report.add(finish("10 expired token blocks", f, v))


def test_11_rule_conflict_priority(conn, report):
    r=evaluate_task(conn, task_id="T11", task_type="file_operation", requested_capabilities=["write_files"], input_source="local")
    f=[]
    require(r.conflict_resolved, "expected multiple matching rules", f)
    require(r.selected_rule_id == "RULE-004", f"selected {r.selected_rule_id} != RULE-004", f)
    report.add(finish("11 conflict priority", f))


def test_12_rule_id_tiebreak(conn, report):
    now="2026-04-27T00:00:00Z"
    with conn:
        conn.execute("UPDATE rules SET active=0 WHERE rule_id IN ('RULE-002','RULE-004')")
        for rid in ["RULE-A", "RULE-B"]:
            conn.execute("INSERT OR IGNORE INTO rules VALUES (?, '1.0.0', '[\"test\"]', '[\"write_files\"]', 'high', 'high', 'require_approval', 5, 'tie test', 1, ?)", (rid, now))
    r=evaluate_task(conn, task_id="T12", task_type="file_operation", requested_capabilities=["write_files"], input_source="local")
    f=[]
    require(r.selected_rule_id == "RULE-A", f"selected {r.selected_rule_id} != RULE-A", f)
    report.add(finish("12 rule_id tiebreak", f))


def test_13_inactive_rule_ignored(conn, report):
    now="2026-04-27T00:00:00Z"
    with conn:
        conn.execute("INSERT OR IGNORE INTO rules VALUES ('RULE-INACTIVE', '1.0.0', '[\"test\"]', '[\"read_files\"]', 'low', 'critical', 'block', 999, 'inactive should not match', 0, ?)", (now,))
    r=evaluate_task(conn, task_id="T13", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    f=[]
    require(r.final_decision == "allow", f"inactive rule affected decision: {r.final_decision}", f)
    require("RULE-INACTIVE" not in r.matched_rule_ids, "inactive rule matched", f)
    report.add(finish("13 inactive rule ignored", f))


def test_14_cross_task_reuse(conn, report):
    r=evaluate_task(conn, task_id="T14A", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    evaluate_task(conn, task_id="T14B", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    e=enforce(conn, r.token, "read_files", "T14B", r.correlation_id)
    f=[]; v=[]
    require(not e.allowed, "cross-task token reuse allowed", f)
    if e.allowed: v.append("unexpected allow: cross-task token reuse")
    else: report.blocked_enforcements += 1
    report.add(finish("14 cross-task token reuse blocks", f, v))


def test_15_wrong_capability(conn, report):
    r=evaluate_task(conn, task_id="T15", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    e=enforce(conn, r.token, "write_files", "T15", r.correlation_id)
    f=[]; v=[]
    require(not e.allowed, "write allowed with read-only token", f)
    if e.allowed: v.append("unexpected allow: wrong capability")
    else: report.blocked_enforcements += 1
    report.add(finish("15 wrong capability blocks", f, v))


def test_16_missing_token(conn, report):
    # Ensure task exists for rejection event FK.
    evaluate_task(conn, task_id="T16", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    e=enforce(conn, None, "read_files", "T16", "COR-T16")
    f=[]
    require(not e.allowed, "missing token allowed", f)
    if not e.allowed: report.blocked_enforcements += 1
    report.add(finish("16 missing token blocks", f))


def test_17_revoked_token(conn, report):
    r=evaluate_task(conn, task_id="T17", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    with conn:
        conn.execute("UPDATE capability_tokens SET revoked=1 WHERE token_id=?", (r.token.token_id,))
    e=enforce(conn, r.token, "read_files", "T17", r.correlation_id)
    f=[]; v=[]
    require(not e.allowed, "revoked token allowed", f)
    if e.allowed: v.append("unexpected allow: revoked token")
    else: report.blocked_enforcements += 1
    report.add(finish("17 revoked token blocks", f, v))


def test_18_replay_rejection_idempotency(conn, report):
    evaluate_task(conn, task_id="T18", task_type="file_operation", requested_capabilities=["read_files"], input_source="local")
    e1=enforce(conn, None, "read_files", "T18", "COR-T18")
    count1=event_logger.count_events(conn)
    e2=enforce(conn, None, "read_files", "T18", "COR-T18")
    count2=event_logger.count_events(conn)
    f=[]
    require(e1.rejection_event_id == e2.rejection_event_id, "same rejection did not return same event", f)
    require(count1 == count2, f"duplicate rejection changed event count {count1}->{count2}", f)
    if e2.rejection_event_id == e1.rejection_event_id: report.idempotency_hits += 1
    report.blocked_enforcements += 2
    report.add(finish("18 rejection idempotency", f))


def test_19_secret_write_critical(conn, report):
    r=evaluate_task(conn, task_id="T19", task_type="file_operation", requested_capabilities=["write_files"], input_source="local", data_sensitivity="secret")
    f=[]
    require(r.risk_level == "critical", f"risk {r.risk_level} != critical", f)
    require(r.selected_rule_id == "RULE-005", f"selected {r.selected_rule_id} != RULE-005", f)
    require(r.final_decision == "require_approval", f"decision {r.final_decision} != require_approval", f)
    report.add(finish("19 secret write critical precedence", f))


def test_20_untrusted_prompt_injection_text(conn, report):
    r=evaluate_task(conn, task_id="T20", task_type="file_operation", requested_capabilities=["read_files"], input_source="untrusted")
    f=[]
    require(r.risk_level == "medium", f"risk {r.risk_level} != medium", f)
    require(r.final_decision == "require_review", f"decision {r.final_decision} != require_review", f)
    report.add(finish("20 untrusted content is data", f))


TESTS: List[Callable] = [
    test_01_allowed_read, test_02_write_requires_approval, test_03_delete_requires_approval,
    test_04_secrets_critical, test_05_secret_sensitivity_critical, test_06_untrusted_read_review,
    test_07_idempotency, test_08_unknown_capability, test_09_empty_capabilities,
    test_10_expired_token, test_11_rule_conflict_priority, test_12_rule_id_tiebreak,
    test_13_inactive_rule_ignored, test_14_cross_task_reuse, test_15_wrong_capability,
    test_16_missing_token, test_17_revoked_token, test_18_replay_rejection_idempotency,
    test_19_secret_write_critical, test_20_untrusted_prompt_injection_text,
]


def run_isolated() -> TestReport:
    report=TestReport("isolated")
    for test in TESTS:
        conn=fresh_conn()
        try:
            test(conn, report)
        finally:
            conn.close()
    return report


def run_accumulated() -> TestReport:
    report=TestReport("accumulated")
    conn=fresh_conn()
    try:
        for test in TESTS:
            test(conn, report)
        report.db_events = event_logger.count_events(conn)  # type: ignore[attr-defined]
    finally:
        conn.close()
    return report


def print_report(report: TestReport) -> None:
    db_events = getattr(report, "db_events", "—")
    print(f"\n== {report.mode.upper()} ==")
    for r in report.results:
        print(f"{'PASS' if r.passed else 'FAIL'} {r.name}: {r.detail}")
        for v in r.invariant_violations:
            print(f"  INV: {v}")
    print(f"Passed: {report.passed}/{len(report.results)}")
    print(f"Failed: {report.failed}")
    print(f"Unexpected allows: {report.unexpected_allows}")
    print(f"Invariant violations: {report.invariant_violations}")
    print(f"Idempotency hits: {report.idempotency_hits}")
    print(f"Blocked enforcements: {report.blocked_enforcements}")
    print(f"DB events: {db_events}")


def main():
    isolated=run_isolated()
    accumulated=run_accumulated()
    print_report(isolated)
    print_report(accumulated)
    print("\nCOMPARATIVE SUMMARY")
    print(f"Passed: isolated {isolated.passed}/20 | accumulated {accumulated.passed}/20")
    print(f"Failed: isolated {isolated.failed} | accumulated {accumulated.failed}")
    print(f"Unexpected allows: isolated {isolated.unexpected_allows} | accumulated {accumulated.unexpected_allows}")
    print(f"Invariant violations: isolated {isolated.invariant_violations} | accumulated {accumulated.invariant_violations}")
    print(f"DB events accumulated: {getattr(accumulated, 'db_events', '—')}")
    exit_code = 1 if (isolated.failed or accumulated.failed or isolated.invariant_violations or accumulated.invariant_violations) else 0
    sys.stdout.flush()
    sys.stderr.flush()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parents[1])
    main()
