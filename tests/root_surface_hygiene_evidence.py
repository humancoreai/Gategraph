#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOVED={"DEVLOG.md","PRODUCTION_CHECKLIST.md","REPO_HYGIENE.md","STABLE_REPORT.txt","GOVERNANCE_FREEZE_SUMMARY.txt"}
FORBIDDEN_SUFFIXES={".db",".csv",".log",".tmp",".zip"}
def main():
    failed=[]
    for name in MOVED:
        if (ROOT/name).exists(): failed.append(f"root artifact remains: {name}")
        if not (ROOT/'docs'/'release_artifacts'/name).exists(): failed.append(f"moved artifact missing: {name}")
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix.lower() in FORBIDDEN_SUFFIXES:
            failed.append(f"forbidden root suffix: {p.name}")
        if p.is_file() and p.name.upper().startswith('STARTPROMPT'):
            failed.append(f"development prompt in root: {p.name}")
    assert not failed, failed
    print("✓ root release surface contains no moved development artifacts")
    print("✓ release artifacts retained under docs/release_artifacts")
    print("PASS root_surface_hygiene_evidence")
    print("Summary: {'passed': 2, 'failed': 0}")
    return 0
if __name__=='__main__': raise SystemExit(main())
