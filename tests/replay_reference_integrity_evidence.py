#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.recovery_foundation import validate_reference_only_object

def main() -> int:
    checks=[]
    for context_type in ('replay_context','explain_snapshot','archive_record','recovery_snapshot'):
        r=validate_reference_only_object({'context_type':context_type,'executable':False,'governance_influence':False,'rehydrate_runtime':False}); assert r.decision=='continue'; checks.append((f'{context_type}_reference_only', r.to_dict()))
    r=validate_reference_only_object({'context_type':'replay_context','executable':True}); assert r.decision=='stop' and r.reason=='REPLAY_REFERENCE_EXECUTABLE_BLOCKED'; checks.append(('executable_replay_blocked', r.to_dict()))
    r=validate_reference_only_object({'context_type':'recovery_snapshot','governance_influence':True}); assert r.decision=='stop' and r.reason=='REPLAY_REFERENCE_GOVERNANCE_INFLUENCE_BLOCKED'; checks.append(('governance_influence_blocked', r.to_dict()))
    r=validate_reference_only_object({'context_type':'archive_record','rehydrate_runtime':True}); assert r.decision=='stop' and r.reason=='REPLAY_REFERENCE_RUNTIME_REHYDRATION_BLOCKED'; checks.append(('runtime_rehydration_blocked', r.to_dict()))
    r=validate_reference_only_object({'context_type':'explain_snapshot','capability_token':'tok'}); assert r.decision=='stop' and r.reason=='REPLAY_REFERENCE_CAPABILITY_MATERIAL_BLOCKED'; checks.append(('capability_material_blocked', r.to_dict()))
    for name,payload in checks: print(f'✓ {name}: {payload}')
    print('\nREPLAY REFERENCE INTEGRITY EVIDENCE REPORT'); print({'passed':len(checks),'failed':0}); return 0
if __name__=='__main__': raise SystemExit(main())
