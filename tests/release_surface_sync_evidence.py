#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE='v0.12.9_CANDIDATE'
EXPECTED_BASE='v0.12.8_STABLE'
EXPECTED_STATUS='candidate'
EXPECTED_VERSION='0.12.9'
SURFACES=['README.md','VERSION.md','RELEASE_NOTES.md','RELEASE_STATUS.md','RELEASE_METADATA.json','RELEASE_MANIFEST.json','pyproject.toml','tools/build_release.py','tools/verify_release.py','docs/RECOVERY_FOUNDATION.md','docs/RELEASE_v0.12.9_CANDIDATE.md']

def read(p): return (ROOT/p).read_text(encoding='utf-8')
def main() -> int:
    meta=json.loads(read('RELEASE_METADATA.json')); manifest=json.loads(read('RELEASE_MANIFEST.json'))
    assert meta['release']==EXPECTED_RELEASE and manifest['release']==EXPECTED_RELEASE
    assert meta['base']==EXPECTED_BASE and manifest['base']==EXPECTED_BASE
    assert meta['status']==EXPECTED_STATUS
    assert meta['phase']=='Operator Explainability Hygiene'
    assert f'version = "{EXPECTED_VERSION}"' in read('pyproject.toml')
    for rel in SURFACES:
        text=read(rel)
        assert EXPECTED_RELEASE in text, rel
    assert EXPECTED_BASE in read('README.md') and EXPECTED_BASE in read('VERSION.md') and EXPECTED_BASE in read('RELEASE_NOTES.md')
    stale_current=re.findall(r'Current release: \*\*v0\.12\.1_STABLE\*\*|Release: v0\.12\.1_STABLE|Current release: v0\.12\.1_STABLE', read('README.md')+read('VERSION.md')+read('RELEASE_STATUS.md'))
    assert not stale_current, stale_current
    print({'release':EXPECTED_RELEASE,'base':EXPECTED_BASE,'status':EXPECTED_STATUS,'surfaces':SURFACES})
    print('PASS release_surface_sync_evidence'); print("Summary: {'passed': 1, 'failed': 0}"); return 0
if __name__=='__main__': raise SystemExit(main())
