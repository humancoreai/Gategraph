# GateGraph v0.12.4_STABLE

Base: v0.12.3_STABLE  
Status: stable  
Phase: Semantic Registry Lock & Coverage Freeze

## Scope

v0.12.4 freezes the semantic registry consolidation from v0.12.3 with deterministic registry-lock evidence.

The release adds a descriptive lock file for semantic registry surfaces and validates it through evidence. The lock is not runtime authority and does not repair, rewrite, load, score or promote semantic objects.

## Added surfaces

- `registry/semantic_registry_lock.json`
- `src/semantic_registry_lock.py`
- `tests/semantic_registry_lock_evidence.py`
- `tests/release_manifest_coverage_evidence.py`

## Invariants

- Semantic registry locks are descriptive release evidence only.
- Registry lock membership does not create authority.
- Registry hash mismatch is detected as evidence failure.
- Dynamic loading and auto-repair remain forbidden.
- Release manifest coverage must declare the registry lock surface.

## Non-scope

- No governance logic change.
- No enforcement behavior change.
- No runtime authority expansion.
- No new adapter.
- No autonomous semantic drift correction.
