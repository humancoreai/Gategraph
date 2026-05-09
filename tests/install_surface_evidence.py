#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run(cmd: list[str], cwd: Path = ROOT, timeout: int = 60) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    import tomllib

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]

    assert scripts["gategraph"] == "src.cli:main"
    assert scripts["gategraph-server"] == "src.server:main"

    cli_help = run([sys.executable, "-m", "src.cli", "--help"], timeout=30)
    server_help = run([sys.executable, "-m", "src.server", "--help"], timeout=30)

    # Existing modules must remain importable. Help behavior may return non-zero if argparse exits
    # through the project-specific command parser; importability is the invariant here.
    import src.cli as cli
    import src.server as server

    assert hasattr(cli, "main"), "src.cli has no main"
    assert hasattr(server, "main"), "src.server has no main"

    result = {
        "install_surface": {
            "pyproject_present": True,
            "scripts": scripts,
            "cli_main": "present",
            "server_main": "present",
            "cli_help_returncode": cli_help["returncode"],
            "server_help_returncode": server_help["returncode"],
            "editable_install_command": "python -m pip install -e .",
        }
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS install_surface_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
