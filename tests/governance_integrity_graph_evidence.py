#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GRAPH=ROOT/'registry'/'governance_integrity_graph.json'
EDGE_TYPES={'depends_on','validated_by','affects','lineage_of'}

def main():
    g=json.loads(GRAPH.read_text())
    assert g['release']=='v0.14.10_CANDIDATE'
    assert g['base']=='v0.14.9_STABLE'
    assert g['schema_version']=='0.14.6'
    for k in ['runtime_authority','policy_mutation','auto_repair','dynamic_loading','self_healing']:
        assert g['authority'][k] is False, k
    assert set(g['edge_types'])==EDGE_TYPES
    node_ids={n['id'] for n in g['nodes']}
    assert len(node_ids)==len(g['nodes'])
    assert {'semantic_object_registry','release_manifest','freeze_snapshot','replay_provenance'} <= node_ids
    for e in g['edges']:
        assert e['type'] in EDGE_TYPES, e
        assert e['from'] in node_ids, e
        if e['type'] != 'validated_by' and not e['to'].startswith('v'):
            assert e['to'] in node_ids, e
    print({'governance_integrity_graph': {'nodes': len(g['nodes']), 'edges': len(g['edges']), 'edge_types': sorted(EDGE_TYPES)}})
    print('PASS governance_integrity_graph_evidence')
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
