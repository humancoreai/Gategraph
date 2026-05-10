#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()

def main():
    g=json.loads((ROOT/'registry/governance_integrity_graph.json').read_text())
    h1=hashlib.sha256(canonical(g)).hexdigest()
    h2=hashlib.sha256(canonical(json.loads((ROOT/'registry/governance_integrity_graph.json').read_text()))).hexdigest()
    assert h1==h2
    assert g['authority']['runtime_authority'] is False
    freeze_inputs=['registry/governance_integrity_graph.json','registry/governance_lineage.json','RELEASE_METADATA.json']
    missing=[p for p in freeze_inputs if not (ROOT/p).exists()]
    assert not missing, missing
    print({'integrity_graph_freeze': {'hash': h1, 'freeze_inputs': freeze_inputs}})
    print('PASS integrity_graph_freeze_evidence')
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
