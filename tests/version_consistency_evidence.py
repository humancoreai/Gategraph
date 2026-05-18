#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE='v0.17.2_STABLE'
EXPECTED_BASE='v0.17.1_STABLE'
EXPECTED_STATUS = "candidate" if EXPECTED_RELEASE.endswith("_CANDIDATE") else "stable"
EXPECTED_VERSION = "0.17.2"
SURFACES=['README.md','VERSION.md','RELEASE_NOTES.md','RELEASE_STATUS.md','RELEASE_METADATA.json','pyproject.toml','tools/build_release.py','tools/verify_release.py']
def main():
    meta=json.loads((ROOT/'RELEASE_METADATA.json').read_text())
    assert meta['release']==EXPECTED_RELEASE
    assert meta['base']==EXPECTED_BASE
    assert meta['status']==EXPECTED_STATUS
    py=(ROOT/'pyproject.toml').read_text()
    assert f'version = "{EXPECTED_VERSION}"' in py
    for rel in SURFACES:
        text=(ROOT/rel).read_text(encoding='utf-8')
        assert EXPECTED_RELEASE in text, rel
    assert EXPECTED_BASE in (ROOT/'README.md').read_text()
    assert EXPECTED_BASE in (ROOT/'VERSION.md').read_text()
    assert EXPECTED_BASE in (ROOT/'RELEASE_NOTES.md').read_text()
    print({'release':EXPECTED_RELEASE,'base':EXPECTED_BASE,'status':EXPECTED_STATUS,'version':EXPECTED_VERSION,'surfaces':SURFACES})
    print('PASS version_consistency_evidence')
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
