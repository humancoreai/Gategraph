"""GateGraph Operator Export / Evidence Bundle (v0.8.47).

Creates deterministic, read-only handoff bundles from existing evidence and
archive material. It does not execute or evaluate governance decisions.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from src.governance_drift_compare import assert_descriptive_drift_payload

try:
    from src.version import current_schema_version
except Exception:
    def current_schema_version() -> str:
        return "0.8.47"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "operator_exports"
DEFAULT_EVIDENCE_SOURCES = (
    PROJECT_ROOT / "tests" / "logs",
    PROJECT_ROOT / "operator_logs",
)
FORBIDDEN_EXPORT_FIELDS = {
    "severity", "risk_level", "requires_attention", "recommended_action",
    "recommendation", "priority", "score", "root_cause", "alarm", "alert",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_payload(payload: Any) -> str:
    return _sha256_bytes(_canonical(payload).encode("utf-8"))


def _safe_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _assert_export_payload(payload: Any) -> bool:
    """Export bundles remain descriptive and avoid prioritization language."""
    if not assert_descriptive_drift_payload(payload):
        return False
    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if str(key).lower() in FORBIDDEN_EXPORT_FIELDS:
                    return False
                if not walk(nested):
                    return False
        elif isinstance(value, list):
            for item in value:
                if not walk(item):
                    return False
        return True
    return walk(payload)


def collect_export_sources(sources: Iterable[Path | str] = DEFAULT_EVIDENCE_SOURCES, *, root: Path | str = PROJECT_ROOT) -> List[Dict[str, Any]]:
    """Return deterministic file observations for existing handoff material."""
    project_root = Path(root)
    observations: List[Dict[str, Any]] = []
    for source in sorted({Path(s) for s in sources}, key=lambda p: p.as_posix()):
        if not source.exists():
            continue
        candidates = [source] if source.is_file() else sorted(p for p in source.rglob("*") if p.is_file())
        for path in candidates:
            if path.name == ".gitkeep" or "__pycache__" in path.parts:
                continue
            data = path.read_bytes()
            observations.append({"relative_path": _safe_rel(path, project_root), "size_bytes": len(data), "sha256": _sha256_bytes(data)})
    observations = sorted(observations, key=lambda item: item["relative_path"])
    if not _assert_export_payload(observations):
        raise ValueError("non-descriptive export source observation detected")
    return observations


def build_operator_export_manifest(source_observations: Sequence[Mapping[str, Any]], *, export_id: str | None = None, timestamp: str | None = None) -> Dict[str, Any]:
    """Build a deterministic manifest over already-collected source files."""
    normalized = [dict(item) for item in sorted(source_observations, key=lambda item: str(item.get("relative_path", "")))]
    manifest = {
        "export_schema_version": current_schema_version(),
        "export_mode": "operator_evidence_handoff_bundle",
        "export_id": export_id or _sha256_payload({"sources": normalized}),
        "timestamp": timestamp or _utc_now(),
        "source_count": len(normalized),
        "sources": normalized,
    }
    manifest["manifest_hash"] = _sha256_payload({k: v for k, v in manifest.items() if k != "manifest_hash"})
    if not _assert_export_payload(manifest):
        raise ValueError("non-descriptive operator export manifest detected")
    return manifest


def create_operator_export_bundle(*, export_root: Path | str = DEFAULT_EXPORT_ROOT, sources: Iterable[Path | str] = DEFAULT_EVIDENCE_SOURCES, root: Path | str = PROJECT_ROOT, export_id: str | None = None, timestamp: str | None = None, copy_sources: bool = True) -> Dict[str, Any]:
    """Create a deterministic handoff directory with manifest and observed files.

    INV: This function only reads source files and writes to export_root. It does
    not call Governance, Enforcement, Runtime, Budget, Policy or Queue mutation.
    """
    project_root = Path(root)
    observations = collect_export_sources(sources, root=project_root)
    manifest = build_operator_export_manifest(observations, export_id=export_id, timestamp=timestamp)
    bundle_dir = Path(export_root) / manifest["export_id"]
    bundle_dir.mkdir(parents=True, exist_ok=True)
    if copy_sources:
        for item in observations:
            src = project_root / item["relative_path"]
            dst = bundle_dir / "sources" / item["relative_path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    result = {"bundle_path": str(bundle_dir), "manifest_path": str(manifest_path), "manifest": manifest}
    if not _assert_export_payload(result):
        raise ValueError("non-descriptive operator export bundle detected")
    return result


def verify_operator_export_manifest(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    """Describe manifest hash observations without assigning status semantics."""
    copy = dict(manifest)
    observed_hash = copy.pop("manifest_hash", None)
    computed_hash = _sha256_payload(copy)
    observation = {
        "export_id": manifest.get("export_id"),
        "source_count": manifest.get("source_count"),
        "manifest_hash_observed": observed_hash == computed_hash,
        "source_paths_observed": sorted(str(item.get("relative_path", "")) for item in manifest.get("sources", [])),
    }
    if not _assert_export_payload(observation):
        raise ValueError("non-descriptive operator export verification detected")
    return observation
