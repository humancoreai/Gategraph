# GateGraph v0.17.7_STABLE Release Notes

Release: v0.17.7_STABLE  
Status: stable  
Base: v0.14.7_STABLE  
Version: 0.14.8
Phase: Install / Packaging / Public Repo Hygiene

## Scope

v0.17.7_STABLE hardens release/evidence determinism without changing governance, runtime authority, enforcement logic, or policy behavior.

## Candidate Focus

- Release surface symmetry evidence.
- Evidence runner robustness evidence.
- Manifest and artifact hygiene checks.
- Fresh-clone and public-surface consistency checks.
- Failure classification remains descriptive only.

## Non-Scope

- No autonomous policy mutation.
- No runtime authority expansion.
- No adaptive governance.
- No new agent orchestration.
- No enforcement logic change.

## Gate Rule

Candidate-to-stable promotion requires Windows Evidence CI PASS and manual promotion. Stable promotion without a prior candidate PASS is forbidden.
