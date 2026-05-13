#!/usr/bin/env python3
"""INV: Candidate release surfaces derive the same version/base/status from release metadata."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    meta = json.loads((ROOT / 'RELEASE_METADATA.json').read_text(encoding='utf-8'))
    release = meta['release']; version = meta['version']; base = meta['base']; status = meta['status']
    assert release == 'v0.16.0_STABLE'
    assert version == '0.16.0'
    assert base == 'v0.15.9_STABLE'
    assert status == 'stable'
    for name in ['README.md','VERSION.md','RELEASE_STATUS.md','RELEASE_NOTES.md']:
        text = (ROOT / name).read_text(encoding='utf-8')
        assert release in text, name
        assert base in text, name
        assert version in text, name
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert release in readme
    assert base in readme
    assert 'v0.16.0_CANDIDATE' not in readme
    print({'release_ssot_stable': {'release': release, 'base': base, 'status': status, 'manual_drift_surfaces': False}})
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__ == '__main__': raise SystemExit(main())
