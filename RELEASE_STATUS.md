# Release Status

Current candidate: v0.8.45_CANDIDATE
Base: v0.8.44_STABLE
Phase: Governance Archive / Historical Replay

Evidence:
- governance_archive_replay_evidence: passed locally
- drift_detection_evidence: passed locally after schema bump
- Full Windows Evidence CI: pending

Candidate notes:
- Historical archive records are append-only.
- Replay reconstructs stored records only.
- Replay does not re-evaluate governance decisions.
- No policy, guard, runtime, queue or workflow mutation introduced.
