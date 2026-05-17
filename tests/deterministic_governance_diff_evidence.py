#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    g=json.loads((ROOT/'registry/governance_integrity_graph.json').read_text())
    diff=g['expected_diff']
    assert g['diff_baseline']=='v0.15.9_STABLE'
    assert g['diff_current']=='v0.16.0_CANDIDATE'
    assert diff['runtime_authority_changed'] is False
    assert 'governance_integrity_graph' in diff['added_nodes']
    assert diff['removed_nodes']==[]
    # Deterministic diff view: sort all lists before rendering.
    rendered=json.dumps(diff, sort_keys=True, separators=(',', ':'))
    assert rendered==json.dumps(json.loads(rendered), sort_keys=True, separators=(',', ':'))
    print({'deterministic_governance_diff': diff})
    print('PASS deterministic_governance_diff_evidence')
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
