# GateGraph Release Status

Release: v0.15.3_CANDIDATE
Base: v0.15.2_STABLE
Status: candidate
Version: 0.15.3
Phase: Release truth centralization and evidence-maintainability cleanup

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
