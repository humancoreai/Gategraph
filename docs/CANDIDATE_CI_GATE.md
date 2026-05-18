# Candidate CI Gate

GateGraph requires a successful Windows CI run on the current Candidate before any Stable promotion.

This document is descriptive release-process evidence only. It does not add runtime authority, automatic promotion, auto-repair, or governance mutation.

## Rule

If Candidate CI is negative or unclear:

1. Fix the Candidate at the same Candidate version.
2. Produce a new Candidate ZIP.
3. Run Windows CI on that Candidate.
4. Promote to Stable only after Candidate `Passed: True`.

Stable promotion without a prior Candidate PASS is forbidden.
