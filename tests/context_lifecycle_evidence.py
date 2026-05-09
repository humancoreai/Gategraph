#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from gategraph.context import observe_context_lifecycle, required_provenance
PASSED=FAILED=0
def check(name, condition, details=None):
    global PASSED, FAILED
    if condition: PASSED+=1; print(f"✓ {name}: {details or {}}")
    else: FAILED+=1; print(f"✗ {name}: {details or {}}")
def main():
    ext=required_provenance('untrusted_external_context','external_api')
    first=observe_context_lifecycle(ext,'received','classified')
    check('received_to_classified_reference_only', first.decision=='continue' and first.executable is False and first.provenance_mutated is False and 'lifecycle_observed' in first.markers, first.to_dict())
    bounded=observe_context_lifecycle(ext,'classified','bounded')
    check('classified_to_bounded_no_authority_change', bounded.decision=='continue' and bounded.governance_influence is False and bounded.context_type=='untrusted_external_context', bounded.to_dict())
    replay=required_provenance('replay_context','audit_replay')
    rehydrate=observe_context_lifecycle(replay,'archived','replayed',target_context_type='transient_runtime_context')
    check('replay_rehydration_to_runtime_fails_closed', rehydrate.decision=='stop' and rehydrate.reason=='CTX_REHYDRATION_FORBIDDEN', rehydrate.to_dict())
    bad_state=observe_context_lifecycle(ext,'classified','runtime_promoted')
    check('unknown_lifecycle_state_fails_closed', bad_state.decision=='stop' and bad_state.reason=='CTX_LIFECYCLE_UNKNOWN_STATE', bad_state.to_dict())
    bad_transition=observe_context_lifecycle(ext,'received','archived')
    check('skipped_lifecycle_transition_fails_closed', bad_transition.decision=='stop' and bad_transition.reason=='CTX_LIFECYCLE_TRANSITION_FORBIDDEN', bad_transition.to_dict())
    print('\nCONTEXT LIFECYCLE EVIDENCE REPORT'); print(json.dumps({'passed':PASSED,'failed':FAILED}, indent=2, sort_keys=True))
    if FAILED: return 1
    print('PASS context_lifecycle_evidence'); print(f"Summary: {{'passed': {PASSED}, 'failed': {FAILED}}}"); return 0
if __name__=='__main__': raise SystemExit(main())
