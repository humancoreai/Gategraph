# GitHub Actions CI

GateGraph v0.14.5 introduces a minimal GitHub Actions workflow for reproducible evidence execution.

## Scope

The workflow is a validation surface only. It does not perform release promotion, mutate governance policy, repair files, publish packages, resolve secrets, or decide whether a release is stable.

## Runner

- OS: `windows-latest`
- Python: `3.11`
- Entry point: `python tests\evidence_ci.py`

Windows remains the primary compatibility target because the local release gate is validated on Windows.

## Permissions

The workflow uses read-only repository permissions:

```yaml
permissions:
  contents: read
```

No repository write permission, deployment permission, package publishing, or secret-dependent step is required.

## Artifacts

Evidence logs under `tests/logs/*.json` may be uploaded after the run for inspection. Logs are generated runtime artifacts and are not release inputs.

## Non-scope

- No automatic Candidate to Stable promotion.
- No dynamic governance rule generation.
- No cloud-only release authority.
- No secret access.
- No deployment.

