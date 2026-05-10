"""Synthetic evidence target for evidence_runner_selftest.py."""
from __future__ import annotations

import os
import subprocess
import sys
import time


def main() -> int:
    mode = os.environ.get("RUNNER_SELFTEST_MODE", "pass")
    if mode == "pass":
        print("Summary: {'passed': 1, 'failed': 0}", flush=True)
        return 0
    if mode == "fail":
        print("Summary: {'passed': 0, 'failed': 1}", flush=True)
        return 1
    if mode == "hang":
        print("hang entered", flush=True)
        time.sleep(60)
        return 0
    if mode == "child_hang":
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        print(f"CHILD_PID:{child.pid}", flush=True)
        time.sleep(60)
        return 0
    print(f"unknown mode: {mode}", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
