#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE='v0.17.6_STABLE'; EXPECTED_BASE='v0.17.5_STABLE'
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def main() -> int:
    meta=json.loads(read('RELEASE_METADATA.json')); manifest=json.loads(read('RELEASE_MANIFEST.json'))
    assert meta['release']==EXPECTED_RELEASE and meta['base']==EXPECTED_BASE and meta['status'] in {'candidate','stable'}
    assert meta['recovery_foundation_scope'] is True and meta['replay_recovery_consistency_scope'] is True
    paths={e['path'] for e in manifest['files']}
    required={'src/recovery_foundation.py','tests/recovery_foundation_evidence.py','tests/replay_recovery_consistency_evidence.py','tests/surface_recovery_consistency_evidence.py','docs/RECOVERY_FOUNDATION.md','docs/RELEASE_v0.17.6_STABLE.md'}
    assert not (required-paths), f'manifest missing recovery files: {sorted(required-paths)}'
    assert EXPECTED_RELEASE in read('README.md') and EXPECTED_BASE in read('README.md')
    notes = read('RELEASE_NOTES.md')
    assert EXPECTED_RELEASE in notes and 'Evidence Lifecycle Cleanup Formalization' in notes
    print({'release':EXPECTED_RELEASE,'base':EXPECTED_BASE,'required_files':sorted(required)}); print('PASS surface_recovery_consistency_evidence'); print("Summary: {'passed': 1, 'failed': 0}"); return 0
if __name__=='__main__': raise SystemExit(main())
