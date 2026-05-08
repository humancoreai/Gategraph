"""
WHY: evidence scripts can trigger environment-specific Python shutdown hangs.
INV: this wrapper preserves the script's logical exit code but bypasses interpreter teardown.
"""
from __future__ import annotations

import os
import runpy
import sys

if len(sys.argv) != 2:
    print("usage: _run_isolated.py <script>", file=sys.stderr)
    os._exit(2)

try:
    runpy.run_path(sys.argv[1], run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    os._exit(code)
except BaseException as exc:
    print(f"isolated runner error: {exc!r}", file=sys.stderr)
    os._exit(1)

os._exit(0)
