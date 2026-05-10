#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    g=json.loads((ROOT/'registry/governance_integrity_graph.json').read_text())
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text())
    paths={e['path'] for e in manifest['files']}
    nodes=g['nodes']
    missing=[n['path'] for n in nodes if 'path' in n and n['path'] not in paths and not (ROOT/n['path']).exists()]
    assert not missing, missing
    edges=g['edges']
    validated={e['from'] for e in edges if e['type']=='validated_by'}
    key_nodes={n['id'] for n in nodes if n['kind'] in {'registry','lock','lineage','manifest'}}
    orphans=sorted(key_nodes-validated-{'release_manifest'})
    assert not orphans, orphans
    print({'orphan_governance_artifact_check': {'checked_nodes': len(nodes), 'orphans': orphans}})
    print('PASS orphan_governance_artifact_evidence')
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
