"""Controlled Apply evidence: separate Human-Gate, signed artifact, strict scope."""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import reset_db, get_connection, seed_rules, ensure_pattern_schema, ensure_review_schema, ensure_controlled_apply_schema
from src import review_workflow, controlled_apply


def fresh_db():
    import uuid; db_path = Path(tempfile.gettempdir()) / f'gategraph_ca_{os.getpid()}_{uuid.uuid4().hex}.db'; reset_db(db_path); conn = get_connection(db_path); ensure_pattern_schema(conn); ensure_review_schema(conn); ensure_controlled_apply_schema(conn)
    with conn:
        seed_rules(conn)
        conn.execute("""
            INSERT INTO proposals
              (proposal_id, schema_version, proposal_type, target_rule_id, reason, proposed_change,
               supporting_events, confidence, confidence_basis, priority, score, score_basis, status, created_at)
            VALUES ('CAPROP-1','0.8.22','rule_hardening','RULE-003','repeat review events','{}',
                    '[]',0.95,'manual evidence','P1',88.0,'manual evidence','pending_review',datetime('now'))
        """)
    return conn

def ok(cond, msg):
    if not cond: raise AssertionError(msg)

def approve_manual(conn):
    review_workflow.decide_proposal(conn, proposal_id='CAPROP-1', reviewer_id='manual-reviewer', decision='approved_for_manual_action', rationale='Eligible for separate human-gated apply.')

def approve2(conn):
    controlled_apply.record_human_gate(conn, proposal_id='CAPROP-1', reviewer_id='reviewer-a', decision='approved_for_controlled_apply', rationale='strict scope')
    controlled_apply.record_human_gate(conn, proposal_id='CAPROP-1', reviewer_id='reviewer-b', decision='approved_for_controlled_apply', rationale='independent approval')

def rule(conn):
    return conn.execute("SELECT * FROM rules WHERE rule_id='RULE-003'").fetchone()

def expect_error(fn, msg):
    try: fn()
    except controlled_apply.ControlledApplyError: return
    raise AssertionError(msg)

def test_a_manual_review_required():
    conn=fresh_db()
    try:
        expect_error(lambda: controlled_apply.record_human_gate(conn, proposal_id='CAPROP-1', reviewer_id='a', decision='approved_for_controlled_apply', rationale='x'), 'must require manual review first')
    finally: conn.close()

def test_b_two_human_gates_required():
    conn=fresh_db()
    try:
        approve_manual(conn)
        controlled_apply.record_human_gate(conn, proposal_id='CAPROP-1', reviewer_id='a', decision='approved_for_controlled_apply', rationale='x')
        expect_error(lambda: controlled_apply.create_apply_artifact(conn, proposal_id='CAPROP-1', change={'change_type':'rule_update','rule_id':'RULE-003','updates':{'decision':'require_approval'}}), 'must require two approvals')
    finally: conn.close()

def test_c_same_reviewer_blocked():
    conn=fresh_db()
    try:
        approve_manual(conn)
        controlled_apply.record_human_gate(conn, proposal_id='CAPROP-1', reviewer_id='a', decision='approved_for_controlled_apply', rationale='x')
        expect_error(lambda: controlled_apply.record_human_gate(conn, proposal_id='CAPROP-1', reviewer_id='a', decision='approved_for_controlled_apply', rationale='y'), 'same reviewer must not approve twice')
    finally: conn.close()

def test_d_unsupported_or_looser_changes_blocked():
    conn=fresh_db()
    try:
        approve_manual(conn); approve2(conn)
        bad=[
            {'change_type':'rule_update','rule_id':'RULE-003','updates':{'decision':'allow'}},
            {'change_type':'rule_update','rule_id':'RULE-003','updates':{'priority':1}},
            {'change_type':'secret_rotation','secret_ref_id':'S1','updates':{}},
            {'change_type':'rule_update','rule_id':'RULE-003','updates':{'active':0}},
        ]
        for change in bad:
            expect_error(lambda c=change: controlled_apply.create_apply_artifact(conn, proposal_id='CAPROP-1', change=c), f'invalid change should fail: {change}')
    finally: conn.close()

def test_e_executes_strict_rule_hardening_and_audits():
    conn=fresh_db()
    try:
        approve_manual(conn); approve2(conn); before=rule(conn)
        art=controlled_apply.create_apply_artifact(conn, proposal_id='CAPROP-1', change={'change_type':'rule_update','rule_id':'RULE-003','updates':{'decision':'require_approval','priority':before['priority']+5}})
        res=controlled_apply.execute_apply_artifact(conn, artifact_id=art.artifact_id); after=rule(conn)
        ok(res['executed'] is True, 'must execute'); ok(after['decision']=='require_approval', 'decision hardened'); ok(after['priority']==before['priority']+5, 'priority tightened')
        status=conn.execute('SELECT status FROM controlled_apply_artifacts WHERE artifact_id=?',(art.artifact_id,)).fetchone()['status']
        ok(status=='executed', 'single-use status'); events=conn.execute("SELECT COUNT(*) FROM events WHERE type='controlled_apply_executed'").fetchone()[0]; ok(events==1, 'audit event missing')
    finally: conn.close()

def test_f_replay_blocked():
    conn=fresh_db()
    try:
        approve_manual(conn); approve2(conn)
        art=controlled_apply.create_apply_artifact(conn, proposal_id='CAPROP-1', change={'change_type':'rule_update','rule_id':'RULE-003','updates':{'decision':'require_approval'}})
        controlled_apply.execute_apply_artifact(conn, artifact_id=art.artifact_id)
        expect_error(lambda: controlled_apply.execute_apply_artifact(conn, artifact_id=art.artifact_id), 'replay must fail')
    finally: conn.close()

def test_g_target_drift_blocked():
    conn=fresh_db()
    try:
        approve_manual(conn); approve2(conn)
        art=controlled_apply.create_apply_artifact(conn, proposal_id='CAPROP-1', change={'change_type':'rule_update','rule_id':'RULE-003','updates':{'decision':'require_approval'}})
        with conn: conn.execute("UPDATE rules SET rationale='out-of-band mutation' WHERE rule_id='RULE-003'")
        expect_error(lambda: controlled_apply.execute_apply_artifact(conn, artifact_id=art.artifact_id), 'target drift must fail')
    finally: conn.close()

def main():
    tests=[test_a_manual_review_required,test_b_two_human_gates_required,test_c_same_reviewer_blocked,test_d_unsupported_or_looser_changes_blocked,test_e_executes_strict_rule_hardening_and_audits,test_f_replay_blocked,test_g_target_drift_blocked]
    passed=failed=0
    for t in tests:
        try: t(); print('✓', t.__name__); passed+=1
        except Exception as e: print('✗', t.__name__, type(e).__name__, e); failed+=1
    print('\nCONTROLLED APPLY EVIDENCE REPORT'); print(f'Passed: {passed}/{len(tests)}'); print(f'Failed: {failed}/{len(tests)}')
    if failed: raise SystemExit(1)
if __name__=='__main__': main()
