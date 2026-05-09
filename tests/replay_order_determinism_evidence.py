#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.recovery_foundation import deterministic_replay_signature

def main() -> int:
    records=[
        {'sequence':3,'task_id':'T-3','stage':'runtime_guard','normalized_reason_code':'RT_LOOP_DETECTED'},
        {'sequence':1,'task_id':'T-1','stage':'enforcement','normalized_reason_code':'ENF_NO_TOKEN'},
        {'sequence':2,'task_id':'T-2','stage':'session_budget','normalized_reason_code':'SES_COST_LIMIT'},
    ]
    sig_a=deterministic_replay_signature(records)
    sig_b=deterministic_replay_signature(list(reversed(records)))
    sig_c=deterministic_replay_signature([records[1], records[2], records[0]])
    assert sig_a==sig_b==sig_c
    assert [entry[0] for entry in sig_a] == [1,2,3]
    fallback=deterministic_replay_signature([{'task_id':'B','stage':'x','reason_code':'R2'}, {'task_id':'A','stage':'x','reason_code':'R1'}])
    assert fallback[0][1]=='A' and fallback[1][1]=='B'
    print('✓ explicit_sequence_order_deterministic:', {'signature':sig_a})
    print('✓ fallback_order_deterministic:', {'signature':fallback})
    print('\nREPLAY ORDER DETERMINISM EVIDENCE REPORT'); print({'passed':2,'failed':0}); return 0
if __name__=='__main__': raise SystemExit(main())
