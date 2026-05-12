# GateGraph Release Process

## Candidate Criteria

A stable release may be produced when:

- the phase scope is documented
- governance invariants are unchanged unless explicitly in scope
- evidence CI runs without failing suites
- release scripts build a non-empty manifest
- release verification passes locally
- forbidden generated artifacts are excluded

## Stable Criteria

A stable release requires:

- candidate evidence CI passed
- release integrity evidence passed
- manifest verification passed
- Windows Evidence CI passed where Windows behavior is in scope
- no known P0 blocker
- documentation claims match implemented behavior

## Packaging Process

1. Update version and release metadata.
2. Run evidence CI.
3. Build release with `tools/build_release.py`.
4. Verify release with `tools/verify_release.py`.
5. Compare produced checksum with expected artifact record.
6. Archive the release ZIP and checksum together.

## Release Freeze Rules

After a candidate is built, only the following changes are allowed before stable promotion:

- blocker fixes
- evidence fixes that reveal no behavior drift
- documentation corrections that reduce or clarify claims
- packaging fixes that improve determinism or integrity

Not allowed during freeze:

- new governance features
- new risk models
- adaptive behavior
- automatic policy changes
- UI/dashboard additions
- multi-node behavior

## Release Verification Requirements

A valid release must satisfy:

- manifest exists and is non-empty
- every manifest file exists in the ZIP
- every ZIP file is declared in the manifest, except the manifest file itself
- SHA256 values match file bytes
- ZIP entries are sorted
- timestamps are normalized
- forbidden files are absent
- verifier is read-only and does not repair silently
