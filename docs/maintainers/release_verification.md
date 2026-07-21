# Release Verification

This page is for maintainers preparing a baseline commit or release candidate. It is not required for a first-time Lite review user.

## Canonical Command

Release verification fails closed unless the evaluation summary is bound to a SHA256 value recorded outside the repository. Set the trusted value supplied by the independent observer or release secret, then run:

```powershell
$env:VIBESPEC_TRUSTED_EVAL_SHA256 = "<externally-recorded-summary-sha256>"
py -3 scripts\verify_release.py
```

Do not derive this value inside the verifier or commit it to the repository. The release workflow reads the same value from the `VIBESPEC_TRUSTED_EVAL_SHA256` repository secret.

The release verifier runs:

- Phase 4/5 smoke verification.
- Full pytest suite.
- `compileall` over `src`, `tests`, and `scripts`.
- Skill evaluation trace, activation, semantic, and no-write verification.
- Lite package, release metadata, and archive verification.
- `review-validate` for curated Phase 4 review outputs.
- Evaluation matrix coverage checks.
- LLM output quality matrix expectation checks.
- Git hygiene checks for cache, env, and generated output ignores.

## Fresh Skill Evaluation

Run the black-box matrices with a standard user-level Skill installation that exactly matches `skills/vibespec-gate`:

```powershell
py -3 scripts\run_skill_blackbox_evals.py --run-id <run-id> --matrix all
```

The runner creates isolated fixture copies under `test output/skill-evals/<run-id>` and immutable traces under `evals/runs/<run-id>`. It disables known conflicting user Skills through an ephemeral CLI override, fails on any other user Skill read, enforces a read-only host sandbox, rejects output roots outside those approved repository areas, and refuses existing or overlapping directories. An independent observer must record the resulting `summary.json` SHA256 before release approval.

## Focused Commands

```powershell
py -3 scripts\verify_phase4_5_smoke.py
py -3 -m pytest -q -p no:cacheprovider
py -3 -m compileall -q src tests scripts
py -3 scripts\verify_skill_evals.py
```

## Boundary

Passing release verification means the repository support system is internally consistent. It does not certify that a reviewed user product is fully secure.

See also: `docs/usage/verification.md`.
