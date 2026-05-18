# Install / Packaging / Public Repo Hygiene

Release: v0.17.7_STABLE.
Base: v0.14.7_STABLE.
Status: stable.

## Scope

This surface makes release-gate expectations explicit and executable. It is evidence-only hardening for Candidate/Stable release hygiene.

## Guarantees checked

- Candidate surfaces must declare `candidate`, not `stable`.
- Stable promotion remains manual and CI-gated.
- Release/manifest/status/base claims must be synchronized.
- The check does not repair files, promote releases, prune tests, or alter runtime governance.

## Non-scope

- No governance logic change.
- No runtime behavior change.
- No automatic repair.
- No automatic Stable promotion.
