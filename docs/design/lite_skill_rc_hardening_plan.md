# Lite Skill RC Hardening And External Pilot Plan

Date: 2026-07-08

## 1. Current Judgment

VibeSpec Gate Lite has crossed the line from design-only into **release candidate** territory.

The current evidence supports this classification:

```text
Status: READY_FOR_RELEASE_CANDIDATE
Scope: prompt-only Agent-native Lite package, with optional Core-powered CLI overlay
Evidence: package verifier, focused Lite tests, CLI smoke, four prompt-only cases, usability notes
```

This does not mean broad external release is proven. It means the next step is not more architecture planning. The next step is **RC hardening and a controlled external pilot**.

## 2. First-Principles Goal

The product job is still simple:

```text
Help a non-security user decide whether an AI-built product can launch,
what risks matter most, what an Agent may safely fix, and how to retest.
```

At RC stage, the question changes from "can the system produce outputs?" to:

```text
Will the Skill remain useful, safe, and understandable when used by someone
who did not build the repository?
```

Therefore the next optimization must prove five properties:

1. **Reproducible packaging**: the Lite package can be generated again without manual drift.
2. **External usability**: a new user can trigger and understand it without maintainer context.
3. **Cross-case reliability**: decisions remain sensible beyond four internal demo cases.
4. **Action safety**: `agent_fix_plan.md` does not invite unsafe or over-broad edits.
5. **Release discipline**: RC evidence, versioning, known limitations, and no-go rules are explicit.

## 3. Non-Goals

Do not use this phase to expand scope.

Out of scope:

- adding broad new security categories;
- expanding Phase 11 calibration;
- splitting the repository;
- converting the prompt-only package into a runnable package;
- making certification, penetration-test, legal, or compliance claims;
- optimizing maintainer workflows that do not affect the external user path.

New rules may be added only when pilot evidence shows a repeated launch-impacting miss.

## 4. Workstream A: Reproducible Package Build

Goal: make the RC package reproducible, not manually assembled.

Required outcome:

```text
source files + manifest -> candidate-lite-package -> verifier pass
```

Actions:

1. Treat `docs/design/lite_skill_package_manifest.md` as the source of truth.
2. Keep `scripts/verify_lite_package.py` as the boundary verifier.
3. Use `scripts/run_lite_release_validation.py` or a follow-up package builder to stage the candidate package.
4. Save the staged package under a dated validation folder.
5. Do not include `test output/`, tests, scorer, calibration, fixtures, or release verifier in the Lite package.

Pass criteria:

- The package contains only manifest-approved files.
- The package verifier passes against both source docs and candidate package.
- Rebuilding the package produces the same file list.
- CLI usage remains optional and appears after the prompt-only path.

Fail criteria:

- Any maintainer-only file appears in the package.
- Package contents are copied manually without a repeatable process.
- README, `SKILL.md`, quickstart, and example prompt drift on output names or safety boundaries.

## 5. Workstream B: Expanded Validation Matrix

Goal: test the Skill on enough project shapes to catch obvious overfit.

Minimum next matrix:

| Case | Expected Decision | Purpose |
| --- | --- | --- |
| Secret leak web app | `BLOCK` | Confirms hard blocker behavior. |
| Missing auth / ownership | `BLOCK` or `REVIEW` | Confirms authorization boundary judgment. |
| Agent or MCP tool overreach | `REVIEW` or `BLOCK` | Confirms tool-authority judgment. |
| Low-risk clean project | `PASS` or `PASS_WITH_WARNINGS` | Confirms no unsupported block. |
| Supabase RLS mistake | `BLOCK` or `REVIEW` | Confirms database rule reasoning. |
| Firebase rule mistake | `BLOCK` or `REVIEW` | Confirms non-Supabase backend coverage. |
| Electron/Desktop risky preload | `REVIEW` or `BLOCK` | Confirms desktop local boundary coverage. |
| Upload/logging privacy issue | `REVIEW` or `BLOCK` | Confirms data-safety judgment. |

Pass criteria:

- No known launch blocker is marked `PASS`.
- No clean or low-risk case receives an unsupported `BLOCK`.
- Each `BLOCK` includes evidence and a fix-first action.
- Each `REVIEW` explains missing evidence or human confirmation needed.
- Retest checklists include project-specific checks.

Fail criteria:

- Repeated false confidence on auth, secrets, database rules, or Agent/tool authority.
- Generic fix plans that cannot be handed to a coding Agent.
- Retest checklists that only say "rerun tests" without checking the actual risk.

## 6. Workstream C: External Blind Usability

Goal: validate the package with users who did not build the repo.

Pilot size:

```text
3 to 5 external or semi-external users
```

Participant profile:

- at least one non-security builder;
- at least one developer who uses coding Agents;
- at least one user with an AI/Agent or SaaS project;
- optional: one security-aware reviewer for calibration.

Test protocol:

1. Give the participant only the candidate Lite package.
2. Do not explain Phase, scorer, calibration, fixtures, or release verifier.
3. Ask them to trigger a launch-blocking review on a project or demo.
4. Ask them to identify:
   - launch decision;
   - top risk;
   - first safe Agent fix task;
   - what must be confirmed by a human;
   - how to retest.
5. Record confusion, unsafe interpretation, and missing context.

Pass criteria:

- At least 80% of participants can start the review without maintainer help.
- At least 80% can identify the four output files and read order.
- No participant interprets the result as certification.
- No participant believes `agent_fix_plan.md` permits blind edits.
- At least 80% can explain the retest path.

Fail criteria:

- Two or more participants are blocked by package installation or trigger language.
- One or more participants makes an unsafe fix interpretation because of wording.
- Users repeatedly ask for maintainer-only concepts before using the Skill.

## 7. Workstream D: Actionability And Safety Review

Goal: prove that `agent_fix_plan.md` is bounded enough for real coding-Agent use.

For each pilot output, review:

1. Does the task name the file or boundary to inspect?
2. Does it distinguish Agent-executable work from human decisions?
3. Does it prohibit dangerous shortcuts?
4. Does it avoid printing full secrets or exploit details?
5. Does it include verification steps?
6. Does it avoid broad rewrites unrelated to the risk?

Pass criteria:

- Every blocker has at least one bounded fix-first task.
- Every fix task includes a human confirmation boundary.
- Every fix task names prohibited changes.
- Security-sensitive tasks avoid leaking complete secrets or operational exploit steps.

Fail criteria:

- Fix plan says "secure the app" without concrete scope.
- Fix plan tells the Agent to remove validation, broaden permissions, or suppress findings.
- Fix plan requires product, legal, cloud, or identity-provider decisions but does not mark them for humans.

## 8. Workstream E: Feedback Triage And Release Notes

Goal: convert pilot evidence into a disciplined release decision.

Capture:

```text
test output/lite_rc_hardening/<date>/
  package_file_list.txt
  verifier_source.txt
  verifier_candidate.txt
  focused_tests.txt
  validation_matrix_summary.md
  pilot_usability_notes.md
  actionability_review.md
  known_limitations.md
  release_decision.md
```

Triage categories:

- `blocking`: unsafe output, hidden launch blocker, package boundary failure, certification confusion.
- `important`: confusing trigger, weak retest checklist, generic fix plan, unsupported warning.
- `minor`: wording, ordering, examples, optional docs.
- `defer`: maintainer-only improvements that do not affect the Lite user path.

Release notes must include:

- package mode: prompt-only Agent-native Lite package;
- optional Core-powered CLI overlay;
- supported use cases;
- known limitations;
- non-certification boundary;
- safe Agent fix boundary;
- how to report confusing or unsafe outputs.

## 9. Promotion Gates

Promote from RC to controlled external pilot only if:

1. Candidate package generation is reproducible.
2. Source and candidate package verifier pass.
3. Focused Lite tests pass.
4. Expanded validation matrix has no blocker-level failures.
5. External blind usability passes threshold.
6. Actionability review finds no unsafe fix instructions.
7. Release notes state limitations and non-certification boundary.

Promote from controlled pilot to public release only if:

1. At least 3 external pilot users complete the flow.
2. No unresolved blocking pilot feedback remains.
3. At least 5 project shapes are validated.
4. The low-risk case still avoids unsupported `BLOCK`.
5. Host-Agent variance is documented.
6. Known limitations are visible in README or release notes.

Do not promote if:

- any known launch blocker is marked `PASS`;
- any package includes maintainer-only artifacts;
- any user believes the result is certification;
- any fix plan encourages unsafe blind mutation;
- the package cannot be rebuilt from source and manifest.

## 10. First Implementation Order

Recommended next actions:

```text
1. Make package staging reproducible from the manifest.
2. Run verifier against source and candidate package.
3. Expand validation matrix to at least 6 project shapes.
4. Run 3 external blind usability sessions.
5. Review actionability and safety of all fix plans.
6. Write known limitations and RC release notes.
7. Decide controlled pilot / no-go from evidence.
```

Do not start with public marketing or broad release. The evidence supports RC, not GA.

## 11. Adversarial Review

Verdict: pass with strict pilot gates.

This plan is reasonable because it follows the current evidence. The project already has enough proof to justify RC hardening: verifier passes, focused tests pass, CLI smoke exists, four prompt-only cases exist, and usability notes pass. The plan does not waste effort by redoing productization from scratch.

Counterargument: expanding the matrix before external pilot could delay learning from real users.

Response: the matrix expansion should be small and targeted. It prevents obvious misses in high-risk surfaces such as RLS, Firebase rules, Electron/Desktop, and uploads/logging. External pilot should run after this minimum expansion, not after exhaustive calibration.

Counterargument: prompt-only Skill quality cannot be guaranteed across host Agents.

Response: correct. The goal is not deterministic equivalence across all Agents. The goal is to make the package instructions strong enough that common host Agents produce bounded, understandable outputs. Host-Agent variance must be documented as a known limitation.

Counterargument: 3 to 5 external users is too small.

Response: it is too small for broad public release, but appropriate for controlled pilot readiness. A public release should require more project diversity and post-pilot issue triage.

Counterargument: the plan still depends on `test output/` evidence, which is excluded from the Lite package.

Response: that is intentional. Validation evidence is maintainer material and should not enter the user package. The user package stays light; the repository keeps the quality system.

Final recommendation:

```text
Proceed to RC hardening and controlled external pilot preparation.
Do not claim GA readiness until reproducible packaging, expanded matrix,
blind usability, and actionability review all pass.
```
