#!/usr/bin/env python3
"""INV: Semantic boundary preparation remains observability-only and proposal-only."""
from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['uncertainty_marker','unverifiable_state','interpretation_boundary_placeholder','proposal_only_semantic_signal']
FORBIDDEN_AUTHORITY = ['automatic policy update','runtime decision change','enforcement decision change','LLM-based governance decision']

def main() -> int:
    text = (ROOT / 'docs' / 'SEMANTIC_BOUNDARY_PREPARATION.md').read_text(encoding='utf-8')
    for marker in REQUIRED:
        assert marker in text
    assert 'no enforcement authority' in text
    assert 'no runtime authority' in text
    assert 'no policy mutation authority' in text
    for forbidden in FORBIDDEN_AUTHORITY:
        assert forbidden in text
    meta = (ROOT / 'RELEASE_METADATA.json').read_text(encoding='utf-8')
    assert '"semantic_context_scoring": false' in meta
    print({'semantic_boundary_preparation': {'markers': REQUIRED, 'authority': 'observability_only', 'enforcement_effect': False}})
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0
if __name__ == '__main__': raise SystemExit(main())
