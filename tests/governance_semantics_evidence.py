#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gategraph.semantics.object_boundary import assert_no_reference_promotion, classify_object

def check(name, cond, detail):
    assert cond, detail
    print(f"✓ {name}: {detail}")

def main():
    cases=[]
    d=assert_no_reference_promotion({"object_type":"replay_object"}, "execution")
    check("replay_object_not_executable", d.decision=="stop" and d.reason=="SEM_REFERENCE_PROMOTION_BLOCKED", d.__dict__)
    cases.append(d)
    d=assert_no_reference_promotion({"object_type":"explain_object"}, "policy_mutation")
    check("explain_object_not_policy", d.decision=="stop", d.__dict__)
    cases.append(d)
    d=assert_no_reference_promotion({"object_type":"proposal_object"}, "capability_creation")
    check("proposal_object_not_capability", d.decision=="stop", d.__dict__)
    cases.append(d)
    d=classify_object({"object_type":"monitoring_object", "executable": True, "governance_influence": True})
    check("reference_flags_forced_non_authoritative", d.decision=="continue" and not d.executable and not d.governance_influence, d.__dict__)
    cases.append(d)
    d=classify_object({"object_type":"unknown_object"})
    check("unknown_object_fails_closed", d.decision=="stop", d.__dict__)
    cases.append(d)
    print("GOVERNANCE SEMANTICS EVIDENCE REPORT")
    print({"passed":5,"failed":0})
    print("PASS governance_semantics_evidence")
    return 0
if __name__=="__main__": raise SystemExit(main())
