# DEVLOG

## v0.4.2

Fixes after 20-run comparative validation:

- added revoked-token DB check in `enforcement.py`
- fixed critical-risk behavior via `RULE-005`
- fixed `data_sensitivity=secret` priority in `risk_engine.py`
- preserved task-binding enforcement
- extended validation to 20 scenarios in isolated and accumulated modes

Validation result:

```text
Passed: isolated 20/20 | accumulated 20/20
Failed: 0
Unexpected allows: 0
Invariant violations: 0
DB events accumulated: 31
```

## v0.4.1

- added task-binding check in enforcement
- added cross-task token reuse validation

## v0.4.0

- initial PoC implementation based on GateGraph v0.4 spec

## v0.4.3 — Usage simulation semantic fixes

- Risk Engine: `api_call` with `input_source="external"` now classifies as `medium`.
- Risk Engine: `data_sensitivity="secret"` is evaluated before write/delete and always classifies as `critical`.
- Governance: `require_review` now issues an analysis-only token when requested capability is `read_files`.
- `require_review` still denies side-effect capabilities (`write_files`, `delete_files`, `api_call`).
- No architecture changes; only semantic alignment with v0.4 intent.

## v0.4.4 — Risk Engine deterministic rewrite

- Rewrote `src/risk_engine.py` explicitly instead of patching conditionally.
- Confirmed `api_call` + `input_source="external"` classifies as `medium`.
- Preserved prior fixes: `secret` sensitivity is `critical`; `require_review` remains analysis-only.

## v0.4.5 — Enum validation for unusual inputs

- Risk Engine now validates `input_source` and `data_sensitivity` against explicit allowed sets.
- Unknown enum values classify as `medium` instead of silently falling through to `low`.
- Unusual input simulation confirms zero unsafe allows and zero invariant violations.

## v0.4.6 — require_review analysis-only token fix

- Governance now issues a token for `require_review` only when the permitted capability is `read_files`.
- Side-effect capabilities remain denied under `require_review`.
- Agent scenarios validate that untrusted read analysis is allowed while write/delete/api actions remain blocked.

## v0.5 — PoC consolidation

- Consolidated GateGraph naming and repository documentation.
- Added README, ARCHITECTURE, SECURITY, TEST_REPORT, and VERSION files.
- Documented GLP as inspiration only, not as implemented protocol.
- Froze v0.4.6 core as v0.5 PoC-ready baseline.
- No runtime feature expansion in this step.

## v0.6-spec — Runtime Guard design

- Added `docs/RUNTIME_GUARD.md`.
- Defined runtime/cost-control layer as separate from GateGraph Core.
- Added RuntimeBudget, RuntimeStep, RuntimeDecision, RuntimeEvent concepts.
- Defined initial limits: max steps, max runtime, max cost units, repeated action limit.
- No implementation changes to Core in this step.

## v0.6-core — Runtime Guard MVP

- Added Runtime Guard schema tables.
- Added `src/runtime_guard.py`.
- Added runtime budget creation and pre-step evaluation.
- Implemented max steps, max runtime, max cost units, and repeated-action stop checks.
- Added runtime guard tests A–F.
- Runtime stop occurs before Governance evaluation.

## v0.7 — Pattern Engine MVP

- Added `src/pattern_engine.py`.
- Added `proposals` table schema/helper.
- Added `tests/pattern_engine_tests.py`.
- Added `docs/PATTERN_ENGINE.md`.
- Pattern Engine creates `pending_review` proposals only.
- Verified active rules are not mutated by Pattern Engine.
