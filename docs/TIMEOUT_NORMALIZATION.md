# Timeout Normalization – v0.17.8_STABLE

Release: v0.17.8_STABLE  
Base: v0.17.7_STABLE  
Status: stable  
Phase: Evidence Lifecycle Cleanup Formalization

Timeout handling is normalized as CI/evidence metadata only.

## Invariant

A timeout may classify an evidence script result, but it must not grant runtime authority, mutate policy, repair registries, or promote releases.

## Normalized timeout shape

- `status`: `timeout`
- `timed_out`: `true`
- `cleanup_attempted`: `true`
- `cleanup_confirmed`: `true`
- `killed_process_group`: boolean
- `authority`: `descriptive_only`
