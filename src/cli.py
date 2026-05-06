"""
WHY: CLI is the stable single-node entry point for operating GateGraph without test harnesses.
INV: CLI is an adapter only; it must not duplicate or bypass Governance/Enforcement decisions.
SEC: invalid inputs fail closed and are reported as structured JSON with non-zero exit codes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src import service_adapter
from src.config_loader import AppConfig, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gategraph", description="GateGraph single-node CLI")
    parser.add_argument("--config", default=None, help="Path to config YAML/JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    init_p = sub.add_parser("init", help="Initialize a single-node GateGraph database")
    init_p.add_argument("--reset", action="store_true", help="Delete and recreate the configured DB")
    eval_p = sub.add_parser("evaluate", help="Evaluate a task and emit a structured decision")
    eval_p.add_argument("--task", required=True, help="Path to task JSON")
    eval_p.add_argument("--token-out", default=None, help="Optional path for issued token JSON")
    status_p = sub.add_parser("status", help="Emit a minimal DB/status summary")
    status_p.add_argument("--json", action="store_true", help="Emit JSON")
    export_p = sub.add_parser("export-monitoring", help="Write a read-only monitoring export JSON")
    export_p.add_argument("--out", required=True, help="Output path for monitoring JSON")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "init":
            return _cmd_init(config, reset=args.reset)
        if args.command == "evaluate":
            return _cmd_evaluate(config, task_path=Path(args.task), token_out=Path(args.token_out) if args.token_out else None)
        if args.command == "status":
            return _cmd_status(config)
        if args.command == "export-monitoring":
            return _cmd_export_monitoring(config, out_path=Path(args.out))
        raise ValueError(f"unknown command: {args.command}")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


def _cmd_init(config: AppConfig, *, reset: bool) -> int:
    print(json.dumps(service_adapter.initialize(config, reset=reset), indent=2))
    return 0


def _cmd_evaluate(config: AppConfig, *, task_path: Path, token_out: Path | None) -> int:
    task = json.loads(task_path.read_text(encoding="utf-8"))
    output = service_adapter.evaluate_request(config, task)
    if token_out is not None and output.get("token") is not None:
        token_out.parent.mkdir(parents=True, exist_ok=True)
        token_out.write_text(json.dumps(output["token"], indent=2), encoding="utf-8")
    public_output = dict(output)
    public_output.pop("token", None)
    print(json.dumps(public_output, indent=2))
    return 0 if public_output.get("ok") else 1


def _cmd_status(config: AppConfig) -> int:
    print(json.dumps(service_adapter.status(config), indent=2))
    return 0


def _cmd_export_monitoring(config: AppConfig, *, out_path: Path) -> int:
    report = service_adapter.monitoring(config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out_path": str(out_path), "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
