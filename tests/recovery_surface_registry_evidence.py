#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE='v0.13.3_CANDIDATE'
EXPECTED_BASE='v0.13.2_STABLE'
REQUIRED={
 'src/recovery_foundation.py',
 'docs/RECOVERY_FOUNDATION.md',
 'tests/recovery_idempotency_evidence.py',
 'tests/replay_order_determinism_evidence.py',
 'tests/replay_reference_integrity_evidence.py',
 'tests/recovery_surface_registry_evidence.py',
 'tests/release_surface_sync_evidence.py',
 'docs/RELEASE_v0.13.3_CANDIDATE.md',
}

def read(p): return (ROOT/p).read_text(encoding='utf-8')
def main() -> int:
    meta=json.loads(read('RELEASE_METADATA.json')); manifest=json.loads(read('RELEASE_MANIFEST.json'))
    assert meta['release']==EXPECTED_RELEASE and meta['base']==EXPECTED_BASE and meta['status']=='candidate'
    assert meta['recovery_idempotency_scope'] is True and meta['replay_order_determinism_scope'] is True and meta['replay_reference_integrity_scope'] is True
    paths={e['path'] for e in manifest['files']}
    missing=REQUIRED-paths
    assert not missing, f'manifest missing recovery registry files: {sorted(missing)}'
    freeze=read('docs/GOVERNANCE_SURFACE_FREEZE.md')
    registry=read('docs/INVARIANT_REGISTRY.md')
    assert 'semantic/registry surface evidence' in freeze
    assert 'INV-016' in registry and 'INV-017' in registry and 'INV-018' in registry
    print({'release':EXPECTED_RELEASE,'required_files':sorted(REQUIRED)})
    print('PASS recovery_surface_registry_evidence'); print("Summary: {'passed': 1, 'failed': 0}"); return 0
if __name__=='__main__': raise SystemExit(main())
