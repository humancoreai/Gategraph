from __future__ import annotations

import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import promotion_pipeline


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    report = promotion_pipeline.promotion_pipeline_report()

    checks.append(check("pipeline_report_ok", report["ok"], report))
    checks.append(check("surface_tokens_current", report["surface"]["ok"], report["surface"]))
    checks.append(check("manifest_fresh_for_release_surfaces", report["manifest"]["ok"], report["manifest"]))
    checks.append(check("registry_lock_current", report["registry_lock"]["ok"], report["registry_lock"]))
    checks.append(check("pipeline_has_no_runtime_authority", report["no_authority"], {"no_authority": report["no_authority"], "mode": report["mode"]}))

    failed = [name for name, ok, _ in checks if not ok]
    print("PROMOTION PIPELINE HARDENING EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
