#!/usr/bin/env python3
"""
WHY: Runtime start/stop behavior must be explicit before stable promotion.
INV: Evidence observes CLI/server boundaries only; it does not add runtime behavior.
SEC: Misuse and bad config must fail closed instead of falling back silently.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=30)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    failures: list[str] = []

    help_result = run_cmd([PY, "-m", "src.cli", "--help"])
    if help_result.returncode != 0 or "GateGraph single-node CLI" not in help_result.stdout:
        failures.append("CLI help is not deterministic rc=0")

    missing_command = run_cmd([PY, "-m", "src.cli"])
    if missing_command.returncode == 0:
        failures.append("CLI without command unexpectedly succeeded")

    bad_cfg = write(ROOT / "tests" / "tmp_runtime_bad_config.yaml", "mode: unsupported\ndb_path: gategraph.db\n")
    bad_config_result = run_cmd([PY, "-m", "src.cli", "--config", str(bad_cfg), "status", "--json"])
    bad_cfg.unlink(missing_ok=True)
    if bad_config_result.returncode != 2:
        failures.append(f"bad config rc expected 2, got {bad_config_result.returncode}")
    else:
        try:
            payload = json.loads(bad_config_result.stderr)
            if payload.get("ok") is not False or "only mode" not in payload.get("error", ""):
                failures.append("bad config error payload is not structured/fail-closed")
        except json.JSONDecodeError:
            failures.append("bad config stderr is not structured JSON")

    server_source = (ROOT / "src" / "server.py").read_text(encoding="utf-8")
    required_server_phrases = [
        "prog=\"gategraph-server\"",
        "--host",
        "127.0.0.1",
        "--port",
        "server.serve_forever()",
        "except KeyboardInterrupt",
        "server.server_close()",
        "return 0",
    ]
    missing_server_phrases = [phrase for phrase in required_server_phrases if phrase not in server_source]
    if missing_server_phrases:
        failures.append(f"server startup/shutdown contract drift: {missing_server_phrases}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"Summary: {{'passed': 0, 'failed': {len(failures)}}}")
        return 1

    print("✓ CLI help exits deterministically")
    print("✓ CLI misuse fails non-zero")
    print("✓ invalid config fails closed with structured JSON")
    print("✓ server startup/shutdown contract is explicit in source")
    print("PASS startup_shutdown_semantics_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
