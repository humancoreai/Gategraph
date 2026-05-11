#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE='v0.14.10_CANDIDATE'; EXPECTED_BASE='v0.14.9_STABLE'
REQUIRED_FILES={'gategraph/context/context_lifecycle.py','docs/CONTEXT_LIFECYCLE_MODEL.md','tests/context_lifecycle_evidence.py','tests/context_freeze_coupling_evidence.py','tests/context_replay_explain_boundary_evidence.py','docs/RELEASE_v0.14.10_CANDIDATE.md'}
REQUIRED_EVIDENCE={'context_lifecycle_evidence','context_freeze_coupling_evidence','context_replay_explain_boundary_evidence'}
PASSED=FAILED=0
def check(name, condition, details=None):
    global PASSED, FAILED
    if condition: PASSED+=1; print(f"✓ {name}: {details or {}}")
    else: FAILED+=1; print(f"✗ {name}: {details or {}}")
def main():
    metadata=json.loads((ROOT/'RELEASE_METADATA.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    paths={entry['path'] for entry in manifest['files']}
    evidence_ci=(ROOT/'tests'/'evidence_ci.py').read_text(encoding='utf-8')
    doc=(ROOT/'docs'/'CONTEXT_LIFECYCLE_MODEL.md').read_text(encoding='utf-8')
    check('release_metadata_context_lifecycle_scope', metadata['release']==EXPECTED_RELEASE and metadata['base']==EXPECTED_BASE and metadata['status']=='candidate' and metadata.get('context_lifecycle_scope') is True, {'release':metadata.get('release'),'base':metadata.get('base'),'status':metadata.get('status'),'context_lifecycle_scope':metadata.get('context_lifecycle_scope')})
    check('manifest_contains_context_lifecycle_files', manifest['release']==EXPECTED_RELEASE and manifest['base']==EXPECTED_BASE and manifest['status']=='candidate' and not (REQUIRED_FILES-paths), sorted(REQUIRED_FILES-paths))
    check('evidence_ci_contains_context_lifecycle_gates', all(name in evidence_ci for name in REQUIRED_EVIDENCE), sorted(REQUIRED_EVIDENCE))
    check('docs_state_non_scope', all(phrase in doc for phrase in ['not a memory system','Unknown lifecycle states fail closed','must not become executable context','No memory system']), {'doc':'CONTEXT_LIFECYCLE_MODEL.md'})
    forbidden=[p for p in paths if p.startswith('dist/') or p.startswith('tests/logs/') or p.endswith(('.db','.csv','.pyc','.pyo','.log','.tmp','.zip'))]
    check('manifest_has_no_generated_artifacts', not forbidden, forbidden)
    print('\nCONTEXT FREEZE COUPLING EVIDENCE REPORT'); print(json.dumps({'passed':PASSED,'failed':FAILED}, indent=2, sort_keys=True))
    if FAILED: return 1
    print('PASS context_freeze_coupling_evidence'); print(f"Summary: {{'passed': {PASSED}, 'failed': {FAILED}}}"); return 0
if __name__=='__main__': raise SystemExit(main())
