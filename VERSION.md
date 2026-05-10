# GateGraph Version

Current: v0.8.13-security-finesse

## v0.8.13-security-finesse
- Adds Block B security-finesse evidence for secret leak checks, HTTP policy edge cases, and combined token failure behavior.
- Hardens HTTP path-prefix matching with boundary-aware semantics: `/v1` allows `/v1` and `/v1/...`, not `/v10` or `/v1evil`.
- Rejects wildcard hosts in endpoint policies rather than interpreting them implicitly.
- Keeps ordering: Enforcement -> Session Budget -> Runtime Guard -> HTTP Policy -> Secret Provider -> Transport.

Previous: v0.8.12-http-policy-allowlist
