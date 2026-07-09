# Lite Skill Package Manifest

Date: 2026-07-08

This manifest defines the file boundary for a downloadable Lite VibeSec Gate Skill package.

The package is intentionally smaller than the repository. It should help a first-time user answer:

1. When should I use this Skill?
2. What prompt or command starts the review?
3. Which generated files do I read first?
4. What do `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, and `PASS` mean?
5. What can I safely ask a coding Agent to fix?
6. How do I retest after fixes?

## Package Rule

The Lite package includes only files needed to trigger the Skill and understand the first review result.

Maintainer-only infrastructure remains in the repository, but it is not part of the first user path.

## Package Mode

The default Lite package is a **prompt-only, Agent-native Skill package**.

This means a user can install or copy the package into an Agent environment and trigger the Skill by asking for a launch-blocking security review. The package must not assume that the user has installed the full Python CLI, repository test suite, calibration scripts, scorer, or release verifier.

Default package flow:

```text
download Lite package -> read README/SKILL -> trigger Agent review -> receive four-file review shape
```

The full repository may also provide a **Core-powered runnable path**, but that path is an optional overlay, not the default Lite package.

Runnable overlay flow:

```text
clone repository -> install Python project -> run vibesec CLI -> generate lite_review/
```

This distinction prevents a misleading package that looks lightweight but secretly requires the whole engineering platform to work.

## Include

These files are required in the default prompt-only Lite package:

```text
SKILL.md
README.md
README.zh-CN.md
docs/usage/lite_quickstart.md
examples/lite_review_prompt.md
```

`docs/usage/lite_quickstart.md` may mention the Core-powered CLI path, but it must label that path as optional repository usage. The first user path must still work as Agent-native instructions.

## Optional

These files may be included when the package needs a slightly deeper usage path:

```text
docs/usage/agent_review_cookbook.md
docs/usage/examples.md
docs/usage/quickstart.md
```

Optional files must not require a first-time user to understand scorer hard failures, Phase 11 calibration, golden fixtures, host-agent comparison, or release verification before running the Lite path.

## Runnable Overlay

If a separate runnable package is produced later, it must be declared as a different artifact from the default Lite package.

Minimum runnable overlay contents:

```text
pyproject.toml
src/vibesec/
scripts/build_lite_review_bundle.py
README.md
docs/usage/lite_quickstart.md
examples/lite_review_prompt.md
```

The runnable overlay must also include:

- installation instructions;
- Python version expectations;
- one smoke command;
- expected `lite_review/` output shape;
- a statement that tests, calibration, scorer, and release verifier remain maintainer workflows unless explicitly included.

Do not call the runnable overlay "Lite" unless the package can be installed and run without understanding maintainer-only internals.

## Exclude

These paths are maintainer-only and should not be included in the Lite package:

```text
test output/
tests/
scripts/*phase*
scripts/*matrix*
scripts/*score*
scripts/*calibration*
scripts/verify_release.py
docs/design/*phase*
docs/usage/*quality*
docs/usage/*contract*
docs/maintainers/
tests/evaluation_cases/
tests/evaluation_cases/llm_outputs/
tests/evaluation_cases/llm_outputs_bad/
```

Also exclude generated calibration outputs, golden fixtures, bad fixtures, quality matrices, host-agent sample comparisons, and release-verification evidence unless a maintainer package explicitly needs them.

## Generated Lite Output

The user-facing review output must keep this shape:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

The four Markdown files are the first reading path. `evidence/` remains available for auditability, debugging, and maintainer follow-up, but it is not the first user screen.

## Decision Language

Every included user-facing file should use the same launch decision meanings:

- `BLOCK`: do not launch yet; one or more findings currently block launch.
- `REVIEW`: do not treat as launch-ready yet; human confirmation or missing evidence remains.
- `PASS_WITH_WARNINGS`: no launch-blocking finding is present, but warnings or downgrade/suppression candidates need review.
- `PASS`: no material launch risk was found in the reviewed evidence.

## Safety Boundary

The Lite package must state that VibeSec Gate is not a professional security certification, penetration test, legal review, or compliance attestation.

The Lite package must also state that coding Agents should not auto-fix, auto-suppress, broaden permissions, remove validation, or mutate the reviewed project without explicit human confirmation.

## Verification Contract

The manifest is only useful if it can be checked. `scripts/verify_lite_package.py` should fail when:

1. Any excluded path or pattern appears in the default Lite package.
2. Any required include file is missing.
3. `README.md`, `SKILL.md`, quickstart, and example prompt disagree on the four output file names.
4. The package first path requires Phase outputs, calibration, scorer, quality matrix, release verifier, or fixtures.
5. CLI commands are presented as mandatory for the default prompt-only package.
6. The safety boundary is missing from either README or quickstart.

The first version is `scripts/verify_lite_package.py`. It is a static check and does not need to validate security findings or run the full review engine.

## Maintainer Boundary

The full repository continues to own:

- core review engine code;
- schemas and validators;
- tests and fixtures;
- quality scoring;
- calibration workflows;
- release verification;
- historical phase artifacts.

Those materials support quality and repeatability, but they are not required for the first Lite Skill user path.

## Adversarial Review

Verdict: pass with required constraints.

The manifest now makes the most important product distinction explicit: default Lite package means prompt-only Agent-native Skill, while runnable CLI usage is a separate optional overlay. This resolves the main ambiguity in the previous plan.

Remaining risks:

1. Optional files can reintroduce internal language. Each optional include needs the same exposure review as required files.
2. `scripts/build_lite_package_zip.py` should generate the downloadable artifact from this manifest instead of relying on manual copying.

Next implementation recommendation:

```text
1. Keep README, SKILL.md, lite_quickstart, and lite_review_prompt aligned with this manifest.
2. Run the static verifier before packaging.
3. Build the downloadable Lite package artifact with `scripts/build_lite_package_zip.py` only after the verifier passes.
```
