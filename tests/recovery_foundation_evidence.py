#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.recovery_foundation import apply_consume_once, incident_transition, recover_interrupted_reservation, validate_append_only_audit

def main() -> int:
    checks=[]
    r=recover_interrupted_reservation({'reservation_id':'R-1','state':'reserved','consumed':False,'released':False}); assert r.decision=='continue' and r.reason=='RECOVERY_RELEASE_INTERRUPTED_RESERVATION'; checks.append(('interrupted_reservation_releases_only',r.to_dict()))
    r=recover_interrupted_reservation({'reservation_id':'R-2','state':'reserved','consumed':True,'released':True}); assert r.decision=='stop' and r.reason=='RECOVERY_RESERVATION_CONFLICT'; checks.append(('conflicting_reservation_fails_closed',r.to_dict()))
    r=apply_consume_once({'R-3'},'R-3'); assert r.decision=='stop' and r.reason=='RECOVERY_DUPLICATE_CONSUME_BLOCKED'; checks.append(('duplicate_consume_blocked',r.to_dict()))
    r=validate_append_only_audit([{'event_id':'E-1','sequence':1},{'event_id':'E-2','sequence':2}]); assert r.decision=='continue'; checks.append(('append_only_sequence_ok',r.to_dict()))
    r=validate_append_only_audit([{'event_id':'E-1','sequence':1},{'event_id':'E-3','sequence':3}]); assert r.decision=='stop' and r.reason=='RECOVERY_AUDIT_SEQUENCE_GAP'; checks.append(('partial_audit_gap_fails_closed',r.to_dict()))
    r=incident_transition('resolved','acknowledged'); assert r.decision=='stop' and r.reason=='RECOVERY_INCIDENT_STATE_REGRESSION_BLOCKED'; checks.append(('incident_regression_blocked',r.to_dict()))
    for name,payload in checks: print(f'✓ {name}: {payload}')
    print('\nRECOVERY FOUNDATION EVIDENCE REPORT'); print({'passed':len(checks),'failed':0}); return 0
if __name__=='__main__': raise SystemExit(main())
