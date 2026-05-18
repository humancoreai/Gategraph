# Evidence Lifecycle Cleanup – v0.17.8_STABLE

Release: v0.17.8_STABLE  
Base: v0.17.7_STABLE  
Status: stable  
Phase: Evidence Lifecycle Cleanup Formalization

This surface documents deterministic evidence teardown expectations for test and CI harnesses only.

## Boundary

- Descriptive evidence lifecycle only.
- No runtime authority.
- No policy mutation.
- No auto-repair.
- No auto-promotion.

## Required markers

Evidence lifecycle records should distinguish:

- started
- completed
- timeout
- cleanup_attempted
- cleanup_confirmed
- process_group_killed

These markers are evidence metadata and do not alter governance decisions.
