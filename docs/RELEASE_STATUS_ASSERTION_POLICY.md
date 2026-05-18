# Release SSOT Consolidation

Release/status evidence must derive expected status from `RELEASE_METADATA.json` and the release suffix.

This surface is descriptive only. It does not add runtime authority, auto-repair, auto-promotion or policy mutation.

## Invariant

Evidence tests may validate `candidate` or `stable`, but must not hardcode one status in a way that breaks the paired Candidate/Stable promotion path.

Release: v0.17.2_CANDIDATE  
Base: v0.17.1_STABLE  
Status: candidate
