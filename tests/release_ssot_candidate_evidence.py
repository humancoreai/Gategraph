#!/usr/bin/env python3
"""INV: Candidate release surfaces derive the same version/base/status from release metadata."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    meta = json.loads((ROOT / 'RELEASE_METADATA.json').read_text(encoding='utf-8'))
    release = meta['release']; version = meta['version']; base = meta['base']; status = meta['status']
    assert release == 'v0.16.5_CANDIDATE'
    assert version == '0.16.5'
    assert base == 'v0.16.4_STABLE'
    assert status == 'candidate'
    for name in ['README.md','VERSION.md','RELEASE_STATUS.md','RELEASE_NOTES.md']:
        text = (ROOT / name).read_text(encoding='utf-8')
        assert release in text, name
        assert base in text, name
        assert version in text, name
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert release in readme
    assert base in readme
    # Candidate surfaces may name the candidate itself, but must not claim its future stable as current.
    
    if meta.get('status') == 'candidate':
        assert meta.get('future_stable', 'v0.16.5_CANDIDATE') not in readme
    print({'release_ssot_candidate': {'release': release, 'base': base, 'status': status, 'manual_drift_surfaces': False}})
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__ == '__main__': raise SystemExit(main())
