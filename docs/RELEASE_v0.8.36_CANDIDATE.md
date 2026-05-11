# GateGraph v0.8.36_CANDIDATE

## Phase
API Robustness / Real-World Stability

## Scope Check

API contract remains unchanged:

- no new response fields
- no schema-shape change
- no governance-core change
- no smart recovery
- no auth/rate limiting/multi-node scope expansion

## Changes

- Added adapter-level evaluate serialization for the local single-node SQLite server path.
- Added bounded socket timeout for malformed/truncated HTTP reads.
- Added defensive handling for client aborts and broken response writes.
- Added deterministic oversized-payload rejection without parsing.
- Added `tests/api_robustness_evidence.py`.
- Added robustness evidence to `tests/evidence_ci.py` manifest.
- Updated version metadata to `v0.8.36_CANDIDATE`.

## Evidence

Verified in this environment:

- `api_contract_evidence` passed
- `api_robustness_evidence` passed
- `repo_push_hygiene_evidence` passed
- `server_hardening_evidence` produced PASS output, but the local shell command did not return cleanly afterward in this container session; treat full aggregate CI as unverified here and rerun on Windows.

## Blockers

None found in the patched API contract path.

## Unverified

- Full aggregate `tests/evidence_ci.py` run in this container. It timed out during local execution before a complete report was produced.
- Windows Full Evidence CI still required before stable promotion.

## Implementierungsfallen

- Parallel `/evaluate` requests against one SQLite file can cause write contention. The fix intentionally serializes only the adapter call, not governance logic.
- Client abort handling must not be interpreted as a governance event.
- Oversized payload rejection must stay schema-compatible and must not add diagnostic fields.
