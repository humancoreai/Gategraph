from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.17.9_CANDIDATE"
EXPECTED_BASE = "v0.17.8_STABLE"
EXPECTED_STATUS = "candidate" if EXPECTED_RELEASE.endswith("_CANDIDATE") else "stable"


def check(name: str, ok: bool, detail: object | None = None) -> dict:
    print(("✓" if ok else "✗"), name, detail if detail is not None else {})
    return {"name": name, "ok": ok, "detail": detail or {}}


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    meta = load_json("RELEASE_METADATA.json")
    reg = load_json("registry/evidence_maintainability_registry.json")
    manifest = load_json("RELEASE_MANIFEST.json")
    manifest_paths = {item["path"] for item in manifest.get("files", [])}
    doc = (ROOT / "docs/EVIDENCE_MAINTAINABILITY.md").read_text(encoding="utf-8")

    checks = [
        check("metadata_current_release", meta.get("release") == EXPECTED_RELEASE and meta.get("base") == EXPECTED_BASE and meta.get("status") == EXPECTED_STATUS, {"release": meta.get("release"), "base": meta.get("base"), "status": meta.get("status")}),
        check("registry_current_release", reg.get("release") == EXPECTED_RELEASE and reg.get("base") == EXPECTED_BASE and reg.get("status") == EXPECTED_STATUS, reg),
        check("descriptive_only_no_authority", not reg.get("runtime_authority") and not reg.get("auto_repair") and not reg.get("auto_pruning") and not reg.get("policy_mutation"), {k: reg.get(k) for k in ["runtime_authority", "auto_repair", "auto_pruning", "policy_mutation"]}),
        check("maintenance_concerns_declared", len(reg.get("maintenance_concerns", [])) >= 5, {"count": len(reg.get("maintenance_concerns", []))}),
        check("surfaces_manifested", not [p for p in reg.get("required_surfaces", []) if p not in manifest_paths], {"missing": [p for p in reg.get("required_surfaces", []) if p not in manifest_paths]}),
        check("doc_states_non_authority", "no runtime authority" in doc and "no policy mutation" in doc and EXPECTED_RELEASE in doc and EXPECTED_BASE in doc, {}),
    ]
    failed = [c["name"] for c in checks if not c["ok"]]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
