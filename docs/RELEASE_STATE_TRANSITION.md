# Release State Transition Model

GateGraph v0.12.7_STABLE records release-state transition expectations as descriptive release evidence.

Allowed release-state transition for this scope:

- candidate -> stable

Forbidden:

- stable -> candidate mutation inside the same promoted artifact
- silent status coercion
- auto-promotion
- auto-repair
- runtime authority from release metadata

Candidate and Stable surfaces must be string-symmetric except for explicitly declared release, status and release document path fields.
