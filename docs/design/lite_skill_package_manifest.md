# Lite Skill Package Manifest

> Package contract for the `0.2.0rc2` Agent-native Skill install unit. It implements R3 in the [current Skill and product optimization plan](lite_skill_next_optimization_plan.md).

Date: 2026-07-20

This manifest defines the file boundary for a downloadable Lite VibeSpec Gate Skill package.

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

The default Lite package is an **Agent-native Skill package**.

This means a user can install or copy the package into an Agent environment and trigger the Skill by asking for a launch-blocking security review. The package must not assume that the user has installed the full Python CLI, repository test suite, calibration scripts, scorer, or release verifier.

Default package flow:

```text
download Lite package -> extract vibespec-gate/ -> install the directory -> explicitly trigger $vibespec-gate -> receive a chat-first review
```

The full repository may also provide an **optional Python CLI**, but that path is separate from the default Skill package.

Runnable overlay flow:

```text
clone repository -> install Python project -> run vibespec-gate CLI -> generate lite_review/
```

This distinction prevents a misleading package that looks lightweight but secretly requires the whole engineering platform to work.

## Include

These are the only files allowed in the default Agent-native Skill package:

```text
SKILL.md
LICENSE
agents/openai.yaml
references/review-protocol.md
references/evidence-coverage.md
assets/templates/launch-decision.md
assets/templates/top-security-risks.md
assets/templates/agent-fix-plan.md
assets/templates/retest-checklist.md
```

The zip archive must contain exactly one top-level directory named `vibespec-gate/`. It must not place `SKILL.md`, README files, or any other package file directly at the archive root.

`agents/openai.yaml` supplies Codex-facing UI metadata. Other hosts may consume `SKILL.md`, but the package must not claim their install path or runtime behavior is validated without host-specific evidence.

`SKILL.md` routes both references and all four templates, and states when each resource is needed. `policy.allow_implicit_invocation` is `false`, so this high-impact review starts only through explicit invocation.

## Optional

The default Skill package has no optional files. README, Quickstart, Changelog, examples, tests, and maintainer documentation remain in the repository.

## Runnable Overlay

If a separate runnable package is produced later, it must be declared as a different artifact from the default Lite package.

Minimum runnable overlay contents:

```text
pyproject.toml
src/vibespec_gate/
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
- `PASS`: coverage is complete and no material risk or remaining warning was found in the reviewed evidence.

## Safety Boundary

The Lite package must state that VibeSpec Gate is not a professional security certification, penetration test, legal review, or compliance attestation.

The Lite package must also state that coding Agents should not auto-fix, auto-suppress, broaden permissions, remove validation, or mutate the reviewed project without explicit human confirmation.

Synthetic examples must be labeled as synthetic and must not be presented as real launch decisions, audit results, or share-safe evidence. User docs must warn that generated evidence can contain source paths, snippets, findings, or other sensitive context and requires manual inspection before sharing.

## Verification Contract

The manifest is only useful if it can be checked. `scripts/verify_lite_package.py` fails when:

1. Any non-manifest file appears in the package.
2. Any required runtime file is missing.
3. The repository has more than one authoritative `SKILL.md`.
4. `SKILL.md` does not route every reference and template.
5. The coverage reference omits a status or review surface.
6. A template omits its required decision, evidence, repair-boundary, or retest fields.
7. Agent metadata does not disable implicit invocation.

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

The manifest now makes the most important product distinction explicit: the default artifact is an Agent-native Skill, while CLI usage is a separate optional source-repository path.

Remaining risks:

1. Host behavior still requires black-box evaluation; a clean package boundary proves structure, not review quality.
2. Release availability must not be claimed until the archive and checksum are actually published.

Next implementation recommendation:

```text
1. Keep README installation instructions and the Skill/CLI capability table aligned with this manifest.
2. Run the static verifier before packaging.
3. Build the downloadable Lite package artifact with `scripts/build_lite_package_zip.py` only after the verifier passes.
```
