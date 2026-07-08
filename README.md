# VibeSec Gate

VibeSec Gate is an **LLM-native security review Skill for vibe-coded products**.

Use it when you built a product with AI and need a practical launch answer:

> Can this app leak secrets, expose user data, ship broken auth, or give an Agent/tool too much authority?

VibeSec Gate reviews the project evidence, identifies launch-impacting security and data-safety risks, explains them in plain language, and produces bounded fix tasks that a coding Agent can handle after human confirmation.

## Default Lite Package

The default Lite package is prompt-only and Agent-native. It does not require the Python CLI, repository tests, scorer, calibration data, or release verifier.

Use it like this:

1. Install or copy the Lite package into your Agent environment.
2. Ask the Agent to review your project with `examples/lite_review_prompt.md`.
3. Read the four-file review shape the Agent produces.

Use this starter prompt:

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

Expected output shape:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

The Lite bundle keeps machine-readable evidence under `evidence/`, but first-time users do not need to understand fixtures, scoring matrices, calibration ledgers, or release verification to get a launch decision.

## Optional Core-Powered Path

The full repository also provides a runnable CLI overlay. Use it when you cloned the source repository and want deterministic local evidence generation:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

The CLI is optional repository infrastructure, not a requirement for the default prompt-only Lite package.

## Decision Meanings

- `BLOCK`: do not launch yet; one or more findings currently block launch.
- `REVIEW`: do not treat as launch-ready yet; human confirmation or missing evidence remains.
- `PASS_WITH_WARNINGS`: no launch-blocking finding is present, but warnings or downgrade/suppression candidates need review.
- `PASS`: no material launch risk was found in the reviewed evidence.

## Safe Agent Fix Boundary

`agent_fix_plan.md` is a bounded repair plan, not permission for blind edits.

- Confirm the evidence before asking a coding Agent to change the project.
- Do not auto-write suppressions.
- Do not broaden permissions, remove validation, add bypasses, or mutate production systems while fixing.
- Retest with `retest_checklist.md` after fixes.

VibeSec Gate is not a professional security certification, penetration test, legal review, or compliance attestation.

## When To Use It

VibeSec Gate is useful for:

- AI-built web apps, SaaS products, local tools, and prototypes before sharing or launch;
- projects with authentication, user data, uploads, logs, payments, or deployment secrets;
- Supabase, Firebase, database-rule, object-ownership, and server-side authorization checks;
- AI Agent, MCP/IPC, Electron, desktop, local file, shell, email, database, or payment tool surfaces;
- teams using Codex, Claude, Cursor, Gemini CLI, or similar coding Agents to review and fix generated code.

It focuses on launch-impacting issues such as exposed keys, missing auth, broken authorization, unsafe database rules, risky CORS/cookie/session/header/upload config, prompt or prompt-log exposure, excessive Agent authority, MCP/IPC boundary mistakes, and Electron/Desktop permission issues.

## Powered By The Core Engine

The Lite path is the user-facing surface over a heavier review system. The repository still contains the core engine, schemas, fixtures, tests, quality scoring, calibration workflows, and release verifier used by maintainers to keep reviews repeatable.

Maintainer review outputs include `llm_review_packet.json`, which carries product context and evidence for deeper LLM-native review workflows.

Those internals support quality, but they are not the first user workflow.

## Source Checkout Commands

Install for local development:

```bash
python -m pip install -e .
```

Run the Lite path without installation:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

Use the lower-level CLI when maintaining or debugging the engine:

```bash
vibesec scan ./my-project --output ./outputs
vibesec review ./outputs/findings.json --project ./my-project --output ./outputs-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibesec review-validate ./outputs-review
```

Before a release candidate from the full repository:

```powershell
py -3 scripts\verify_release.py
```

Check the Lite package boundary:

```powershell
py -3 scripts\verify_lite_package.py
```

## Documentation

User path:

- `docs/usage/lite_quickstart.md`
- `examples/lite_review_prompt.md`
- `docs/usage/agent_review_cookbook.md`

Package boundary:

- `docs/design/lite_skill_package_manifest.md`
- `docs/maintainers/lite_package_verification.md`

Maintainer path:

- `docs/usage/quickstart.md`
- `docs/usage/examples.md`
- `docs/usage/verification.md`
- `docs/usage/llm_review_contract.md`
- `docs/maintainers/release_verification.md`
- `docs/maintainers/llm_quality_scoring.md`
- `docs/maintainers/host_agent_calibration.md`
- `docs/maintainers/fixture_authoring.md`
- `docs/maintainers/release_boundary_cleanup.md`
- `docs/design/model_invocation_strategy.md`
