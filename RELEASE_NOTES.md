Release: v0.17.7_STABLE
Base: v0.17.6_STABLE
Status: stable
Version: 0.17.7
Phase: Evidence Lifecycle Cleanup Formalization

# Release Notes – v0.17.7_STABLE

v0.17.7_STABLE is a stable release promoted from v0.17.6_CANDIDATE after Windows Evidence CI `Passed: True`.

Included scope:

- formalize registry-lock rebaseline as a mandatory promotion hygiene step
- keep release/status token registries candidate-aware
- keep semantic registry lock validation deterministic after surface changes
- keep README/Integrator surface from v0.17.4 intact
- no runtime authority, governance logic, policy mutation, or enforcement behavior changes

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
