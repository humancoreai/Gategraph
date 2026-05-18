# Security Policy

## Supported Versions

| Version | Supported |
|---|---:|
| v0.17.6_CANDIDATE | yes |
| v0.17.6_CANDIDATE | yes |
| older v0.15.x snapshots | best-effort review only |
| older v0.14.x and below | historical/reference only |


## Scope of Security Claims

GateGraph provides deterministic governance/enforcement checks for explicit task metadata. It does not verify semantic truthfulness of caller-provided fields and does not provide autonomous security classification.

Security claims are limited to behavior covered by evidence suites and documented invariants.

## Reporting a Vulnerability

Report issues privately to the project maintainer before public disclosure. If no dedicated security email has been published for the repository yet, use the repository owner contact channel.

A useful report should include:

- affected version
- reproduction steps
- expected vs. observed behavior
- whether the issue affects governance, enforcement, audit, release integrity, or documentation claims

## Out of Scope

- requests for autonomous risk classification
- feature requests unrelated to a security defect
- attacks requiring a caller to intentionally provide false trusted metadata without an upstream trust failure
- multi-node or distributed consensus concerns in single-node releases


## Development Keyring Boundary

GateGraph may include a local development keyring constant for deterministic tests and local evidence runs.
This is not a production secret and must not be treated as deployable signing material. Production use requires operator-managed key material outside the repository.

The development keyring exists to make evidence reproducible; it does not grant external authority, does not bypass enforcement, and does not remove token binding or revocation checks.
