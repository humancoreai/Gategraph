#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE="v0.15.5_STABLE"
EXPECTED_BASE="v0.15.4_STABLE"
def check(name, ok, detail):
    print(("✓" if ok else "✗")+f" {name}: {detail}")
    return name, ok, detail
def group_failures(failures, registry):
    groups=registry["groups"]
    out={}
    for item in failures:
        matched="unclassified"
        for group,names in groups.items():
            if item in names:
                matched=group; break
        out.setdefault(matched,[]).append(item)
    return {k:sorted(v) for k,v in sorted(out.items())}
def main():
    reg=json.loads((ROOT/'registry'/'failure_root_cause_grouping.json').read_text())
    checks=[]
    checks.append(check('registry_release_current', reg.get('release')==EXPECTED_RELEASE, {'release':reg.get('release')}))
    checks.append(check('registry_base_previous_stable', reg.get('base')==EXPECTED_BASE, {'base':reg.get('base')}))
    checks.append(check('descriptive_only_no_authority', reg.get('runtime_authority') is False and reg.get('auto_repair') is False and reg.get('policy_mutation') is False, {k:reg.get(k) for k in ['runtime_authority','auto_repair','policy_mutation']}))
    sample=['release_integrity_evidence','version_consistency_evidence','semantic_registry_lock_evidence','artifact_determinism_evidence','fresh_clone_surface_validation_evidence']
    grouped=group_failures(sample, reg)
    checks.append(check('related_failures_grouped_deterministically', list(grouped)==sorted(grouped), grouped))
    checks.append(check('release_surface_group_present', 'release_surface' in grouped and len(grouped['release_surface'])==2, grouped))
    failed=[n for n,ok,_ in checks if not ok]
    print('Summary:', {'passed':len(checks)-len(failed),'failed':len(failed),'failed_checks':failed})
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
