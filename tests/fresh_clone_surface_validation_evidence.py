#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE="v0.16.1_CANDIDATE"
EXPECTED_BASE="v0.16.0_STABLE"
REQUIRED=[
 'README.md','VERSION.md','RELEASE_STATUS.md','RELEASE_METADATA.json','RELEASE_MANIFEST.json',
 'docs/RELEASE_v0.16.1_CANDIDATE.md','docs/FRESH_CLONE_SURFACE_VALIDATION.md','docs/FAILURE_ROOT_CAUSE_GROUPING.md','docs/ARTIFACT_DETERMINISM.md',
 'tests/failure_root_cause_grouping_evidence.py','tests/artifact_determinism_evidence.py','tests/fresh_clone_surface_validation_evidence.py'
]
def check(name, ok, detail):
    print(("✓" if ok else "✗")+f" {name}: {detail}")
    return name, ok, detail
def main():
    meta=json.loads((ROOT/'RELEASE_METADATA.json').read_text())
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text())
    mpaths={e['path'] for e in manifest.get('files',[]) if isinstance(e,dict) and 'path' in e}
    missing=[p for p in REQUIRED if not (ROOT/p).exists()]
    unmanifested=[p for p in REQUIRED if p not in mpaths and p!='RELEASE_MANIFEST.json']
    checks=[]
    checks.append(check('metadata_current_candidate', meta.get('release')==EXPECTED_RELEASE and meta.get('base')==EXPECTED_BASE and meta.get('status')=='candidate', {'release':meta.get('release'),'base':meta.get('base'),'status':meta.get('status')}))
    checks.append(check('manifest_current_candidate', manifest.get('release')==EXPECTED_RELEASE and manifest.get('base')==EXPECTED_BASE and manifest.get('status')=='candidate', {'release':manifest.get('release'),'base':manifest.get('base'),'status':manifest.get('status')}))
    checks.append(check('required_surfaces_present', not missing, {'missing':missing}))
    checks.append(check('required_surfaces_manifested', not unmanifested, {'missing':unmanifested}))
    checks.append(check('fresh_clone_non_authority_declared', meta.get('fresh_clone_surface_validation_scope') is True and meta.get('runtime_logic_changed') is False, {'scope':meta.get('fresh_clone_surface_validation_scope'),'runtime_logic_changed':meta.get('runtime_logic_changed')}))
    failed=[n for n,ok,_ in checks if not ok]
    print('Summary:', {'passed':len(checks)-len(failed),'failed':len(failed),'failed_checks':failed})
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
