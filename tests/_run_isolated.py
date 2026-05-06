"""
WHY: Evidence scripts can trigger environment-specific shutdown/import hangs when executed as __main__ via runpy.
INV: This wrapper only orchestrates test execution; it does not change production governance/enforcement/runtime semantics.
SEC: Each script is loaded as a normal module and only its public main()/run() entrypoint is called.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = PROJECT_ROOT / "tests"

for import_path in (str(PROJECT_ROOT), str(TESTS_DIR)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)


def _finish(code: int) -> None:
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(code)


def _load_entrypoint(script_path: Path) -> Callable[[], object]:
    if not script_path.exists():
        raise FileNotFoundError(str(script_path))

    # WHY: import by module name mirrors direct developer usage and avoids duplicate module identity.
    if script_path.parent.resolve() != TESTS_DIR.resolve():
        raise RuntimeError(f"Evidence scripts must live under {TESTS_DIR}: {script_path}")
    module = importlib.import_module(script_path.stem)

    for entrypoint in ("main", "run"):
        fn = getattr(module, entrypoint, None)
        if callable(fn):
            return fn
    raise RuntimeError(f"{script_path} exposes neither main() nor run()")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: _run_isolated.py <script>", file=sys.stderr)
        return 2

    script_path = Path(argv[1])
    if not script_path.is_absolute():
        script_path = (PROJECT_ROOT / script_path).resolve()

    old_cwd = Path.cwd()
    try:
        os.chdir(PROJECT_ROOT)
        fn = _load_entrypoint(script_path)
        result = fn()
        return result if isinstance(result, int) else 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except BaseException as exc:
        print(f"isolated runner error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    _finish(main(sys.argv))
