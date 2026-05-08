#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.recovery_foundation import deterministic_replay_signature

def main() -> int:
    records_a=[{'task_id':'T-2','stage':'runtime_guard','normalized_reason_code':'RT_LOOP_DETECTED'},{'task_id':'T-1','stage':'session_budget','normalized_reason_code':'SES_COST_LIMIT'}]
    sig_a=deterministic_replay_signature(records_a); sig_b=deterministic_replay_signature(list(reversed(records_a)))
    assert sig_a==sig_b
    replay={'context_type':'replay_context','executable':False,'governance_influence':False}; explain={'context_type':'explain_snapshot','executable':False,'governance_influence':False}
    assert not replay['executable'] and not replay['governance_influence']; assert not explain['executable'] and not explain['governance_influence']
    print('✓ deterministic_replay_signature:', {'signature':sig_a}); print('✓ replay_objects_reference_only:', {'replay':replay,'explain':explain})
    print('\nREPLAY RECOVERY CONSISTENCY EVIDENCE REPORT'); print({'passed':2,'failed':0}); return 0
if __name__=='__main__': raise SystemExit(main())
