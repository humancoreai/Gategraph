#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "release_process_guard.py"), "v0.13.5_CANDIDATE", "candidate", "v0.13.4_STABLE"], cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    payload = json.loads(proc.stdout)
    print(json.dumps({"release_process_guard": payload}, indent=2, sort_keys=True))
    assert proc.returncode == 0
    assert payload["passed"] is True
    print("PASS release_process_guard_evidence")
    return 0
if __name__ == "__main__": raise SystemExit(main())
