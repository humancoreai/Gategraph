# Release Status - GateGraph v0.8.6-runaway-cost-control

## Status

Evidence build: PASS on targeted and individual evidence runs.

## Change type

Security / control-plane hardening.

## Core changes

- Non-positive projected session costs fail closed.
- Non-positive runtime costs fail closed.
- Invalid cost stops receive normalized reason codes.
- New runaway-cost evidence scenarios added.

## Invariants preserved

- Enforcement remains the only capability gatekeeper.
- Guards can only stop; they never grant capability.
- External API calls remain mock-only and pass through Enforcement + Guard Pipeline.
- Pattern Engine remains proposal-only.
- Audit remains append-only.

## Known limitation

The aggregate CI runner still shows environment-level shutdown/runner instability in this container. Individual evidence scripts were executed successfully. Production semantics were not weakened to accommodate the runner.
