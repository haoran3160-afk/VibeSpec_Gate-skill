# VibeSpec Gate Lite Next Optimization Plan

Date: 2026-07-08

## 1. Decision

VibeSpec Gate should move toward a **heavy core + light skill surface** architecture.

The next optimization step is not to delete the core engine, tests, calibration data, scorer, or release verifier. The next step is to reduce what a first-time user must understand before they can run the Skill and get a launch decision.

Target user mental model:

```text
download -> trigger -> review project -> read launch decision -> fix -> retest
```

Target maintainer mental model:

```text
core engine -> schemas -> fixtures -> quality scoring -> calibration -> release verification
```

Both paths are valid, but they must not share the same first screen.

## 2. First-Principles Job

The user hires this Skill for one job:

> I built a product with AI. Tell me whether it is safe to launch, what is dangerous, what an Agent can fix, and how to retest.

The Lite Skill path therefore needs only six user-facing capabilities:

1. Identify project type and sensitive assets.
2. Inspect the most important security boundaries.
3. Produce a launch decision.
4. Explain the highest-impact risks in plain language.
5. Produce a bounded Agent fix plan.
6. Produce a retest checklist.

Everything else is maintainer infrastructure unless it directly helps the user complete that job.

## 3. Current Gap

The repository already has a Skill shape:

- `SKILL.md` defines the review behavior.
- `README.md` now introduces the Lite path.
- `docs/usage/lite_quickstart.md` explains the short flow.
- `examples/lite_review_prompt.md` gives a simple trigger.
- The core review engine, output schemas, validator scripts, tests, scoring, and calibration flow support repeatability.

The remaining gap is packaging and exposure control:

- A new user can still see too many internal concepts too early.
- Phase documents, calibration language, scorer details, fixtures, and historical outputs can look like required user workflow.
- The repository is credible as an engineering system, but not yet simple enough as a downloadable Skill package.

## 4. Optimization Objective

Create a lightweight user path without weakening the internal quality system.

Success means a non-security user can answer these questions within three minutes:

1. When should I use this Skill?
2. What exact prompt or command starts the review?
3. Which files do I read first?
4. What does `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, or `PASS` mean?
5. What can I safely ask a coding Agent to fix?
6. How do I retest after fixes?

The optimization is complete only if the user does not need to understand scorer hard failures, Phase 11 calibration, golden fixtures, host-agent comparison, or release verification to use the Lite path.

## 5. Proposed Structure

Use one repository for now, but define two explicit paths.

User-facing path:

```text
SKILL.md
README.md
docs/usage/lite_quickstart.md
examples/lite_review_prompt.md
```

Generated Lite output:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

Maintainer-facing path:

```text
src/
scripts/
tests/
docs/design/
docs/usage/*contract*
docs/usage/*quality*
calibration or phase artifacts
test output/
```

Do not split the repository yet. First create a clear package manifest that defines what would be included in a downloadable Lite Skill package.

## 6. Next Implementation Steps

### Step 1: Define the Lite Skill package manifest

Add a small manifest document that declares the user-visible package contents.

Recommended file:

```text
docs/design/lite_skill_package_manifest.md
```

The manifest should classify files as:

- `include`: required for the downloadable Skill.
- `optional`: helpful examples or advanced usage.
- `exclude`: maintainer-only internals.

Initial include list:

```text
SKILL.md
README.md
docs/usage/lite_quickstart.md
examples/lite_review_prompt.md
```

Initial exclude list:

```text
test output/
tests/
scripts/*phase*
scripts/*matrix*
scripts/*score*
scripts/*calibration*
docs/design/*phase*
docs/usage/*quality*
docs/usage/*contract*
fixtures and bad fixtures
```

This step gives packaging discipline before any directory move.

### Step 2: Make the README first screen user-only

Keep the README first screen focused on:

- what the Skill is for;
- when to use it;
- the shortest Lite command or trigger;
- the four output files;
- the safety boundary.

Move or link deep engine details below the first user path. The README can still mention the core engine, but not as the first thing a user must understand.

### Step 3: Keep `SKILL.md` as the behavioral contract

`SKILL.md` should describe what the Agent should do during review, but it should still read like a Skill, not an internal architecture document.

It should emphasize:

- project intake;
- sensitive asset detection;
- launch-blocking risk judgment;
- bounded fix planning;
- retest checklist;
- human confirmation before suppressions or risky fixes.

It should not force users to learn calibration, scorer, or release-verifier concepts before use.

### Step 4: Add a package verification checklist

Before building a zip or separate package, add a lightweight checklist or script that verifies:

- package includes only manifest-approved user files;
- package excludes phase outputs, calibration outputs, fixtures, tests, and scorer internals;
- `README.md`, `SKILL.md`, quickstart, and example prompt are mutually consistent;
- output file names match the Lite bundle generated by the CLI.

This can start as documentation. A script is useful only after the manifest stabilizes.

### Step 5: Delay physical repo split

Do not immediately move `src/`, `scripts/`, `tests/`, or calibration files into a new root layout.

The safer sequence is:

```text
manifest -> README/SKILL surface cleanup -> package verification -> optional package builder -> physical split only if needed
```

This avoids breaking imports, tests, and existing release verification while still giving users a clean package boundary.

## 7. User Path Acceptance Gates

The Lite path passes when all of these are true:

1. A new user can identify the trigger and expected outputs in under three minutes.
2. The first user path has four primary outputs: launch decision, top risks, Agent fix plan, retest checklist.
3. The first user path does not require reading Phase 7/8/9/10/11, scorer, quality matrix, host-agent calibration, or fixture documentation.
4. The Lite output keeps evidence for auditability without making evidence files the first reading path.
5. The documentation says the result is not a professional security certification.
6. The fix plan distinguishes Agent-executable changes from human-confirmed decisions.
7. The retest checklist is concrete enough for a user or coding Agent to run after fixes.

## 8. Maintainer Path Acceptance Gates

The core remains credible only if these stay intact:

1. Existing tests and release verification remain available to maintainers.
2. Scorer, quality matrix, fixtures, and calibration artifacts remain documented, but under maintainer-facing paths.
3. Lite packaging does not remove evidence needed to debug false positives, false negatives, or unsafe suppressions.
4. Any package builder is generated from the manifest or checked against it to avoid drift.
5. Internal schema changes continue to update docs and validation expectations.

## 9. Risks And Mitigations

Risk: hiding too much makes the Skill look like a prompt wrapper.

Mitigation: keep a short "Powered by the core engine" section and link to maintainer docs after the Lite path.

Risk: the Lite package drifts from the full repository.

Mitigation: use a manifest first, then add package verification once file boundaries are stable.

Risk: users treat the launch decision as certification.

Mitigation: state the safety boundary in README, quickstart, and `launch_decision.md` output template.

Risk: premature repo restructuring breaks working tests and scripts.

Mitigation: avoid physical split until the package manifest has survived at least one release cycle.

Risk: exposing all internals overwhelms users.

Mitigation: keep Phase, calibration, scorer, quality matrix, and release verifier materials out of the first user path.

## 10. Review Of This Plan

Verdict: pass with constraints.

The plan follows the right product direction: preserve the heavy review engine while making the user entry lightweight. It avoids the high-risk move of deleting or prematurely splitting core infrastructure. It also defines concrete gates that can be checked after implementation.

The main constraint is that "lightweight Skill package" must become a file-level contract, not just a documentation tone. The next concrete artifact should therefore be `docs/design/lite_skill_package_manifest.md`, followed by README and `SKILL.md` cleanup against that manifest.

Recommended next action:

```text
Create the Lite package manifest first, then align README, SKILL.md, quickstart,
and example prompt to that manifest. Add package verification only after the
manifest stops changing.
```

