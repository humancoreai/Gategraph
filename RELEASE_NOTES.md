Release: v0.17.3_STABLE
Base: v0.17.2_STABLE
Status: stable
Version: 0.17.3
Phase: Promotion Status Drift Guard

# Release Notes – v0.17.3_STABLE

v0.17.3_STABLE promotes the v0.17.3_CANDIDATE after Windows Evidence CI Passed: True.

Included scope:

- release-state token consistency after promotion
- stable/candidate status separation in active surfaces
- registry-lock rebaseline after release-state changes
- manifest/package hygiene
- governance lineage deduplication from the candidate fix
- operational/review readiness status handling for candidate/stable surfaces

Explicit non-scope:

- no runtime authority change
- no governance logic change
- no policy mutation
- no new autonomous behavior

Semantic boundary assertions:

- No governance logic change
- No runtime/enforcement behavior change
- No autonomous policy update
- No semantic scoring or memory system
