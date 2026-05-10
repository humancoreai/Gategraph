"""
WHY: Release packaging must be deterministic and externally verifiable.
INV: This tool packages source/review artifacts only; it does not alter governance behavior.
SEC: Hidden files, runtime databases, caches and generated local artifacts are rejected fail-closed.
"""
from __future__ import annotations

import hashlib
import json
import stat
import sys
import zipfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.11.4_STABLE"
BASE = "v0.11.3_STABLE"
DIST = ROOT / "dist"
ZIP_NAME = f"GateGraph_{VERSION}.zip"
ZIP_PATH = DIST / ZIP_NAME
FIXED_ZIP_DT = (2026, 1, 1, 0, 0, 0)

EXCLUDED_DIRS = {".git", "dist", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
FORBIDDEN_DIRS = {".idea", ".vscode"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".db", ".csv", ".zip", ".tmp", ".temp", ".log"}
EXCLUDED_NAMES = {"ARTIFACTS.sha256"}
FORBIDDEN_NAMES = {
    "gategraph.db",
    "gategraph.db-journal",
    "gategraph.db-wal",
    "gategraph.db-shm",
    ".DS_Store",
    "Thumbs.db",
}
REQUIRED_RELEASE_FILES = {
    "VERSION.md",
    "RELEASE_METADATA.json",
    "RELEASE_MANIFEST.json",
    "TRUST_MODEL.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/KNOWN_GAPS_ROADMAP.md",
    "RELEASE_PROCESS.md",
    "tests/install_surface_evidence.py",
    "tests/packaging_integrity_evidence.py",
    "docs/DEPLOYMENT_BOUNDARY.md",
    "tests/config_consistency_evidence.py",
    "tests/startup_surface_evidence.py",
    "docs/STARTUP_SURFACE.md",
    "docs/RUNTIME_SURFACE_FREEZE.md",
    "docs/MODE_BOUNDARY_SURFACE.md",
    "tests/mode_boundary_surface_evidence.py",
    "docs/OPERATIONAL_BOUNDARY_TIGHTENING.md",
    "tests/startup_shutdown_semantics_evidence.py",
    "tests/runtime_surface_consistency_evidence.py",
    "tests/surface_freeze_coupling_evidence.py",
    "pyproject.toml",
    "docs/THREAT_MODEL.md",
    "README.md",
    "PRODUCTION.md",
    "LICENSE",
    "tools/build_release.py",
    "tools/verify_release.py",
    "tools/release_process_guard.py",
    "tests/caller_boundary_evidence.py",
    "tests/release_integrity_evidence.py",
    "tests/release_process_guard_evidence.py",
    "tests/runtime_boundary_hardening_evidence.py",
    "tests/freeze_runtime_invariant_evidence.py",
    "tests/api_boundary_split_evidence.py",
    "tests/runtime_chain_order_evidence.py",
    "tests/multi_agent_architecture_evidence.py",
    "docs/MULTI_AGENT_SSOT.md",
    "docs/MULTI_MODE_SSOT.md",
    "docs/DELEGATION_BOUNDARY.md",
    "docs/MULTI_AGENT_BUDGET_AUTHORITY.md",
    "docs/MULTI_AGENT_REPLAY_AUDIT.md",
    "docs/EMERGENCE_BOUNDARIES.md",
    "docs/GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md",
    "docs/INVARIANT_REGISTRY.md",
    "docs/BOUNDARY_REFERENCES.md",
    "docs/RELEASE_REPRODUCIBILITY.md",
    "docs/RUNTIME_BOUNDARY_HARDENING.md",
    "docs/RUNTIME_CHAIN_ASSERTIONS.md",
    "src/runtime_path_assertions.py",
    "src/runtime_chain_assertions.py",
    "src/api_boundary.py",
    "tests/governance_freeze_evidence.py",
    "docs/CAPABILITY_TOKEN_AUDIT_REDACTION.md",
    "tests/capability_token_redaction_evidence.py",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def forbidden_reason(path: Path) -> str | None:
    r = rel(path)
    parts = Path(r).parts
    if set(parts) & FORBIDDEN_DIRS:
        return "forbidden directory"
    if path.name in EXCLUDED_NAMES:
        return None
    if path.name in FORBIDDEN_NAMES:
        return "forbidden generated/local file"
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return "forbidden suffix"
    if is_hidden_part(Path(r)) and r != ".gitignore":
        return "hidden file"
    if r.startswith("tests/logs/") and path.name != ".gitkeep":
        return "test log artifact"
    return None


def is_excluded_path(path: Path) -> bool:
    r = rel(path)
    parts = Path(r).parts
    if set(parts) & EXCLUDED_DIRS:
        return True
    # WHY: Evidence CI writes transient logs while release_integrity_evidence is running.
    # They are never release inputs; ZIP verification still fails if they appear in a package.
    if r.startswith("tests/logs/"):
        return True
    return False


def should_include(path: Path) -> bool:
    if not path.is_file():
        return False
    if is_excluded_path(path):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    return forbidden_reason(path) is None


def scan_forbidden_files() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix()):
        if not path.is_file():
            continue
        if is_excluded_path(path):
            continue
        reason = forbidden_reason(path)
        if reason is not None:
            errors.append(f"{reason}: {rel(path)}")
    return errors


def iter_release_files() -> list[Path]:
    return sorted((p for p in ROOT.rglob("*") if should_include(p)), key=lambda p: rel(p))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(files: Iterable[Path]) -> dict:
    entries = [{"path": rel(p), "size": p.stat().st_size, "sha256": sha256_file(p)} for p in files]
    if not entries:
        raise RuntimeError("release manifest would be empty")
    return {
        "release": VERSION,
        "status": "stable",
        "base": BASE,
        "kind": "candidate_release",
        "scope": "capability_token_audit_redaction",
        "deterministic_packaging": True,
        "file_count": len(entries),
        "files": entries,
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_release_set(files: list[Path]) -> None:
    errors = scan_forbidden_files()
    paths = {rel(p) for p in files}
    missing = sorted(REQUIRED_RELEASE_FILES - paths)
    if missing:
        errors.append(f"missing required release files: {missing}")
    if not files:
        errors.append("release file set is empty")
    if errors:
        raise RuntimeError("release build refused: " + "; ".join(errors))


def write_zip(files: list[Path], zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            r = rel(path)
            info = zipfile.ZipInfo(filename=f"GateGraph_{VERSION}/{r}", date_time=FIXED_ZIP_DT)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            zf.writestr(info, path.read_bytes())


def main() -> int:
    DIST.mkdir(exist_ok=True)
    metadata = {
        "release": VERSION,
        "status": "stable",
        "base": BASE,
        "phase": "Capability Token Audit Redaction",
        "governance_logic_changed": False,
        "runtime_logic_changed": False,
        "enforcement_logic_changed": False,
        "new_governance_features": False,
        "new_runtime_capability": False,
        "new_runtime_model": False,
        "new_risk_model": False,
        "new_agentic_behavior": False,
        "new_adapter": False,
        "packaging_scope": True,
        "deployment_scope": "single_node_local_protected",
        "startup_surface_scope": True,
        "config_consistency_scope": True,
        "runtime_surface_scope": True,
        "surface_freeze_coupling_scope": True,
        "mode_boundary_surface_scope": True,
        "capability_token_audit_redaction_scope": True,
        "startup_shutdown_semantics_scope": True,
        "release_process_guard": True,
        "distributed_governance": False,
        "self_orchestration": False,
        "scope_freeze": True,
        "claim_boundary": "capability-token audit redaction only; audit may record token_id and token_hash but never raw token objects, signatures, signing input, Authorization headers, secret material, or bearer values",
    }
    write_json(ROOT / "RELEASE_METADATA.json", metadata)

    files_without_manifest = [p for p in iter_release_files() if rel(p) != "RELEASE_MANIFEST.json"]
    assert_release_set(files_without_manifest + [ROOT / "RELEASE_MANIFEST.json"])
    manifest = build_manifest(files_without_manifest)
    write_json(ROOT / "RELEASE_MANIFEST.json", manifest)

    files = iter_release_files()
    assert_release_set(files)
    source_hashes = [f"{sha256_file(p)}  {rel(p)}" for p in files]
    (ROOT / "ARTIFACTS.sha256").write_text("\n".join(source_hashes) + "\n", encoding="utf-8")

    files = iter_release_files()
    write_zip(files, ZIP_PATH)
    zip_sha = sha256_file(ZIP_PATH)
    (DIST / f"{ZIP_NAME}.sha256").write_text(f"{zip_sha}  {ZIP_NAME}\n", encoding="utf-8")
    print(json.dumps({"zip": str(ZIP_PATH), "sha256": zip_sha, "file_count": len(files)}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
