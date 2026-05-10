"""
WHY: evidence scripts can trigger environment-specific Python shutdown hangs after logical completion.
INV: this wrapper preserves the script's logical exit code and exits only after explicit stream flushing.
SEC: evidence scripts are expected to close DB handles themselves before returning; the wrapper is not a DB lifecycle owner.
"""
from __future__ import annotations

import os
import runpy
import sys


def _exit(code: int) -> None:
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(code)


if len(sys.argv) != 2:
    print("usage: _run_isolated.py <script>", file=sys.stderr)
    _exit(2)

try:
    runpy.run_path(sys.argv[1], run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    _exit(code)
except BaseException as exc:
    print(f"isolated runner error: {exc!r}", file=sys.stderr)
    _exit(1)

_exit(0)
