#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def downstream(graph, start):
    edges=graph['edges']
    seen=set(); frontier=[start]
    while frontier:
        cur=frontier.pop()
        for e in edges:
            if e['from']==cur and e['type'] in {'affects','depends_on'} and e['to'] not in seen:
                seen.add(e['to']); frontier.append(e['to'])
    return seen

def main():
    g=json.loads((ROOT/'registry/governance_integrity_graph.json').read_text())
    impact=downstream(g,'semantic_registry_lock')
    assert 'freeze_snapshot' in impact
    replay=downstream(g,'governance_lineage')
    assert 'replay_provenance' in replay
    assert g['authority']['auto_repair'] is False
    print({'impact_visibility': {'semantic_registry_lock_affects': sorted(impact), 'governance_lineage_affects': sorted(replay)}})
    print('PASS governance_impact_visibility_evidence')
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
