# Evidence Lifecycle Cleanup – v0.17.7_CANDIDATE

Release: v0.17.7_CANDIDATE  
Base: v0.17.5_STABLE  
Status: candidate  
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
