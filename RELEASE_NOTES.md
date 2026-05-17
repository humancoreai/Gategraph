# Release Notes – v0.16.1_CANDIDATE

Base: v0.16.0_STABLE  
Status: candidate  
Version: 0.16.1  

## Focus

v0.16.1_CANDIDATE hardens replay/recovery determinism, runtime budget edge handling, release SSOT checks and semantic-boundary readiness surfaces.

## Changes

- Added deterministic replay/recovery hardening evidence for interrupted promotion recovery, partial archive reconstruction, degraded escalation replay, release-boundary replay and incomplete reservation release recovery.
- Added runtime/budget edge evidence for reservation-release races, throttling fairness, cross-session edge cases and repeated recovery attempts.
- Added candidate release SSOT evidence for README, VERSION, RELEASE_STATUS and RELEASE_METADATA alignment.
- Added semantic boundary preparation evidence with observability-only uncertainty and unverifiable-state markers.
- Kept Semantic Registry surfaces descriptive and locked to release evidence only.
- Kept all semantic markers proposal-only/descriptive; no enforcement effect.

## Explicit non-changes

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
- No distributed consensus or multi-node revocation.

## Known limitations

- Candidate requires Windows Evidence CI validation before stable promotion.
- Semantic boundary markers are readiness/observability only and intentionally do not decide actions.


Phase: Evidence artifact hygiene and revocation negative-path hardening
