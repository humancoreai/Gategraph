#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from gategraph.context import classify_context, required_provenance
PASSED=FAILED=0
def check(name, condition, details=None):
    global PASSED, FAILED
    if condition: PASSED+=1; print(f"✓ {name}: {details or {}}")
    else: FAILED+=1; print(f"✗ {name}: {details or {}}")
def main():
    missing=classify_context({'context_type':'untrusted_external_context','source':'external_api'})
    check('provenance_required', missing.decision=='stop' and missing.reason=='CTX_PROVENANCE_REQUIRED', missing.to_dict())
    unknown=classify_context({'context_type':'unknown','source':'x','trust_level':'untrusted','governance_influence':False,'executable':False,'replayable':True})
    check('unknown_context_type_fail_closed', unknown.decision=='stop' and unknown.reason=='CTX_UNKNOWN_TYPE', unknown.to_dict())
    external=classify_context(required_provenance('untrusted_external_context','external_api'))
    check('governance_influence_false_for_external', external.decision=='continue' and external.provenance and external.provenance.governance_influence is False and external.provenance.executable is False, external.to_dict())
    replay=classify_context(required_provenance('replay_context','audit_log'))
    check('replay_context_non_executable', replay.decision=='continue' and replay.provenance and replay.provenance.executable is False and replay.provenance.trust_level=='reference', replay.to_dict())
    tampered=required_provenance('untrusted_external_context','external_api'); tampered['governance_influence']=True
    bad=classify_context(tampered)
    check('trust_level_inconsistency_fail_closed', bad.decision=='stop' and bad.reason=='CTX_PROVENANCE_INCONSISTENT', bad.to_dict())
    print('\nCONTEXT PROVENANCE EVIDENCE REPORT'); print(json.dumps({'passed':PASSED,'failed':FAILED}, indent=2, sort_keys=True))
    if FAILED: return 1
    print('PASS context_provenance_evidence'); print(f"Summary: {{'passed': {PASSED}, 'failed': {FAILED}}}"); return 0
if __name__ == '__main__': raise SystemExit(main())
