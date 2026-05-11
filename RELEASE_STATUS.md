# GateGraph Release Status

Release: v0.14.9_STABLE
Base: v0.14.8_STABLE
Status: stable
Version: 0.14.9
Phase: Release artifact determinism and failure explainability
Release focus: Promotion / Surface / Registry Lock Hardening

Current stable release: v0.14.9_STABLE
Source candidate: v0.14.9_CANDIDATE
Candidate Windows Evidence CI: Passed: True

Stable release promoted after Windows Evidence CI for the Candidate reported `Passed: True`.

Promotion hardening invariants:
- Candidate/stable assertions are split by release status.
- `phase`, `release_focus`, and `status` are separate fields.
- Registry lock rebuild is required after promotion-affecting registry changes.
- Manifest hashes and paths must be refreshed after release-surface changes.
- Promotion pipeline status must come from release metadata SSOT.
Phase label: Install / Packaging / Public Repo Hygiene
Operational release focus: Install / Packaging / Public Repo Hygiene
Release claim surface: Release artifact determinism and failure explainability
Active phase authority: Release artifact determinism and failure explainability
