from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.15.4_STABLE"
EXPECTED_BASE = "v0.15.4_STABLE"

def check(name: str, ok: bool, detail: dict | None = None) -> dict:
    marker = "✓" if ok else "✗"
    print(f"{marker} {name}: {detail or {}}")
    return {"name": name, "ok": ok, "detail": detail or {}}

def main() -> int:
    data = json.loads((ROOT / "registry" / "evidence_failure_classification.json").read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    ci_text = (ROOT / "tests" / "evidence_ci.py").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest_paths = {item["path"] for item in manifest.get("files", [])}
    ci_names = {m.group(1) for m in re.finditer(r'\("([^"\n]+)",\s*"tests/', ci_text)}
    classes = data.get("classes", {})
    classified = {name for values in classes.values() for name in values}
    mandatory = {"release_integrity_evidence", "release_process_guard_evidence", "version_consistency_evidence", "semantic_registry_lock_evidence", "server_hardening_evidence"}
    checks = [
        check("classification_release_current", data.get("release") == EXPECTED_RELEASE, {"release": data.get("release")}),
        check("classification_base_previous_stable", data.get("base") == EXPECTED_BASE, {"base": data.get("base")}),
        check("classification_descriptive_only", data.get("classification_mode") == "descriptive_grouping_only", {"mode": data.get("classification_mode")}),
        check("no_runtime_authority", data.get("runtime_authority") is False and data.get("auto_repair") is False and data.get("auto_pruning") is False and data.get("auto_promotion") is False, data),
        check("metadata_declares_classification_scope", metadata.get("evidence_failure_classification_scope") is True and metadata.get("evidence_failure_classification_runtime_authority") is False, {"scope": metadata.get("evidence_failure_classification_scope")}),
        check("mandatory_gates_classified", mandatory.issubset(classified), {"missing": sorted(mandatory - classified)}),
        check("classified_names_exist_in_ci", classified.issubset(ci_names), {"missing": sorted(classified - ci_names)}),
        check("classification_registry_manifested", "registry/evidence_failure_classification.json" in manifest_paths, {}),
        check("classification_doc_manifested", "docs/EVIDENCE_FAILURE_CLASSIFICATION.md" in manifest_paths, {}),
        check("classification_evidence_manifested", "tests/evidence_failure_classification_evidence.py" in manifest_paths, {}),
        check("unclassified_fail_closed_declared", data.get("mandatory_unclassified_fail_closed") is True, {}),
    ]
    failed = [c for c in checks if not c["ok"]]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": [c["name"] for c in failed]})
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
