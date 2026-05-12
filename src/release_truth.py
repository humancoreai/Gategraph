"""
WHY: Release/evidence checks should derive their expectations from one metadata source instead of duplicating literals.
INV: This module is read-only release evidence plumbing; it never mutates runtime, policy, governance, or manifests.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ReleaseTruth:
    release: str
    base: str
    status: str
    version: str
    phase: str
    release_focus: str

    @property
    def future_stable(self) -> str:
        if self.release.endswith("_CANDIDATE"):
            return self.release.replace("_CANDIDATE", "_STABLE")
        return self.release


def load_release_truth(root: Path | None = None) -> ReleaseTruth:
    project_root = root or PROJECT_ROOT
    metadata = json.loads((project_root / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    required = ["release", "base", "status", "version", "phase", "release_focus"]
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValueError(f"missing release truth fields: {missing}")

    return ReleaseTruth(
        release=str(metadata["release"]),
        base=str(metadata["base"]),
        status=str(metadata["status"]),
        version=str(metadata["version"]),
        phase=str(metadata["phase"]),
        release_focus=str(metadata["release_focus"]),
    )


def release_truth_surface_report(root: Path | None = None, surfaces: list[str] | None = None) -> dict:
    project_root = root or PROJECT_ROOT
    truth = load_release_truth(project_root)
    checked = surfaces or [
        "README.md",
        "VERSION.md",
        "RELEASE_STATUS.md",
        "RELEASE_NOTES.md",
        "CHANGELOG.md",
        "RELEASE_METADATA.json",
        "RELEASE_MANIFEST.json",
    ]

    missing_release: list[str] = []
    missing_base: list[str] = []
    accidental_future_stable_current: list[str] = []

    for rel in checked:
        path = project_root / rel
        if not path.exists():
            missing_release.append(rel)
            missing_base.append(rel)
            continue

        text = path.read_text(encoding="utf-8")
        if truth.release not in text:
            missing_release.append(rel)
        if rel != "RELEASE_MANIFEST.json" and truth.base not in text:
            missing_base.append(rel)
        # EDGE: Current candidate evidence uses the stable token as the declared base; do not classify base mentions as current-stable claims.
        if rel in {"README.md", "VERSION.md", "RELEASE_STATUS.md", "RELEASE_NOTES.md"} and truth.future_stable != truth.base and truth.future_stable in text:
            accidental_future_stable_current.append(rel)

    return {
        "release": truth.release,
        "base": truth.base,
        "status": truth.status,
        "version": truth.version,
        "phase": truth.phase,
        "release_focus": truth.release_focus,
        "future_stable": truth.future_stable,
        "checked_surfaces": checked,
        "missing_release": missing_release,
        "missing_base": missing_base,
        "accidental_future_stable_current": accidental_future_stable_current,
        "ok": not missing_release and not missing_base and not accidental_future_stable_current,
        "mode": "read_only_release_truth_resolution",
        "runtime_authority": False,
        "auto_repair": False,
        "auto_promotion": False,
    }
