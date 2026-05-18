Release: v0.17.5_CANDIDATE
Base: v0.17.4_STABLE
Status: candidate
Version: 0.17.5
Phase: Promotion Registry Lock Rebaseline Formalization

# Release Notes – v0.17.5_CANDIDATE

v0.17.5_CANDIDATE starts from v0.17.4_STABLE after Windows Evidence CI Passed: True for v0.17.4_STABLE.

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
