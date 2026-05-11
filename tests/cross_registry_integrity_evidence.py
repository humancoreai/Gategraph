from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    schema = json.loads((ROOT / "registry" / "schema_governance_registry.json").read_text(encoding="utf-8"))
    invariant = json.loads((ROOT / "registry" / "invariant_surface_registry.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest_paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
    schema_paths = {entry["path"] for entry in schema.get("schemas", [])}
    missing_schema_files = sorted(p for p in schema_paths if not (ROOT / p).exists())
    checks.append(check("schema_registry_paths_exist", not missing_schema_files, {"missing": missing_schema_files}))
    missing_from_manifest = sorted(p for p in schema_paths if p != "RELEASE_MANIFEST.json" and p not in manifest_paths)
    checks.append(check("schema_paths_declared_in_manifest", not missing_from_manifest, {"missing": missing_from_manifest}))
    evidence_refs = {ev for spec in invariant.get("invariants", {}).values() for ev in spec.get("evidence", [])}
    missing_evidence = sorted(ev for ev in evidence_refs if not (ROOT / "tests" / ev).exists())
    checks.append(check("invariant_evidence_refs_resolve", not missing_evidence, {"missing": missing_evidence}))
    orphaned_surfaces = sorted({surface for spec in invariant.get("invariants", {}).values() for surface in spec.get("surfaces", []) if not isinstance(surface, str) or not surface})
    checks.append(check("surface_refs_non_empty", not orphaned_surfaces, {"invalid": orphaned_surfaces}))
    release_doc = ROOT / "docs" / "RELEASE_v0.14.2_STABLE.md"
    checks.append(check("release_doc_present", release_doc.exists(), {"path": str(release_doc.relative_to(ROOT))}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
