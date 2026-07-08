# Lite Skill Release Validation Plan

Date: 2026-07-08

## 1. Decision

The next step is a **release validation sprint**.

Do not add more security rules, do not expand calibration, and do not split the repository yet. The immediate problem is no longer "can VibeSec Gate produce security review artifacts?" The immediate problem is:

```text
Can a first-time user trigger the Lite Skill, understand the result, act on the fix plan, and retest without learning the maintainer system?
```

The release validation sprint must prove three things:

1. The prompt-only Lite package is usable without the full Python repository.
2. The optional Core-powered CLI path still generates the expected Lite output shape.
3. The generated review is actionable enough to support a launch decision, Agent fix work, and retest.

## 2. First-Principles Quality Bar

The user does not buy architecture. The user wants a safe launch decision.

The Skill is good enough only when it satisfies four first-principles properties:

1. **Accessible**: a non-security user can understand when and how to use it in under three minutes.
2. **Decisive**: the output gives `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, or `PASS` with a clear reason.
3. **Actionable**: the fix plan contains bounded tasks that a coding Agent can perform after human confirmation.
4. **Retestable**: the user can rerun concrete checks after fixes and know whether launch status changed.

Engineering depth matters only when it supports these properties. Scorer, fixtures, calibration, release verifier, and schema details are quality infrastructure, not the first user workflow.

## 3. Validation Scope

### In Scope

- Prompt-only Lite package validation.
- Static package boundary verification.
- Agent-native prompt flow dry run.
- Optional Core-powered CLI smoke validation.
- Four-file output quality review.
- Usability review against the three-minute first-user standard.
- Adversarial review of false confidence, unclear launch decisions, and unsafe Agent fix instructions.

### Out Of Scope

- Adding new security rule categories.
- Reworking the core review engine.
- Moving directories or splitting packages.
- Expanding Phase 11 calibration.
- Publishing a public release artifact before validation passes.
- Treating the result as a professional penetration test or certification.

## 4. Required Inputs

Use the current repository state plus one candidate Lite package directory.

Required source files:

```text
SKILL.md
README.md
docs/usage/lite_quickstart.md
examples/lite_review_prompt.md
docs/design/lite_skill_package_manifest.md
scripts/verify_lite_package.py
```

Required tests:

```text
tests/test_lite_package_verifier.py
tests/test_lite_review_bundle.py
tests/test_review_cli.py
```

Candidate validation fixtures:

```text
case_1_secret_leak_web_app
case_2_missing_auth_or_ownership_check
case_3_agent_or_mcp_tool_overreach
case_4_low_risk_clean_project
```

These can be existing evaluation cases or small disposable demo projects. The validation should include at least one case expected to `BLOCK` and one case expected to avoid a false `BLOCK`.

## 5. Validation Workstreams

### Workstream A: Package Boundary

Goal: prove the Lite package stays light.

Steps:

1. Build or stage a candidate Lite package directory from the manifest.
2. Run source validation:

```powershell
py -3 scripts\verify_lite_package.py
```

3. Run candidate package validation:

```powershell
py -3 scripts\verify_lite_package.py .\path\to\candidate-lite-package
```

Pass criteria:

- Required user-facing files are present.
- No excluded maintainer paths are present.
- `README.md`, `SKILL.md`, quickstart, and prompt agree on the four output file names.
- Prompt-only usage appears before any CLI path.
- Safety boundary is present.

Fail action:

- Fix the manifest, user docs, or package staging process before running any functional validation.

### Workstream B: Prompt-Only Agent-Native Flow

Goal: prove the default Lite package can work as a Skill, not just as a repository CLI.

Steps:

1. Use only the default package files.
2. Trigger the review with `examples/lite_review_prompt.md`.
3. Run the review against two demo projects:
   - one expected launch blocker;
   - one low-risk or warning-only project.
4. Require the Agent or reviewer to produce the four-file shape.

Pass criteria:

- The output includes `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, and `retest_checklist.md`.
- The launch decision is explicitly one of `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, or `PASS`.
- The top risk explanation cites concrete files, configs, routes, rules, or evidence.
- The fix plan separates Agent-executable tasks from human-confirmed decisions.
- The retest checklist contains commands or manual checks specific to the project.

Fail action:

- If the Agent asks the user to understand core internals, tighten `SKILL.md` and quickstart.
- If the output is generic, strengthen the prompt and output contract.
- If fix tasks are unsafe or unbounded, revise the safe Agent fix boundary.

### Workstream C: Optional Core-Powered CLI Flow

Goal: prove the repository overlay still produces the Lite output shape.

Steps:

1. Run the smallest relevant CLI smoke against a demo project or existing review output:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

2. Confirm the generated directory contains:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

3. Run focused tests:

```powershell
py -3 -m pytest tests/test_lite_package_verifier.py tests/test_lite_review_bundle.py tests/test_review_cli.py
```

Pass criteria:

- CLI exits successfully.
- Four primary Markdown files are created.
- Evidence is preserved.
- Focused tests pass.
- CLI path remains described as optional repository infrastructure.

Fail action:

- Fix CLI or bundle generation before packaging a runnable overlay.
- Do not block the prompt-only package unless the failure contradicts shared documentation or output contracts.

### Workstream D: Output Quality Review

Goal: prove the result is useful, not just formatted.

Score every reviewed case using this rubric:

| Dimension | Pass Standard |
| --- | --- |
| Launch decision | Decision matches evidence severity and does not hide blockers. |
| Risk explanation | Top risks explain impact, affected surface, and evidence. |
| Fix boundedness | Tasks are specific, scoped, and safe for a coding Agent after confirmation. |
| Retest quality | Checklist verifies the actual risk, not just generic tests. |
| User clarity | A non-security user can understand why launch is blocked or allowed. |
| False confidence control | Output states uncertainty when evidence is incomplete. |

Pass criteria:

- No known launch blocker is downgraded to `PASS`.
- No low-risk clean project is blocked without evidence.
- Every `BLOCK` has a concrete fix-first action.
- Every `PASS_WITH_WARNINGS` explains remaining warnings.
- Every retest checklist includes at least one project-specific verification step.

Fail action:

- If risk ranking is wrong, adjust review instructions or rubric before adding new rules.
- If output is hard to read, simplify templates before expanding engine behavior.

### Workstream E: Three-Minute Usability Check

Goal: prove the package is understandable.

Test method:

1. Give a reviewer only the Lite package files.
2. Start a three-minute timer.
3. Ask the reviewer to answer:
   - when to use the Skill;
   - how to trigger it;
   - what files to read first;
   - what a `BLOCK` means;
   - what an Agent may fix;
   - how to retest.

Pass criteria:

- The reviewer answers all six without opening maintainer docs.
- The reviewer does not need Phase, scorer, calibration, fixtures, or release verifier concepts.
- The reviewer can identify that the CLI path is optional.

Fail action:

- Rewrite README first screen and quickstart before any release packaging.

## 6. Release Readiness Gates

The Lite package is release-ready only when all gates pass:

1. `scripts/verify_lite_package.py` passes on source docs.
2. `scripts/verify_lite_package.py <candidate-package>` passes on the staged package.
3. Focused Lite tests pass.
4. Prompt-only review produces the four-file shape on at least two demo projects.
5. One expected blocker is correctly identified as `BLOCK` or `REVIEW`.
6. One low-risk case avoids an unsupported `BLOCK`.
7. Fix plans contain bounded Agent tasks and human confirmation boundaries.
8. Retest checklists contain project-specific checks.
9. Three-minute usability check passes.
10. The release notes state that the Lite package is not a certification, penetration test, legal review, or compliance attestation.

If any gate fails, do not call the package release-ready.

## 7. Evidence To Save

Store validation evidence in a clearly named release-candidate folder, not mixed into the first user path:

```text
test output/lite_release_validation/<date>/
  package_verifier_source.txt
  package_verifier_candidate.txt
  pytest_lite_focused.txt
  prompt_only_case_1_secret_leak_web_app/
  prompt_only_case_2_missing_auth_or_ownership_check/
  prompt_only_case_3_agent_or_mcp_tool_overreach/
  prompt_only_case_4_low_risk_clean_project/
  cli_smoke_output/
  usability_notes.md
  release_notes.md
  release_readiness_decision.md
```

This evidence is for maintainers. It should not be included in the downloadable Lite package.

## 8. Professional Judgment

Current functional state appears promising but not proven enough for an external public release.

Best current classification:

```text
Core capability: present
Lite user surface: mostly formed
Package boundary: defined and partly enforceable
Functional release readiness: unproven until validation sprint passes
```

The next optimization direction is therefore validation, not feature expansion.

## 9. Adversarial Review

Verdict: pass with strict release gates.

This plan is stronger than another design cleanup because it forces proof. It treats "good to use" as an observable property: package boundary passes, output exists, launch decisions are justified, fix plans are bounded, and users can understand the flow quickly.

Counterargument: prompt-only validation can vary by host Agent, so it may not prove deterministic quality.

Response: true. That is why the optional CLI overlay and focused tests remain part of the validation sprint. Prompt-only validation proves Skill usability; CLI validation proves repository-backed repeatability.

Counterargument: two demo projects are too few.

Response: true for a mature public release, acceptable for a first release candidate. The minimum should include one blocker and one low-risk case. Before broad distribution, expand to auth, secrets, database rules, Agent/tool authority, and Electron/Desktop surfaces.

Counterargument: a static verifier only checks packaging, not security accuracy.

Response: correct. The verifier prevents packaging drift and complexity leakage. Security accuracy is covered by output quality review, focused tests, and later calibration.

Final recommendation:

```text
Run the release validation sprint before adding new rules or restructuring the repository.
If the sprint passes, prepare a Lite release candidate. If it fails, fix the user path or output quality first.
```
