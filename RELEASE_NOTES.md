# Release Notes – v0.10.3_STABLE

## Summary

v0.10.3_STABLE finalizes the v0.10.x Runtime / Boundary Hardening line with a release-process guard.

The release adds automated checks to prevent pre-release/stable metadata drift, structured manifest regressions, stale manifest entries, and dead local documentation references.

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
