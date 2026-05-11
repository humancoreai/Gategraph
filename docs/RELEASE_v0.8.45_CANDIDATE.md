# GateGraph v0.8.45_CANDIDATE

Phase: Governance Archive / Historical Replay

## Scope

Adds an append-only historical archive and deterministic replay view for stored governance records.

## Invariants

- Archive is descriptive storage only.
- Replay reconstructs archived payloads only.
- Replay does not call governance evaluation.
- No policy tuning, scoring, recommendations, automatic reactions or queue mutations.
- Payload hashes are verified during replay.

## Evidence

- governance_archive_replay_evidence: passed locally
- Full Evidence CI pending external Windows run
