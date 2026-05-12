# GateGraph Release Status

Release: v0.15.6_STABLE
Base: v0.15.5_STABLE
Status: stable
Version: 0.15.6
Phase: CI parity and fresh-clone release-surface consolidation

Candidate scope:
- Introduce descriptive evidence classification.
- Reduce evidence/surface coupling.
- Preserve registry and manifest as authoritative release surfaces.
- Prepare local practical readiness without public deployment.

Release gate:
- Candidate requires full Evidence CI before Stable promotion.
- Windows Evidence CI remains final promotion authority.
- Stable promotion is forbidden until Candidate Passed: True.

Invariant status:
- No runtime authority expansion.
- No autonomous policy mutation.
- No auto-repair or auto-promotion.
- Enforcement remains the only action boundary.
- Evidence registry is descriptive only.
