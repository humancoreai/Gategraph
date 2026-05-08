# Known Gaps / Roadmap

This document tracks open gaps from the v0.8.40 system review and distributes them across controlled future phases.

## v0.8.42 — Operator Workflows / Playbooks

Goal:
- Manual operator workflows after patterns are visible.

Closes / reduces:
- standard responses without automation
- playbook structure
- no auto-fix, no policy tuning

## v0.8.43 — Human Review Queue

Goal:
- Close `require_review` / `require_approval` phantom workflow gap.

Closes:
- review queue
- reviewer assignment
- review status lifecycle
- audit trail for review decisions
- explicit distinct reviewer enforcement verification

## v0.8.44 — Security Boundary Hardening

Goal:
- Harden boundary trust and signing assumptions.

Closes:
- Caller-Trust-Gap
- strict boundary schema for `input_source`, `secrets_involved`, `data_sensitivity`
- fail-closed on missing/invalid boundary flags
- remove `_DEV_KEYRING` silent fallback
- token/signing threat model in `SECURITY.md`

## v0.8.45 — Concurrency / Idempotency Evidence

Goal:
- Test and document realistic parallel behavior.

Closes:
- SQLite concurrency evidence
- simultaneous `idempotency_key` submission
- lock/timeout behavior
- explicit single-node limitations under parallel load

## v0.8.46 — Proposal Lifecycle / Flood Protection

Goal:
- Prevent unbounded proposal growth.

Closes:
- proposal expiry
- proposal archive/cleanup
- proposal flood protection
- lifecycle documentation

## v0.8.47 — Integration Boundary

Goal:
- Make local integration safer and clearer.

Closes:
- Explain API contract stability
- local auth/reverse-proxy operating model documentation
- minimal integration adapter example

## Non-goal

These gaps must not be closed opportunistically inside unrelated phases.
GateGraph remains gate-based: stabilize before extending.
