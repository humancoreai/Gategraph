from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.release_truth import load_release_truth, release_truth_surface_report


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    metadata = json.loads((ROOT / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "registry/release_truth_centralization.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest_paths = {entry["path"] for entry in manifest.get("files", []) if isinstance(entry, dict)}

    truth = load_release_truth(ROOT)
    report = release_truth_surface_report(ROOT, registry["checked_surfaces"])

    checks = []
    checks.append(check("metadata_current_stable", truth.release == "v0.16.3_STABLE" and truth.base == "v0.16.2_STABLE" and truth.status == "stable", {"release": truth.release, "base": truth.base, "status": truth.status}))
    checks.append(check("truth_matches_metadata", truth.release == metadata["release"] and truth.base == metadata["base"] and truth.version == metadata["version"], {"truth": truth.__dict__, "metadata_release": metadata["release"]}))
    checks.append(check("surface_report_ok", report["ok"], report))
    checks.append(check(
        "future_stable_derivation_matches_status",
        truth.future_stable == "v0.16.3_STABLE"
        and truth.status == "stable"
        and truth.future_stable == truth.release,
        {"future_stable": truth.future_stable, "release": truth.release, "status": truth.status}
    ))
    checks.append(check("registry_descriptive_only", registry.get("mode") == "descriptive_release_truth_centralization_only", {"mode": registry.get("mode")}))
    checks.append(check("no_runtime_or_repair_authority", registry.get("runtime_authority") is False and registry.get("auto_promotion") is False and registry.get("auto_repair") is False and registry.get("policy_mutation") is False, {"runtime_authority": registry.get("runtime_authority"), "auto_promotion": registry.get("auto_promotion"), "auto_repair": registry.get("auto_repair"), "policy_mutation": registry.get("policy_mutation")}))

    required = {
        "src/release_truth.py",
        "registry/release_truth_centralization.json",
        "docs/RELEASE_TRUTH_CENTRALIZATION.md",
        "tests/release_truth_centralization_evidence.py",
    }
    checks.append(check("truth_surfaces_manifested", required <= manifest_paths, {"missing": sorted(required - manifest_paths)}))

    failed = [name for name, ok, _ in checks if not ok]
    print("RELEASE TRUTH CENTRALIZATION EVIDENCE REPORT")
    print({"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
