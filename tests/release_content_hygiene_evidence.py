#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE = "v0.17.4_CANDIDATE"
EXPECTED_BASE = "v0.17.3_STABLE"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    paths = [entry["path"] for entry in manifest["files"]]

    readme = read("README.md")
    assert f"Current release: **{EXPECTED_RELEASE}**" in readme
    assert f"Base stable: **{EXPECTED_BASE}**" in readme
    assert "Current stable baseline: **v0.17.4_CANDIDATE**" not in readme
    assert "Base stable: **v0.11.4_STABLE**" not in readme

    assert "Canonical runtime namespace" in readme
    assert "`src/` package is the canonical runtime/governance surface" in readme
    assert "`gategraph/context/` package is a bounded context-governance extension layer" in readme
    assert "must not become an alternative governance or execution path" in readme

    assert "OWASP_AGENTIC_AI_MAPPING.md" in readme
    assert "OWASP_AGENTIC_AI_MAPPING.md" in paths

    dev_prompt_paths = [p for p in paths if Path(p).name.upper().startswith("STARTPROMPT")]
    assert not dev_prompt_paths, f"development prompt artifacts in release manifest: {dev_prompt_paths}"

    print(json.dumps({
        "release_content_hygiene": {
            "release": EXPECTED_RELEASE,
            "base": EXPECTED_BASE,
            "readme_base_consistent": True,
            "namespace_documented": True,
            "owasp_mapping_linked": True,
            "development_prompt_artifacts_absent": True,
            "manifest_files": len(paths),
        }
    }, indent=2, sort_keys=True))
    print("PASS release_content_hygiene_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
