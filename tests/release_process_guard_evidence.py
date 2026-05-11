#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "release_process_guard.py"), "v0.14.4_CANDIDATE", "candidate", "v0.14.3_STABLE"], cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    payload = json.loads(proc.stdout)
    print(json.dumps({"release_process_guard": payload}, indent=2, sort_keys=True))
    assert proc.returncode == 0
    assert payload["passed"] is True
    git_dir = ROOT / ".git"
    git_dir.mkdir(exist_ok=True)
    git_head = git_dir / "HEAD"
    previous = git_head.read_text(encoding="utf-8") if git_head.exists() else None
    git_head.write_text("ref: refs/heads/main\n", encoding="utf-8")
    try:
        proc_git = subprocess.run([sys.executable, str(ROOT / "tools" / "release_process_guard.py"), "v0.14.4_CANDIDATE", "candidate", "v0.14.3_STABLE"], cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        payload_git = json.loads(proc_git.stdout)
        assert proc_git.returncode == 0
        assert payload_git["passed"] is True
    finally:
        if previous is None:
            try:
                git_head.unlink()
            except FileNotFoundError:
                pass
            try:
                git_dir.rmdir()
            except OSError:
                pass
        else:
            git_head.write_text(previous, encoding="utf-8")

    print("PASS release_process_guard_evidence")
    return 0
if __name__ == "__main__": raise SystemExit(main())
