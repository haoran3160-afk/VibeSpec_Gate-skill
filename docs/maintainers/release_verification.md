# Release Verification

This page is for maintainers preparing a baseline commit or release candidate. It is not required for a first-time Lite review user.

## Canonical Command

```powershell
py -3 scripts\verify_release.py
```

The release verifier runs:

- Phase 4/5 smoke verification.
- Full pytest suite.
- `compileall` over `src`, `tests`, and `scripts`.
- `review-validate` for curated Phase 4 review outputs.
- Evaluation matrix coverage checks.
- LLM output quality matrix expectation checks.
- Git hygiene checks for cache, env, and generated output ignores.

## Focused Commands

```powershell
py -3 scripts\verify_phase4_5_smoke.py
py -3 -m pytest -q -p no:cacheprovider
py -3 -m compileall -q src tests scripts
```

## Boundary

Passing release verification means the repository support system is internally consistent. It does not certify that a reviewed user product is fully secure.

See also: `docs/usage/verification.md`.
