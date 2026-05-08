"""
WHY: Legacy multiprocessing supervision was vulnerable to environment-specific child shutdown hangs.
INV: This compatibility entrypoint delegates to the file-backed isolated CI runner; production semantics are untouched.
SEC: Evidence scripts still run in bounded subprocesses with a clean local DB slate per group.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from tests.evidence_ci import main as evidence_ci_main
    return evidence_ci_main()


if __name__ == "__main__":
    # WHY: mirror the isolated runner behavior and avoid interpreter shutdown noise in CI shells.
    os._exit(main())
