# Evidence Failure Classification

Status: descriptive only.
Release: v0.13.4_CANDIDATE.
Base: v0.13.3_STABLE.

This surface groups evidence failures into review buckets such as release-surface, semantic-boundary, registry-lock, server-surface, runtime-governance, and security.

It does not repair failures, skip tests, downgrade failures, promote releases, or change governance/runtime behavior.

## Invariants

- Classification is visibility only.
- Unknown evidence names are treated as unclassified and must not pass silently in release evidence.
- Mandatory Stable gates remain mandatory.
- The registry has no runtime authority.
