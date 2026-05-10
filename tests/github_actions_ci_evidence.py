#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "evidence_ci.yml"
DOC = ROOT / "docs" / "GITHUB_ACTIONS_CI.md"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks: list[tuple[str, bool, dict]] = []
    workflow_exists = WORKFLOW.exists()
    doc_exists = DOC.exists()
    checks.append(check("workflow_exists", workflow_exists, {"path": str(WORKFLOW.relative_to(ROOT))}))
    checks.append(check("documentation_exists", doc_exists, {"path": str(DOC.relative_to(ROOT))}))
    if not workflow_exists:
        failed = [name for name, ok, _ in checks if not ok]
        print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
        return 1

    text = WORKFLOW.read_text(encoding="utf-8")
    lower = text.lower()
    # WHY: CI is evidence-only; it must not become a hidden release or deployment authority.
    forbidden = ["secrets.", "pypi", "deploy", "gh release", "contents: write"]
    found = [item for item in forbidden if item in lower]
    checks.append(check("no_secret_or_publish_surface", not found, {"found": found}))

    checks.append(check("windows_runner", "runs-on: windows-latest" in text, {}))
    checks.append(check("python_311_pinned", re.search(r"python-version:\s*[\"']3\.11[\"']", text) is not None, {}))
    checks.append(check("evidence_ci_entrypoint", "python tests\\evidence_ci.py" in text, {}))
    checks.append(check("read_only_permissions", re.search(r"permissions:\s*\n\s*contents:\s*read", text) is not None, {}))
    checks.append(check("artifact_upload_always", "if: always()" in text and "tests/logs/*.json" in text, {}))
    checks.append(check("manual_dispatch_available", "workflow_dispatch:" in text, {}))

    if doc_exists:
        doc = DOC.read_text(encoding="utf-8")
        required_doc_markers = ["validation surface only", "No automatic Candidate to Stable promotion", "No secret access"]
        missing = [marker for marker in required_doc_markers if marker not in doc]
        checks.append(check("doc_declares_non_authority", not missing, {"missing": missing}))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
