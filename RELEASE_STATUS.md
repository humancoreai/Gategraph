# GateGraph Release Status

Release: v0.15.9_STABLE
Base: v0.15.8_STABLE
Status: stable
Version: 0.15.9
Phase: Evidence artifact hygiene and revocation negative-path hardening

Stable scope:
- Introduce descriptive evidence classification.
- Reduce evidence/surface coupling.
- Preserve registry and manifest as authoritative release surfaces.
- Prepare local practical readiness without public deployment.

Release gate:
- Stable was promoted only after Candidate Evidence CI passed.
- Windows Evidence CI remains final promotion authority.
- Stable promotion prerequisite satisfied: Candidate Passed: True.

Invariant status:
- No runtime authority expansion.
- No autonomous policy mutation.
- No auto-repair or auto-promotion.
- Enforcement remains the only action boundary.
- Evidence registry is descriptive only.
