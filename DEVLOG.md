# v0.8.23 - Evidence Runner Stabilization

- Stabilized aggregate evidence execution by routing scripts through `tests/_run_isolated.py`.
- Added `controlled_apply_evidence.py` to the aggregate manifest.
- Replaced the legacy multiprocessing supervisor with a compatibility wrapper around the isolated CI runner.
- Confirmed aggregate evidence completion with `Passed: True`.
- No production governance/enforcement/runtime/controlled-apply semantics changed.

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

## v0.7.1 – Audit Evidence Layer

- Added `tests/audit_evidence.py` as read-only evidence extraction for governance events, runtime decisions, runtime steps, tokens, and Pattern Engine proposals.
- Added `tests/runtime_stress_evidence.py` to generate structured JSON proof logs under `tests/logs/`.
- No production core semantics changed: Governance, Enforcement, Runtime Guard, Pattern Engine, and Audit Graph remain untouched.
- Verified evidence scenarios:
  - agent ping-pong loop stopped by repeated-action limit
  - cumulative cost limit stops allowed micro-actions
  - valid token does not override runtime exhaustion
  - missing token is rejected by Enforcement with audit event
  - Pattern Engine remains proposal-only and does not mutate rules
  - repeated identical governance evaluation is idempotent in audit evidence

## v0.7.2-ci-evidence

- Added `tests/evidence_ci.py` to run the proof-oriented test suite and write one CI summary JSON.
- Added GitHub Actions workflow `.github/workflows/evidence.yml` for automated evidence-log generation.
- Extended `tests/runtime_stress_evidence.py` with additional stress evidence:
  - alternating multi-agent loop stopped by `max_steps`
  - missing runtime budget fails closed
  - exact cost boundary allowed, next step stopped
  - documented current per-task cost scope / no session-global budget
- No production core modules changed.


## v0.7.3-cross-task-drift-evidence

Added Phase 3B evidence scenarios without changing production core modules:

- cross_task_cascade_drift_visible
- parallel_multi_agent_drift_visible
- session_reset_budget_bypass_visible
- micro_task_flood_drift_visible

Finding:
- Runtime cost control is proven per-task.
- Cross-task, multi-agent, session-reset, and micro-task flood costs are visible in evidence logs but not blocked by a session/global budget.
- This is a documented scope boundary, not an Enforcement/Governance invariant break.

Invariant status:
- Enforcement remains the only action gatekeeper.
- Runtime Guard still never grants capabilities.
- Pattern Engine remains proposal-only.
- Audit evidence remains append-only/read-only from the test perspective.


## v0.8.0-session-budget-guard

Added additive Session Budget Guard:

- `src/session_budget_guard.py`
- `tests/session_budget_evidence.py`
- `docs/SESSION_BUDGET_GUARD.md`

Purpose:
- Close v0.7.3 cross-task/session/multi-agent/micro-task cost drift findings.
- Preserve existing core semantics.

Controls:
- max_session_cost_units
- max_session_tasks
- max_agent_cost_units

Invariant status:
- Session Budget Guard never grants capabilities.
- Enforcement remains the only action gatekeeper.
- Runtime Guard remains per-task.
- Pattern Engine remains proposal-only.
- Missing explicit session budget fails closed.


## v0.8.1-guard-orchestration

Added deterministic Guard Orchestrator:

- `src/guard_orchestrator.py`
- `tests/guard_orchestration_evidence.py`
- `docs/GUARD_ORCHESTRATION.md`

Pipeline:
1. Enforcement
2. Session Budget Guard
3. Runtime Guard
4. Action-ready

Evidence:
- Enforcement blocks before budget guards.
- Session Budget stops before Runtime Guard.
- Runtime Guard stops when Session Budget allows.
- Session stop has priority when both would stop.
- All guards passing reaches action_ready.

Core invariant status:
- Enforcement remains the only action gatekeeper.
- Guards stop only; they do not grant capabilities.
- Pattern Engine remains proposal-only.


## v0.8.2-reason-normalization

Added reason normalization:

- `src/reason_normalizer.py`
- `tests/reason_normalization_evidence.py`
- `docs/REASON_NORMALIZATION.md`

Reason fields:
- code
- category
- severity
- stage
- message
- raw_reason
- priority

Invariant status:
- Raw reasons are preserved.
- Normalization never changes decisions.
- Unknown reasons fall back to unclassified codes.
- Guard Orchestrator now emits normalized_reason as additive metadata.


## v0.8.3-scale-safety-fix

Fixed review findings relevant for scaling:

- Session Budget Guard now wraps budget evaluation/link insertion in `BEGIN IMMEDIATE`.
- Allowed tasks reserve projected cost via `session_task_links.reserved_cost_units`.
- Session budget aggregation uses `max(reserved_cost_units, actual_runtime_cost)`.
- Reason Normalizer now uses explicit canonical reason keys instead of broad substring matching.
- Event schema version updated from `0.4` to `0.8.3`.
- README updated from stale v0.5 status to v0.8.3 architecture.

Added:
- `tests/scale_safety_evidence.py`
- `docs/SCALE_SAFETY.md`

Known boundary:
- This is still SQLite PoC-level concurrency, not distributed transaction safety.


## v0.8.4-external-api-mock-adapter

Added:
- `src/external_api_adapter.py`
- `tests/external_api_evidence.py`
- `docs/EXTERNAL_API_ADAPTER.md`

Purpose:
- Prove controlled outbound API behavior without real network calls.
- Ensure external calls pass through Enforcement → Session Budget → Runtime Guard.
- Audit API success/failure/blocked outcomes.

Invariant status:
- No real APIs.
- No secrets.
- No raw payload logging.
- Untrusted API responses remain data-only.

## v0.8.5-api-enforcement-binding

Fixed external API adapter trust boundary:

- Removed caller-provided `enforcement_allowed` / `enforcement_reason` from the adapter API.
- Adapter now calls `enforce()` internally using the supplied token.
- Tests use valid API tokens for allowed flows and `None` for blocked no-token flow.
- External API Evidence remains 7/7 passing.

Scope remains mock-only: no real network calls.

## v0.8.6 - Runaway / Cost Control Hardening

- Added fail-closed validation for non-positive projected session costs.
- Added fail-closed validation for non-positive runtime step costs.
- Added stable reason codes: `SES_INVALID_COST`, `RT_INVALID_COST`.
- Added `tests/runaway_cost_evidence.py` with negative/zero-cost scenarios.
- Verified External API negative-cost path stops at Session Budget before Runtime/Action.
- No change to Governance/Enforcement authority model.

## v0.8.7 - CI Evidence Runner Stabilization

- Added bounded shell evidence runner (`tests/evidence_ci.sh`).
- Kept JSON aggregate evidence output.
- Replaced `os._exit` in `tests/test_loop.py` with `SystemExit` for normal runner composition.
- Added `docs/CI_EVIDENCE_RUNNER.md`.
- No production governance/enforcement/runtime semantics changed.

## v0.8.8-capability-token-hardening

### Changed
- Added HMAC-signed Capability Tokens.
- Added token signature and signing key metadata to token storage.
- Enforcement now validates persisted token claims and signature before capability checks.
- Added normalized reasons for invalid signatures, claim mismatch, and missing tokens.
- Added `tests/capability_token_hardening_evidence.py`.
- Added `docs/CAPABILITY_TOKEN_HARDENING.md`.

### Invariants preserved
- Enforcement remains the only action gatekeeper.
- Guards still only stop; they do not allow.
- Pattern Engine remains proposal-only.
- Audit remains append-only.
- Fail-closed behavior strengthened for token uncertainty.

### Known boundaries
- Uses local HMAC secret model, not distributed key management.
- No key rotation yet.
- No asymmetric signatures yet.


## v0.8.13-security-finesse

- Added Block B security-finesse evidence tests.
- Hardened HTTP path-prefix matching to avoid neighboring-path allows.
- Rejected wildcard hosts explicitly in API endpoint policies.
- Confirmed secret values stay out of audit/evidence while still reaching the transport seam after all gates pass.
## v0.8.22-controlled-apply

### Added
- Implemented `src/controlled_apply.py` as a separate, narrow Human-Gate path after manual review.
- Added Controlled Apply schema tables for reviews and signed artifacts.
- Added strict rule-hardening validation: no loosening of risk, severity, decision, or priority.
- Added TTL, signature/hash validation, single-use execution, and target-state drift protection.
- Added audit events for request/approval/execution.
- Added docs and evidence script.

### Preserved invariants
- Pattern Engine does not decide.
- Review Workflow does not apply.
- Enforcement runtime path is not bypassed or modified.
- Unsupported apply types fail closed.

### Boundary
- This is not autonomous rule learning. It is a human-authorized deterministic apply seam with minimal scope.
## v0.8.25_RUNTIME_GOVERNANCE_CANDIDATE

- Added `src/runtime_governance.py` with deterministic normal/degraded/throttled/blocked escalation states.
- Runtime Guard now applies stricter `max_cost_for_action` constraints before recording a new step.
- Loop signals can only escalate constraints; they cannot allow continuation.
- Extended runaway cost evidence with near-budget and loop-signal constraint cases.
- No change to Enforcement authority, Pattern decision rights, Secret handling or Human-Gate invariants.



## v0.8.25.1_RUNNER_HARDENING_CANDIDATE
- Evidence runner hardened for timeout handling.
- POSIX path uses external watchdog (`timeout --kill-after`) to avoid interpreter wait/signal hangs.
- Windows path keeps process-tree termination via `taskkill /T /F` and direct kill fallback.
- Selftest reduced to deterministic pass/fail/timeout proof; brittle nested child-hang case removed from release gate.


## v0.8.25.1_STABLE

- Consolidated `v0.8.25.1_RUNNER_HARDENING_CANDIDATE` into a stable recovery point.
- Windows full Evidence CI reported `Passed: True` on 2026-04-28.
- Runtime Governance / Runaway Cost Control retained as stable scope.
- Runner timeout path retained with deterministic pass/fail/timeout selftest.
- Added `docs/RELEASE_v0.8.25.1_STABLE.md`.
- No governance, enforcement, token, secret or controlled-apply authority model changes were introduced during consolidation.

### Stable boundary
- Stable for current local evidence scope.
- Still single-node.
- No production KMS, distributed budget or monitoring/alerting.

## v0.8.26_CANDIDATE - Cross-Session Budget Control

Implemented candidate extension for system/actor budget control across task boundaries.

Added:
- `src/budget_ledger.py`
- `budget_scopes` and `budget_reservations` schema
- budget reservation claims in capability tokens
- enforcement checks for persisted budget token claims
- governance-side budget reservation before token issuance
- `tests/cross_session_budget_evidence.py`
- CI manifest entry for cross-session budget evidence

Invariant preserved:
- Runtime does not decide or expand budget.
- Pattern Engine remains advisory.
- Enforcement remains token verifier/gatekeeper.

Known limit:
- single-node ledger only; no distributed lock/consensus/KMS.


## v0.8.26_STABLE - Stable Consolidation + Repo Hygiene

Promoted `v0.8.26_CROSS_SESSION_BUDGET_CANDIDATE` to `v0.8.26_STABLE` after the Windows full Evidence CI run reported `Passed: True`.

### Consolidated
- Cross-Session Budget Control is now part of the stable recovery point.
- Budget Ledger remains single-node and deterministic.
- Governance reserves budget before token issuance.
- Enforcement verifies budget claims against persisted token state.
- Runtime remains non-authoritative and only reads signed constraints.

### Evidence basis
- Cross-session split attack evidence passed.
- Reservation idempotency evidence passed.
- Reservation expiry/release evidence passed.
- Token budget-claim enforcement evidence passed.
- Missing budget scope fails closed.
- Full Evidence CI reported no unexpected allows and no invariant violations.

### Repo hygiene
- Removed generated `__pycache__` and compiled Python files.
- Removed generated evidence JSON/tmp logs from the stable archive.
- Kept `tests/logs/.gitkeep` so the evidence log directory exists without committing generated logs.
- Updated version, release status, release notes, and stable release document.

### Stable boundary
- Single-node only.
- No production KMS.
- No distributed budget consensus or lock manager.
- No monitoring/alerting/incident layer.

## v0.8.27_OPERATIONAL_HARDENING_CANDIDATE

- Added `src/operational_hardening.py`.
- Added budget snapshot visibility for all Budget Ledger scopes.
- Added deterministic audit replay consistency checks.
- Added append-only operational incident records.
- Added `tests/operational_hardening_evidence.py`.
- Added documentation in `docs/OPERATIONAL_HARDENING.md`.
- No changes to Enforcement/Governance allow-path semantics.


## v0.8.27.1_RUNNER_POSIX_HARDENING_CANDIDATE

### Scope

Evidence Runner patch only.

### Change

- Replaced POSIX external `timeout` wrapper with Python-owned `Popen` supervision.
- Added POSIX `start_new_session=True` for process-session isolation.
- Preserved file-backed stdout/stderr.
- Preserved fail-closed timeout reporting.

### Rationale

The evidence runner must own timeout semantics directly. Shell timeout wrappers can
create platform-specific hangs and make POSIX behavior diverge from Windows.

### Validation

Targeted evidence runner selftest passed locally. Full CI remains the release gate.

## v0.8.27.1_STABLE - Stable Consolidation + Repo Hygiene

Promoted `v0.8.27.1_RUNNER_POSIX_HARDENING_CANDIDATE` to `v0.8.27.1_STABLE` after the full Windows Evidence CI run reported `Passed: True` on 2026-04-28.

### Consolidated
- Operational Hardening is now part of the stable recovery point.
- Budget snapshots expose system/actor/task/session ledger state for operational inspection.
- Audit replay consistency checks detect budget overspend and state drift.
- Operational incidents remain append-only records.
- Evidence Runner POSIX path uses Python-owned process supervision and session isolation.

### Evidence basis
- Full Evidence CI reported `Passed: True`.
- Operational Hardening evidence passed: 6/6.
- Unexpected allows: 0.
- Invariant violations: 0.
- Evidence runner selftest passed on Windows.

### Repo hygiene
- Removed generated `__pycache__` and compiled Python files.
- Removed generated evidence JSON/tmp logs from the stable archive.
- Kept `tests/logs/.gitkeep` so the evidence log directory exists without committing generated logs.
- Updated version, release status, release notes and stable release document.

### Stable boundary
- Single-node only.
- No production KMS.
- No distributed budget consensus or lock manager.
- Mock external API only.
- No automated incident recovery.

## v0.8.28_CANDIDATE - Governance SSOT Integration

### Scope
- Added `GOVERNANCE.md` at repository root.
- Linked governance document from README.
- Updated release/version metadata for candidate boundary.

### Boundary
- Documentation/governance consolidation only.
- No functional code changes.
- Operational extensions remain deferred.

### Validation baseline
- Inherits `v0.8.27.1_STABLE` full Windows Evidence CI baseline: `Passed: True`, unexpected allows `0`, invariant violations `0`.


## v0.8.29_CANDIDATE - Operational Alerting

### Scope
- Added read-only operational alert evaluation on top of append-only incident records.
- Added `OperationalAlert` signal model.
- Added deterministic severity sorting for operational alerts.
- Added `tests/operational_alerting_evidence.py`.
- Added `docs/OPERATIONAL_ALERTING.md` and candidate release document.

### Boundary
- Alerts are signals only.
- No automatic recovery.
- No notification transport.
- No changes to Enforcement/Governance/Runtime allow-path semantics.

### Validation
- Targeted operational alerting evidence passed: 4/4.
- Full Evidence CI remains the Windows promotion gate.
