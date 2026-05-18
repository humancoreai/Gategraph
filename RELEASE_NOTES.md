Release: v0.17.3_CANDIDATE
Base: v0.17.2_STABLE
Status: candidate
Version: 0.17.3
Phase: Promotion Status Drift Guard

# Release Notes – v0.17.3_CANDIDATE

v0.17.3_CANDIDATE focuses on post-stable release-surface finalization. It carries forward the v0.17.2_STABLE Windows-CI-passed baseline and hardens the surfaces that previously drifted during candidate-to-stable promotion.

Included scope:

- release-state token consistency after promotion
- stable/candidate status separation in active surfaces
- registry-lock rebaseline after release-state changes
- manifest/package hygiene

Explicit non-scope:

- no runtime authority change
- no governance logic change
- no policy mutation
- no new autonomous behavior
- no Stable promotion in this artifact

Windows Evidence CI remains the promotion gate.

Boundary confirmations:

- No governance logic change
- No runtime/enforcement behavior change
- No autonomous policy update
- No semantic scoring or memory system
