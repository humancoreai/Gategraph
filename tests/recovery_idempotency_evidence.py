#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.recovery_foundation import classify_partial_recovery_state, recover_attempt_once, validate_reservation_recovery_collision

def main() -> int:
    checks=[]
    r=recover_attempt_once({'RC-1'}, 'RC-1'); assert r.decision=='continue' and r.reason=='RECOVERY_ATTEMPT_ALREADY_FINAL' and r.effect=='descriptive_only'; checks.append(('duplicate_recovery_attempt_visible_idempotent', r.to_dict()))
    r=recover_attempt_once(set(), 'RC-2'); assert r.decision=='continue' and r.reason=='RECOVERY_ATTEMPT_ACCEPTED_ONCE' and r.effect=='record_recovery_attempt'; checks.append(('new_recovery_attempt_record_only', r.to_dict()))
    r=validate_reservation_recovery_collision({'reservation_id':'R-10','state':'reserved','consumed':False,'released':False}, [{'event_id':'E-1','sequence':1,'reservation_id':'R-10','event_type':'reservation_consumed'}]); assert r.decision=='stop' and r.reason=='RECOVERY_RESERVATION_LOCAL_AUDIT_CONFLICT'; checks.append(('reservation_local_audit_collision_blocked', r.to_dict()))
    r=validate_reservation_recovery_collision({'reservation_id':'R-11','state':'consumed','consumed':True,'released':False}, [{'event_id':'E-1','sequence':1,'reservation_id':'R-11','event_type':'reservation_consumed'}]); assert r.decision=='continue' and r.reason=='RECOVERY_CONSUME_ALREADY_FINAL'; checks.append(('reservation_finality_consistent', r.to_dict()))
    r=classify_partial_recovery_state({'snapshot_id':'S-1','audit_complete':True,'reservation_complete':False,'ledger_complete':True,'incident_complete':True}); assert r.decision=='stop' and r.reason=='RECOVERY_PARTIAL_STATE_FAIL_CLOSED'; checks.append(('partial_recovery_fails_closed', r.to_dict()))
    r=classify_partial_recovery_state({'snapshot_id':'S-2','audit_complete':True,'reservation_complete':True,'ledger_complete':True,'incident_complete':True}); assert r.decision=='continue' and r.reason=='RECOVERY_SNAPSHOT_COMPLETE_DESCRIPTIVE'; checks.append(('complete_recovery_descriptive_only', r.to_dict()))
    for name,payload in checks: print(f'✓ {name}: {payload}')
    print('\nRECOVERY IDEMPOTENCY EVIDENCE REPORT'); print({'passed':len(checks),'failed':0}); return 0
if __name__=='__main__': raise SystemExit(main())
