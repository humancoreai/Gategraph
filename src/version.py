"""
WHY: Version values are part of public schemas and must not drift across files.
INV: VERSION.md remains the human-readable SSOT; code derives the candidate version from it.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_FALLBACK_SCHEMA_VERSION = "0.8.46"


@lru_cache(maxsize=1)
def current_schema_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION.md"
    try:
        text = version_file.read_text(encoding="utf-8")
    except OSError:
        return _FALLBACK_SCHEMA_VERSION
    match = re.search(r"Current (?:candidate|stable):\s*v?(\d+\.\d+\.\d+)", text)
    return match.group(1) if match else _FALLBACK_SCHEMA_VERSION
