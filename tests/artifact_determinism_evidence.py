#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RELEASE="v0.14.9_STABLE"
EXPECTED_BASE="v0.14.8_STABLE"
FORBIDDEN_PARTS={'__pycache__','.pytest_cache','dist'}
FORBIDDEN_SUFFIXES={'.pyc','.zip','.log','.db','.csv'}
def check(name, ok, detail):
    print(("✓" if ok else "✗")+f" {name}: {detail}")
    return name, ok, detail
def main():
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text())
    entries=manifest.get('files',[])
    paths=[e.get('path') for e in entries]
    stale=[]
    for p in paths:
        parts=set(Path(p).parts)
        if parts & FORBIDDEN_PARTS or Path(p).suffix in FORBIDDEN_SUFFIXES:
            stale.append(p)
    checks=[]
    checks.append(check('manifest_release_current', manifest.get('release')==EXPECTED_RELEASE, {'release':manifest.get('release')}))
    checks.append(check('manifest_base_previous_stable', manifest.get('base')==EXPECTED_BASE, {'base':manifest.get('base')}))
    checks.append(check('manifest_paths_sorted', paths==sorted(paths), {'count':len(paths)}))
    checks.append(check('manifest_has_no_generated_artifacts', not stale, stale))
    checks.append(check('manifest_file_count_matches', manifest.get('file_count')==len(entries), {'declared':manifest.get('file_count'),'actual':len(entries)}))
    failed=[n for n,ok,_ in checks if not ok]
    print('Summary:', {'passed':len(checks)-len(failed),'failed':len(failed),'failed_checks':failed})
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
