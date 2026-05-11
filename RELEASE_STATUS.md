# GateGraph Release Status

Release: v0.14.9_CANDIDATE
Base: v0.14.8_STABLE
Status: candidate
Version: 0.14.9
Phase: Release artifact determinism and failure explainability
Release focus: Promotion / Surface / Registry Lock Hardening
Operational release focus: Install / Packaging / Public Repo Hygiene

Current candidate release: v0.14.9_CANDIDATE

Stable promotion is forbidden until Windows Evidence CI for this Candidate reports `Passed: True`.

Promotion hardening invariants:
- Candidate/stable assertions are split by release status.
- `phase`, `release_focus`, and `status` are separate fields.
- Registry lock rebuild is required after promotion-affecting registry changes.
- Manifest hashes and paths must be refreshed after release-surface changes.
- Promotion pipeline status must come from release metadata SSOT.
