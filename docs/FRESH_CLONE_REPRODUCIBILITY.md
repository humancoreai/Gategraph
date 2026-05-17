# Fresh Clone Reproducibility

Release: v0.15.9_STABLE  
Base: v0.14.7_STABLE  
Status: stable

## Purpose

This surface documents the minimal reproducibility contract for a fresh local clone or unpacked release archive.

## Minimal path

```powershell
python -m pip install -e .
python tests\evidence_ci.py
```

For a narrow smoke check:

```powershell
python -m gategraph.cli --help
python -m gategraph.server --help
python tests\install_surface_evidence.py
python tests\public_repo_hygiene_evidence.py
python tests\fresh_clone_reproducibility_evidence.py
```

## Boundary

- No new governance logic.
- No runtime authority.
- No auto-promotion.
- No publish/deploy behavior.
- No secret access.

This is a packaging and onboarding evidence surface only.
