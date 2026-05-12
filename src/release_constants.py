"""
WHY: Central release constants reduce duplicated release literals across evidence surfaces.
INV: Read-only metadata helper; never mutates runtime or governance state.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_release_constants(root: Path | None = None) -> dict:
    project_root = root or ROOT
    registry = json.loads(
        (project_root / "registry" / "release_constant_registry.json").read_text(encoding="utf-8")
    )
    return registry["constants"].copy()
