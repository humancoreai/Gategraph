# Release Status

Current candidate: v0.8.47_CANDIDATE
Base: v0.8.45_STABLE
Phase: Archive Integrity / Replay Consistency

Evidence:
- archive_integrity_replay_consistency_evidence: passed locally
- governance_archive_replay_evidence: passed locally after schema bump
- drift_detection_evidence: passed locally after schema bump
- Full Windows Evidence CI: pending

Candidate notes:
- Archive envelopes are checked for payload hash, record id and contiguous sequence observations.
- Replay consistency is checked from different input orderings.
- Integrity reports are descriptive and do not re-run governance decisions.
- No policy, guard, runtime, queue or workflow mutation introduced.
