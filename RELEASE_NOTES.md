# Release Notes – v0.10.3_CANDIDATE

## Summary

v0.10.3_CANDIDATE is a release-process hardening phase based on the Windows-CI-confirmed v0.10.2_STABLE baseline.

It adds an explicit release-process guard to prevent Candidate/Stable metadata drift, manifest-shape regressions, stale manifest entries, and missing local documentation references.

## Added

- `tools/release_process_guard.py`
- `tests/release_process_guard_evidence.py`

## Guard coverage

- release metadata truth
- expected release/status consistency
- expected base consistency
- structured manifest validation
- manifest hash/size consistency
- stale/missing manifest entries
- local markdown dead-reference checks

## Unchanged

- governance logic
- enforcement logic
- runtime logic
- adapter behavior
- agent behavior
- packaging/deployment scope
- UI scope
