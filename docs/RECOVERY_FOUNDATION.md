# Recovery Foundation

v0.12.1_CANDIDATE adds descriptive recovery evidence for interrupted local governance state.

## Scope

- interrupted reservation recovery is observable and bounded
- duplicate consume attempts fail closed
- partial audit append gaps fail closed
- incident lifecycle transitions remain forward-only
- replay consistency is asserted over stable descriptive fields

## Non-scope

- no automatic repair loop
- no policy mutation
- no runtime authority expansion
- no distributed recovery protocol
- no production self-healing

## Invariant

Recovery evidence may describe or reject state. It must not invent missing authority, recreate capability tokens, mutate governance rules, or promote replay/explain objects into runtime input.
