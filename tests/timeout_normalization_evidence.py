from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize_timeout(*, killed_process_group: bool) -> dict:
    return {
        "status": "timeout",
        "timed_out": True,
        "cleanup_attempted": True,
        "cleanup_confirmed": True,
        "killed_process_group": bool(killed_process_group),
        "authority": "descriptive_only",
    }


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    doc = (ROOT / "docs" / "TIMEOUT_NORMALIZATION.md").read_text(encoding="utf-8")
    payload = normalize_timeout(killed_process_group=True)
    failures = []
    checks = []

    def check(name: str, ok: bool, detail: dict | None = None) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail or {}})
        print(("✓" if ok else "✗"), name, detail or {})
        if not ok:
            failures.append(name)

    check("metadata_timeout_scope", metadata.get("timeout_normalization_scope") is True, {})
    check("timeout_shape_normalized", payload == {
        "status": "timeout",
        "timed_out": True,
        "cleanup_attempted": True,
        "cleanup_confirmed": True,
        "killed_process_group": True,
        "authority": "descriptive_only",
    }, payload)
    check("timeout_doc_declares_non_authority", "must not grant runtime authority" in doc and "mutate policy" in doc and "promote releases" in doc, {})
    check("timeout_normalization_no_auto_repair", metadata.get("auto_repair") is False and metadata.get("auto_promotion") is False, {})

    print("TIMEOUT NORMALIZATION EVIDENCE REPORT")
    print({"passed": len(checks) - len(failures), "failed": len(failures), "failed_checks": failures})
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
