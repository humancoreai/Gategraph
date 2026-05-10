from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / "registry" / "evidence_provenance_registry.json"
MANIFEST = ROOT / "RELEASE_MANIFEST.json"


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def _manifest_files() -> set[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = data.get("files", [])
    out = set()
    for item in files:
        if isinstance(item, str):
            out.add(item)
        elif isinstance(item, dict):
            out.add(item.get("path") or item.get("relative_path") or item.get("file") or "")
    return {x.replace('\\\\', '/') for x in out if x}


def main() -> int:
    data = json.loads(PROV.read_text(encoding="utf-8"))
    manifest_files = _manifest_files()
    checks = []
    edges = []
    for e in data.get("evidence", []):
        for dep in e.get("depends_on", []):
            edges.append((e.get("evidence_id"), dep))
    checks.append(check("dependency_edges_visible", bool(edges), {"edge_count": len(edges)}))
    unresolved = [{"evidence_id": eid, "dep": dep} for eid, dep in edges if not (ROOT / dep).exists()]
    checks.append(check("dependency_paths_resolve", not unresolved, {"unresolved": unresolved}))
    missing_manifest = sorted({dep for _, dep in edges if dep != "RELEASE_MANIFEST.json" and (ROOT / dep).exists() and dep not in manifest_files})
    checks.append(check("dependency_paths_manifested", not missing_manifest, {"missing_manifest": missing_manifest[:10]}))
    self_refs = [{"evidence_id": eid, "dep": dep} for eid, dep in edges if dep.endswith(f"{eid}.py")]
    checks.append(check("no_self_dependency_edges", not self_refs, {"self_refs": self_refs}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
