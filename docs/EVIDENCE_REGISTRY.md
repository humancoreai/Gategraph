# Evidence Registry – v0.15.6_CANDIDATE

GateGraph v0.15.6 introduces a descriptive evidence registry at `tests/evidence_registry.json`.

The registry classifies evidence gates without changing runtime behavior:

- `P0`: Core invariants such as fail-closed enforcement, runtime guard order, token boundaries, replay/reference integrity, and security gates.
- `P1`: Structural integrity such as release, manifest, registry, provenance, promotion, packaging, and fresh-clone readiness.
- `P2`: Public/review surfaces such as README wording, release notes, operator views, and other mutable documentation surfaces.

## Non-authority boundary

The registry is descriptive only. It cannot disable tests, auto-prune gates, repair files, mutate policy, alter runtime authority, or promote a release.

## Purpose

The purpose is to reduce meta-drift: failures should be easier to classify, and mutable public wording should not be treated as a core runtime invariant unless a real contract boundary is involved.
