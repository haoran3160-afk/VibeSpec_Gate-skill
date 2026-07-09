# Lite Package Verification

Use this checklist before building or publishing a downloadable Lite VibeSpec Gate Skill package.

The package boundary is defined in `docs/design/lite_skill_package_manifest.md`.

Run the static verifier from the full repository:

```powershell
py -3 scripts\verify_lite_package.py
```

To check a candidate package directory:

```powershell
py -3 scripts\verify_lite_package.py .\dist\lite_package
```

To run the full Lite release validation sprint and save evidence:

```powershell
py -3 scripts\run_lite_release_validation.py
```

The sprint writes maintainer evidence under:

```text
test output/lite_release_validation/2026-07-08/
```

To run RC hardening evidence generation:

```powershell
py -3 scripts\run_lite_rc_hardening.py
```

This writes:

```text
test output/lite_rc_hardening/2026-07-08/
```

`run_lite_rc_hardening.py` can pass as an evidence-generation command while still producing `NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT` when real external blind usability sessions are missing. Treat `release_decision.md` as the promotion authority.

## File Boundary

- Confirm every packaged file is listed under `include` or intentionally accepted from `optional`.
- Confirm no file from the manifest `exclude` list is packaged.
- Confirm `test output/`, `tests/`, phase artifacts, calibration outputs, fixtures, quality matrices, scorer internals, and release-verification evidence are absent.
- Confirm generated Lite review bundles are not packaged as source files.

## User Path Consistency

- Confirm `README.md`, `SKILL.md`, `docs/usage/lite_quickstart.md`, and `examples/lite_review_prompt.md` describe the same Lite trigger.
- Confirm all four files name the same primary outputs:
  - `launch_decision.md`
  - `top_security_risks.md`
  - `agent_fix_plan.md`
  - `retest_checklist.md`
- Confirm the first user path does not require Phase 7/8/9/10/11, scorer, quality matrix, host-agent calibration, fixture authoring, or release-verification knowledge.

## Decision Language

- Confirm `BLOCK` means do not launch yet.
- Confirm `REVIEW` means human confirmation or missing evidence remains.
- Confirm `PASS_WITH_WARNINGS` means no launch-blocking finding is present, but warnings remain.
- Confirm `PASS` means no material launch risk was found in the reviewed evidence.

## Safety Boundary

- Confirm the package says VibeSpec Gate is not a professional security certification, penetration test, legal review, or compliance attestation.
- Confirm Agent fix instructions require human confirmation before mutation.
- Confirm suppression and false-positive decisions are never described as automatic.
- Confirm dynamic or live-target testing requires explicit authorization and scope.

## Output Verification

From a source checkout, run a small Lite review and inspect the output names:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\tests\fixtures\vulnerable_next_supabase_app --output .\lite_review_smoke --no-adapters
Get-ChildItem .\lite_review_smoke
```

The output should contain:

```text
launch_decision.md
top_security_risks.md
agent_fix_plan.md
retest_checklist.md
evidence/
```

For release candidates, run the full repository verifier from the source repository, not from the Lite package:

```powershell
py -3 scripts\verify_release.py
```

## Future Automation

The current verifier is intentionally static. After the package boundary stabilizes, extend it to build the package artifact directly from the manifest and compare the generated file list against the candidate package.
