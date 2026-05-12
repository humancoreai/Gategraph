"""
WHY: v0.9.1 closes release integrity gaps left by cosmetic manifest checks.
INV: Release evidence verifies package determinism; it must not change governance logic.
SEC: Empty manifests, undeclared files, forbidden artifacts and non-reproducible ZIPs fail closed.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERSION = "v0.15.6_CANDIDATE"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"could not load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_local_artifacts(root: Path) -> None:
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    for cache in root.rglob(".pytest_cache"):
        shutil.rmtree(cache, ignore_errors=True)
    for artifact in root.glob("ARTIFACTS.sha256"):
        artifact.unlink(missing_ok=True)


def main() -> None:
    clean_local_artifacts(ROOT)
    build = load_module("build_release_evidence", ROOT / "tools" / "build_release.py")
    verify = load_module("verify_release_evidence", ROOT / "tools" / "verify_release.py")

    # WHY: Full Evidence CI starts from an unpacked source tree, not from a prebuilt dist ZIP.
    # Build the release package inside the evidence run, then verify that result deterministically.
    rc = build.main()
    assert rc == 0, "build_release did not complete successfully"

    zip_path = ROOT / "dist" / f"GateGraph_{VERSION}.zip"
    assert zip_path.exists(), f"release zip missing after build: {zip_path}"

    result_one = verify.verify(zip_path)
    result_two = verify.verify(zip_path)
    assert result_one == result_two, "verify_release is not repeatable"
    assert result_one["passed"], result_one["errors"]

    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["release"] == VERSION
    assert manifest["files"], "manifest is empty"
    assert manifest["file_count"] == len(manifest["files"])
    paths = [entry["path"] for entry in manifest["files"]]
    assert paths == sorted(paths), "manifest paths are not sorted"
    assert "TRUST_MODEL.md" in paths
    assert "tests/caller_boundary_evidence.py" in paths
    assert "tests/release_integrity_evidence.py" in paths
    assert "docs/FRESH_CLONE_REPRODUCIBILITY.md" in paths
    assert "tests/fresh_clone_reproducibility_evidence.py" in paths
    assert "tests/runtime_boundary_hardening_evidence.py" in paths
    assert "tests/freeze_runtime_invariant_evidence.py" in paths
    assert "tests/runtime_chain_order_evidence.py" in paths
    assert "tests/api_boundary_split_evidence.py" in paths
    assert "src/runtime_path_assertions.py" in paths
    assert "src/runtime_chain_assertions.py" in paths
    assert "src/api_boundary.py" in paths
    assert "docs/RUNTIME_BOUNDARY_HARDENING.md" in paths
    assert "docs/RUNTIME_CHAIN_ASSERTIONS.md" in paths
    assert "docs/GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md" in paths
    assert "tests/governance_freeze_evidence.py" in paths
    assert "SECURITY_MODEL.md" in paths
    assert "OWASP_AGENTIC_AI_MAPPING.md" in paths
    assert "KNOWN_LIMITATIONS.md" in paths
    assert "src/security/token_redaction.py" in paths
    assert "tests/token_exposure_evidence.py" in paths
    assert "docs/GOVERNANCE_SURFACE_FREEZE.md" in paths
    assert "contracts/governance_decision.schema.json" in paths
    assert "contracts/normalized_reason.schema.json" in paths
    assert "contracts/monitoring_export.schema.json" in paths
    assert "contracts/capability_token_claims.schema.json" in paths
    assert "tests/surface_contract_registry_evidence.py" in paths
    assert "tests/semantic_boundary_evidence.py" in paths
    assert "src/semantic_registry_lock.py" in paths
    assert "registry/semantic_registry_lock.json" in paths
    assert "registry/semantic_object_types.json" in paths
    assert "registry/invariant_surface_registry.json" in paths
    assert "tests/semantic_registry_lock_evidence.py" in paths
    assert "tests/release_manifest_coverage_evidence.py" in paths
    assert "docs/RELEASE_v0.15.6_CANDIDATE.md" in paths
    assert "src/recovery_foundation.py" in paths
    assert "tests/recovery_foundation_evidence.py" in paths
    assert "tests/replay_recovery_consistency_evidence.py" in paths
    assert "tests/surface_recovery_consistency_evidence.py" in paths
    assert "docs/RECOVERY_FOUNDATION.md" in paths
    assert "docs/RELEASE_v0.15.6_CANDIDATE.md" in paths

    with zipfile.ZipFile(zip_path, "r") as zf:
        rel_names = [name.removeprefix(f"GateGraph_{VERSION}/") for name in zf.namelist()]
    assert set(rel_names) - {"RELEASE_MANIFEST.json"} == set(paths), "zip/manifest declaration mismatch"

    files = build.iter_release_files()
    assert files, "build file set is empty"
    with tempfile.TemporaryDirectory() as tmp:
        zip_a = Path(tmp) / "a.zip"
        zip_b = Path(tmp) / "b.zip"
        build.write_zip(files, zip_a)
        build.write_zip(files, zip_b)
        assert sha256(zip_a) == sha256(zip_b), "ZIP writer is not deterministic"

    forbidden = ROOT / "gategraph.db"
    try:
        forbidden.write_text("forbidden", encoding="utf-8")
        reason = build.forbidden_reason(forbidden)
        assert reason is not None and "forbidden" in reason, "build_release did not classify .db as forbidden"
        try:
            build.assert_release_set(build.iter_release_files())
        except RuntimeError as exc:
            assert "gategraph.db" in str(exc)
        else:
            raise AssertionError("build_release accepted forbidden .db artifact")
    finally:
        forbidden.unlink(missing_ok=True)

    print("PASS release_integrity_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")


if __name__ == "__main__":
    main()
