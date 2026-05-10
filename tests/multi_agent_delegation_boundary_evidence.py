#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.multi_agent_delegation import DelegationEdge, assess_delegation_chain, summarize_delegation
PASSED=FAILED=0
def check(name, condition, details=None):
    global PASSED, FAILED
    if condition:
        PASSED += 1; print(f"✓ {name}: {details or {}}")
    else:
        FAILED += 1; print(f"✗ {name}: {details or {}}")
def main():
    single=assess_delegation_chain([DelegationEdge('agent-a','agent-b','TASK-1')])
    check('single_reference_delegation_is_observable_only', single.decision=='continue' and single.reason=='DELEGATION_REFERENCE_ONLY' and single.actor_chain==('agent-a','agent-b'), single.to_dict())
    trans=assess_delegation_chain([DelegationEdge('agent-a','agent-b','TASK-1'), DelegationEdge('agent-b','agent-c','TASK-1')])
    check('transitive_authority_blocked', trans.decision=='stop' and trans.reason=='DELEGATION_TRANSITIVE_AUTHORITY_BLOCKED' and trans.transitive_authority, trans.to_dict())
    circ=assess_delegation_chain([DelegationEdge('agent-a','agent-b','TASK-2'), DelegationEdge('agent-b','agent-a','TASK-2')])
    check('circular_delegation_blocked', circ.decision=='stop' and circ.reason=='DELEGATION_CIRCULAR_CHAIN' and circ.circular_delegation, circ.to_dict())
    amp=assess_delegation_chain([DelegationEdge('agent-a','agent-b','TASK-3', requested_capabilities=('write_files',))])
    check('capability_amplification_blocked', amp.decision=='stop' and amp.reason=='DELEGATION_CAPABILITY_AMPLIFICATION' and amp.capability_amplification, amp.to_dict())
    broken=assess_delegation_chain([DelegationEdge('agent-a','agent-b','TASK-4'), DelegationEdge('agent-x','agent-c','TASK-4')])
    check('actor_chain_loss_fails_closed', broken.decision=='stop' and broken.reason=='DELEGATION_BROKEN_ACTOR_CHAIN', broken.to_dict())
    invalid=assess_delegation_chain([DelegationEdge('agent-a','agent-b','TASK-5', mode='execute_as')])
    check('unsupported_delegation_mode_fails_closed', invalid.decision=='stop' and invalid.reason=='DELEGATION_UNSUPPORTED_MODE', invalid.to_dict())
    summary=summarize_delegation([DelegationEdge('agent-a','agent-b','TASK-6')])
    payload=json.dumps(summary, sort_keys=True)
    forbidden=['capability_token','token','secret','budget_granted','authority_granted']
    check('summary_contains_no_authority_grant', not any(term in payload for term in forbidden), summary)
    print('\nMULTI AGENT DELEGATION BOUNDARY EVIDENCE REPORT')
    print(json.dumps({'passed':PASSED,'failed':FAILED}, indent=2, sort_keys=True))
    if FAILED: return 1
    print('PASS multi_agent_delegation_boundary_evidence')
    print(f"Summary: {{'passed': {PASSED}, 'failed': {FAILED}}}")
    return 0
if __name__ == '__main__': raise SystemExit(main())
