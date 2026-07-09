# VibeSpec Gate Lite Skill Productization Plan

Date: 2026-07-08

## 1. Executive Judgment

VibeSpec Gate 的安全判断方向是正确的，但当前工程形态偏重。它更像一个安全评审平台内核，而不是一个轻量 Skill。

核心问题不是能力不足，而是复杂度泄漏：

- 用户只想知道产品能不能上线；
- 维护者需要 schema、fixtures、scorer、calibration、release verifier；
- 现在这些层级在 README、docs、scripts、phase outputs 中同时暴露，导致使用者需要理解过多内部机制。

目标不是删掉复杂系统，而是把复杂系统收进内部，把用户入口变轻。

目标形态：

```text
User-facing Skill:
  Ask: "Can this AI-built product safely launch?"
  Output: launch decision, top risks, bounded fix plan, retest checklist.

Internal engine:
  Evidence collection, review packets, schemas, validators, quality scoring,
  calibration ledgers, host-agent comparison, release verification.
```

## 2. First-Principles Product Requirement

轻量安全 Skill 的第一性原理不是“功能少”，而是“用户必须用最短路径获得安全判断”。

安全判断闭环必须回答五个问题：

1. What is the product and what data does it protect?
2. What can go wrong before launch?
3. Which issues block launch?
4. What should a coding Agent fix, and what must a human confirm first?
5. How do we retest after fixes?

VibeSpec Gate 的内部系统可以继续复杂，但用户第一屏必须只服务这五个问题。

## 3. Current Technical Debt

### 3.1 Boundary Debt

当前系统混合了四类内容：

```text
Skill surface:
  SKILL.md, README.md, quickstart, examples.

Product engine:
  src/, scripts/, schemas, validators, review runner.

Maintainer evidence:
  tests/, fixtures, quality matrix, release verifier.

Research / calibration history:
  test output/phase*, host-agent samples, human calibration ledger.
```

这些内容都合理，但不应该在普通用户路径中同时出现。

Impact:

- 用户无法快速区分“必须运行的命令”和“维护者验证命令”。
- README 解释系统能力多于解释第一步怎么用。
- Phase evidence 容易被误解为产品必需输入。

### 3.2 Concept Debt

当前概念过多：

- finding
- review packet
- LLM packet
- host-agent workspace
- human review queue
- agent decision ledger
- suppression candidates
- quality matrix
- hard failures
- calibration ledger
- host-agent sample matrix

这些概念对工程正确性有价值，但普通用户只需要：

```text
launch decision
top risks
fix plan
retest checklist
```

Impact:

- Skill 看起来像平台文档，不像一个可立即使用的 Agent 技能。
- 用户容易把 deterministic baseline、host-agent review、human calibration 混为一谈。

### 3.3 Artifact Debt

`test output/phase*` 保存了很多研发证据。它们对阶段交付有用，但作为产品仓库会增加噪声。

Impact:

- review 者很难判断哪些文件是产品代码、哪些是历史证据；
- 后续 release diff 会被 historical outputs 淹没；
- 用户可能以为 phase reports 是运行 Skill 的必要路径。

### 3.4 Workflow Debt

当前使用路径偏工程化：

```text
scan -> gate -> review -> review-validate -> build_llm_review_workspace
-> stub/validate -> score -> matrix -> calibration
```

普通用户路径应该是：

```text
review project -> decision -> fix plan -> retest
```

Impact:

- 维护者流程和用户流程没有足够隔离；
- 校准流程容易压过核心产品体验；
- 用户会觉得“为了检查一个项目，我需要理解整个评估系统”。

### 3.5 Positioning Debt

VibeSpec Gate 正确定位是 LLM-native launch security gate。当前文档有时仍会让人感觉它是一个 CLI/scanner 工程。

Impact:

- 与 ReiPenFlow 这类 workflow skill 对比时，VibeSpec Gate 的工程深度强，但第一印象不够轻；
- 用户难以在 30 秒内理解它相对普通 scanner 的价值。

## 4. Product Architecture Target

采用三层架构，不重写内核：

```text
Layer 1: Lite Skill Surface
  - User prompt contract
  - One-command or one-flow quickstart
  - Four primary outputs
  - Human-safe repair guidance

Layer 2: Review Engine
  - Evidence collection
  - Rule findings
  - LLM review packet
  - Agent decision ledger
  - Output validation

Layer 3: Maintainer Quality System
  - Golden/bad fixtures
  - Quality scorer
  - Host-agent calibration
  - Human review ledger
  - Release verification
```

Rule:

```text
Layer 1 may call Layer 2.
Layer 2 may be verified by Layer 3.
Layer 1 must not require users to understand Layer 3.
```

## 5. Lite Skill User Experience

### 5.1 Primary User Prompt

Supported first prompt:

```text
Review this project for launch-blocking security risks.
```

Expected Skill behavior:

1. Identify product type and sensitive assets.
2. Inspect auth, data access, secrets, config, Agent/tool surfaces, and deployment risk.
3. Produce a launch decision.
4. Explain top risks in plain language.
5. Produce bounded Agent repair tasks.
6. Produce retest checklist.

### 5.2 Primary Outputs

Expose four user-facing files:

```text
launch_decision.md
top_security_risks.md
agent_fix_plan.md
retest_checklist.md
```

Internal evidence should remain available, but secondary:

```text
evidence/
  llm_review_packet.json
  agent_review_decisions.json
  human_review_queue.md
  suppression_candidates.json
  raw_findings.json
```

This is a presentation-layer change. Existing outputs can be reused; they do not need to be deleted.

### 5.3 Decision Semantics

Keep the existing launch decision model:

```text
BLOCK
REVIEW
PASS_WITH_WARNINGS
PASS
```

Do not add new decision states unless a real user workflow requires them.

### 5.4 Non-Technical Summary Contract

Every user-facing review must include:

- Can I launch?
- What is the worst realistic thing that can happen?
- Which files or areas are involved?
- What should a human confirm?
- What should an Agent fix first?
- How do we know the fix worked?

## 6. Repository Restructuring Plan

This is a staged plan. Do not do broad moves in one commit.

### Stage 1: Add Lite Facade Without Moving Existing Internals

Add or update:

```text
docs/usage/lite_quickstart.md
examples/lite_review_prompt.md
scripts/build_lite_review_bundle.py
```

`build_lite_review_bundle.py` should read an existing review output and produce:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

Acceptance:

- Existing tests still pass.
- No schema deletion.
- No phase artifact cleanup yet.
- README can point new users to the Lite path.

### Stage 2: Separate User Docs From Maintainer Docs

Create:

```text
docs/usage/
  quickstart.md
  lite_quickstart.md
  examples.md

docs/maintainers/
  release_verification.md
  llm_quality_scoring.md
  host_agent_calibration.md
  fixture_authoring.md
```

Move explanations, not necessarily files, first. Avoid disruptive path changes until links are stable.

Acceptance:

- User docs do not require understanding Phase 8/9/10/11.
- Maintainer docs preserve calibration and release details.

### Stage 3: Artifact Boundary Cleanup

Classify generated evidence:

```text
Product-required:
  src/
  scripts/
  tests/
  docs/
  README.md
  SKILL.md
  pyproject.toml

Maintainer fixtures:
  tests/evaluation_cases/

Generated / historical:
  test output/
  outputs/
```

Recommended action:

- Keep curated fixtures.
- Keep phase reports only when they are evidence for a milestone.
- Do not expose phase outputs in user quickstart.
- Do not delete historical artifacts without a separate cleanup decision.

Acceptance:

- A reviewer can identify product code vs generated evidence in under one minute.

### Stage 4: Optional CLI Facade

Add a user-level command only after Stage 1 proves the output shape:

```powershell
vibesec lite-review <project> --output <out>
```

Internally it can call existing scan/review/build-bundle logic.

Do not build new scan logic for this command. It should be a facade over existing behavior.

Acceptance:

- One command produces the four user-facing files.
- Full evidence remains available under `evidence/`.
- Existing advanced commands continue to work.

## 7. What Not To Do

Do not solve heaviness by deleting the quality system. The scorer, fixtures, hard failures, and calibration plan are valuable maintainability infrastructure.

Do not merge VibeSpec Gate into a ReiPenFlow-style penetration workflow. VibeSpec Gate is a launch-risk gate, not a default exploitation assistant.

Do not expose Phase 11 calibration as a normal user requirement.

Do not add more decision states, output files, or scripts until the Lite path is usable.

Do not move large directories before the user-facing facade is stable.

## 8. Minimal Implementation Slice

The smallest useful next implementation is:

1. Add `docs/usage/lite_quickstart.md`.
2. Add `examples/lite_review_prompt.md`.
3. Add `scripts/build_lite_review_bundle.py`.
4. Add tests for the bundle builder.
5. Update README first screen to mention the Lite path.

Expected bundle builder behavior:

```text
Input:
  existing review output directory

Output:
  lite_review/launch_decision.md
  lite_review/top_security_risks.md
  lite_review/agent_fix_plan.md
  lite_review/retest_checklist.md
  lite_review/evidence/
```

The builder should not call model providers. It should only transform existing local review outputs.

## 9. Quality Gates For The Lite Path

Lite path is acceptable only if:

- It can be explained in three commands or fewer.
- It produces four primary files.
- It does not require reading calibration docs.
- It preserves machine-readable evidence.
- It does not auto-fix, auto-suppress, or mutate reviewed projects.
- It passes existing release verification.

Suggested focused tests:

```powershell
py -3 -m pytest tests/test_lite_review_bundle.py -q -p no:cacheprovider
py -3 -m pytest -q -p no:cacheprovider
py -3 scripts/verify_release.py
```

## 10. Migration Roadmap

### Milestone A: Lite Facade

Outcome:

- New users can run or ask for a launch review without learning internals.

Deliverables:

- Lite quickstart.
- Lite review prompt example.
- Lite bundle builder.
- Bundle builder tests.

### Milestone B: Documentation Split

Outcome:

- User docs and maintainer docs are visibly separate.

Deliverables:

- Maintainer docs for scoring, calibration, and release.
- README shortened and redirected.

### Milestone C: Release Boundary

Outcome:

- Product code, regression fixtures, and historical outputs are easy to review separately.

Deliverables:

- Cleanup proposal.
- Optional `.gitignore` adjustments.
- No destructive cleanup without explicit approval.

### Milestone D: Optional CLI Facade

Outcome:

- `vibesec lite-review` exists as a stable user command.

Deliverables:

- CLI command.
- End-to-end test.
- Updated quickstart.

## 11. Risk Register

| Risk | Why It Matters | Mitigation |
| --- | --- | --- |
| Lite facade hides too much evidence | Security claims become harder to audit | Keep `evidence/` bundle and link to source JSON |
| New CLI duplicates existing review logic | Maintenance cost rises | Build facade over existing commands and data |
| Docs split breaks links | Users lose important guidance | Add redirects or short index pages |
| Phase artifacts are deleted too early | Calibration evidence is lost | Do cleanup only after explicit approval |
| Lite outputs become marketing copy | Security value drops | Keep launch decision tied to concrete evidence and files |

## 12. Design Review And Corrections

This section reviews the plan for common design mistakes.

### Mistake 1: "Make it light" by removing the engine

Rejected. The engine is the moat. The correct move is to hide internal complexity from first-time users, not delete validators, fixtures, or calibration logic.

Correction:

```text
Add a Lite facade. Keep the review engine and maintainer quality system.
```

### Mistake 2: Add a new full workflow engine

Rejected. A new engine would duplicate `scan`, `review`, `review-validate`, and existing schema work.

Correction:

```text
The Lite path must be a presentation and orchestration layer over existing outputs.
```

### Mistake 3: Make Phase 11 a user-facing blocker

Rejected. Phase 11 is maintainer calibration. It is not required for a normal user to get a useful review.

Correction:

```text
User path: project review.
Maintainer path: scorer and host-agent calibration.
```

### Mistake 4: Rename every existing output

Rejected. Existing outputs are already referenced by tests and docs. Broad renaming increases risk.

Correction:

```text
Create user-facing aliases or a bundle. Leave canonical internal files intact.
```

### Mistake 5: Compete directly with penetration-flow skills

Rejected. Penetration workflow and launch gate workflow solve different jobs.

Correction:

```text
VibeSpec Gate should stay centered on safe launch decisions, bounded repair planning, and retest.
```

## 13. Final Recommendation

Do not rewrite VibeSpec Gate.

Do not reduce security depth.

Do build a Lite Skill facade immediately.

The best engineering direction is:

```text
Deep system inside.
Simple launch gate outside.
Maintainer calibration behind the scenes.
```

That preserves the product's strongest differentiator while making it usable as a lightweight Skill.
