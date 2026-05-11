# GateGraph Release Status

Release: v0.14.10_CANDIDATE
Base: v0.14.9_STABLE
Status: candidate
Version: 0.14.10
Phase: Public surface cleanup and review readiness
Phase label: Public surface cleanup and review readiness
Legacy phase reference: Release artifact determinism and failure explainability
Release focus: Public Surface / Review Readiness / Release Hygiene
Operational release focus: Public Surface / Review Readiness / Release Hygiene
Historical packaging focus: Install / Packaging / Public Repo Hygiene

Current candidate release: v0.14.10_CANDIDATE

Stable promotion is forbidden until Windows Evidence CI for this Candidate reports `Passed: True`.

Public-surface cleanup invariants:
- README is a public product/review surface, not an evidence archive.
- Scope backlog separates deferred items from current capability.
- Release metadata, manifest, status, version, README and release doc must agree.
- Build tooling must preserve release metadata fields.
- No runtime authority, auto-promotion, auto-repair or policy mutation is added.
