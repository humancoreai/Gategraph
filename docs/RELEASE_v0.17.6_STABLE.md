Release: v0.17.7_CANDIDATE
Base: v0.17.5_STABLE
Status: candidate
Version: 0.17.6
Phase: Evidence Lifecycle Cleanup Formalization

# Release Notes – v0.17.7_CANDIDATE

v0.17.7_CANDIDATE formalizes evidence lifecycle cleanup and timeout normalization surfaces without changing governance, runtime authority, enforcement logic, policy behavior, or capability scope.

## Scope

- Evidence lifecycle cleanup is descriptive/test-harness focused.
- Timeout normalization records deterministic timeout/cleanup state markers.
- Registry lock rebaseline remains mandatory during promotion surfaces.
- No runtime authority, policy mutation, automatic repair, or auto-promotion is introduced.

Candidate note: stable promotion remains blocked until Windows Evidence CI `Passed: True`.
