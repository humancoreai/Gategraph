#!/usr/bin/env python3
"""
SEC: development signing material must not be a silent fallback.
INV: deterministic local evidence may opt in explicitly; default remains fail-closed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contextlib import contextmanager

from src.capability_token import load_trusted_keyring

@contextmanager
def clean_env():
    keys = [
        "GATEGRAPH_TOKEN_KEYRING_JSON",
        "GATEGRAPH_TOKEN_SIGNING_SECRET",
        "GATEGRAPH_TOKEN_ACTIVE_KEY_ID",
        "GATEGRAPH_ALLOW_DEV_KEYRING",
    ]
    old = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k in keys:
            if old[k] is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = old[k]

def check(name: str, ok: bool, detail: object):
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok

def main() -> int:
    checks = []
    with clean_env():
        try:
            load_trusted_keyring()
            checks.append(check("implicit_dev_keyring_blocked", False, "unexpected keyring"))
        except RuntimeError as exc:
            checks.append(check("implicit_dev_keyring_blocked", "GATEGRAPH_ALLOW_DEV_KEYRING=1" in str(exc), str(exc)))

    with clean_env():
        os.environ["GATEGRAPH_ALLOW_DEV_KEYRING"] = "1"
        keyring = load_trusted_keyring()
        checks.append(check("explicit_dev_keyring_allowed", "local-dev-v2" in keyring, sorted(keyring)))

    with clean_env():
        os.environ["GATEGRAPH_TOKEN_SIGNING_SECRET"] = "unit-secret"
        keyring = load_trusted_keyring()
        checks.append(check("configured_secret_allowed_without_dev_flag", bool(keyring), sorted(keyring)))

    failed = [name for name, ok in checks if not ok]
    print("DEV KEYRING GATE EVIDENCE REPORT")
    print({"passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
