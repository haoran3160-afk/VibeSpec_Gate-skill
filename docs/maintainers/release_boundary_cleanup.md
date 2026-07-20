# Release Boundary Cleanup Proposal

This proposal classifies repository content for release review. It does not delete, move, stage, or commit files.

## Product-Required

These paths define runtime behavior, user documentation, or package metadata:

```text
src/
scripts/
docs/
README.md
SKILL.md
pyproject.toml
```

Default action: track when behavior or user-facing guidance depends on the file.

Review question: does the Lite path, review engine, or release verifier require this file?

## Maintainer Fixtures

These paths provide deterministic regression evidence:

```text
tests/
tests/evaluation_cases/
```

Default action: track curated fixtures and tests.

Review question: is the fixture deterministic, documented, and covered by focused or release verification?

## Generated Or Historical Evidence

These paths are phase evidence, calibration artifacts, or run outputs:

```text
test output/
outputs/
```

Default action: keep only when the artifact is evidence for a milestone or calibration report; otherwise archive or ignore in a separate cleanup step.

Review question: is this output required to prove a current phase, release gate, or calibration claim?

## Lite Path Boundary

The Lite path should expose:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

The Lite path should not require users to read:

- phase reports;
- host-agent calibration ledgers;
- quality matrices;
- fixture-authoring docs;
- release verifier internals.

## Cleanup Rules

- Do not delete historical outputs without explicit approval.
- Do not move large directories until links are stable.
- Keep generated evidence separate from product code in review summaries.
- Prefer adding `.gitignore` or archive decisions in a dedicated cleanup task.

## Current Recommendation

Keep `skills/vibespec-gate/SKILL.md` as the only authoritative Skill entry. Do not restore the old root or incomplete `skill/` compatibility entries because copying either one produces an invalid install unit.
