# VibeSpec_Gate-skill

[English](README.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Package mode](https://img.shields.io/badge/package-prompt--only%20Skill-green)](#default-lite-package)
[![Security boundary](https://img.shields.io/badge/security-not%20a%20certification-orange)](#safety-boundary)

**A launch safety check for vibe-coded products.**

If you built a site, SaaS app, internal tool, Agent, or desktop app with Cursor, Claude Code, Codex, Lovable, Bolt, v0, Replit, or any other vibe coding workflow, VibeSpec_Gate-skill helps answer the question that is hard to judge before launch:

> Can this product go live, or is there a security or data-safety problem I should fix first?

It is made for builders who are not security experts. You do not need to know security jargon to use it.

It is an LLM-native Skill: your coding Agent reads the instructions, reviews the project, and writes the four review files for you.

## What It Gives You

VibeSpec_Gate-skill asks your coding Agent to look through the project and produce four simple files:

```text
lite_review/
  launch_decision.md       # Can I launch?
  top_security_risks.md    # What could hurt users or the product?
  agent_fix_plan.md        # What can a coding Agent fix after I confirm it?
  retest_checklist.md      # How do I check the fix worked?
  evidence/                # Supporting details for deeper review
```

The most important file is `launch_decision.md`.

It uses four plain decisions:

- `BLOCK`: do not launch yet; fix this first.
- `REVIEW`: do not assume it is safe; a human needs to confirm something.
- `PASS_WITH_WARNINGS`: no launch blocker was found, but warnings remain.
- `PASS`: no launch-blocking risk was found in the reviewed evidence.

## Why This Exists

Vibe coding makes it easy to ship a real product before you fully understand what the generated code is doing.

Common launch risks include:

- a secret key or database URL accidentally committed to the project;
- a private page or API that can be opened without login;
- user A being able to read user B's data;
- signup, password reset, OTP, magic-link, session, token, rate-limit, or admin login mistakes;
- logs that print raw tokens, cookies, reset links, or one-time codes;
- database or storage rules that are too open;
- an Agent, MCP tool, Electron app, shell command, file tool, email tool, database tool, or payment tool with too much power.

VibeSpec_Gate-skill turns those risks into a launch decision, a short risk explanation, a bounded fix plan, and a retest checklist.

## Quick Start

Use the prompt-only Lite flow first. It is the default path.

1. Copy or install this Skill into your Agent environment.
2. Open your vibe-coded product in that Agent.
3. Paste this prompt:

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

Then read:

```text
lite_review/launch_decision.md
lite_review/top_security_risks.md
lite_review/agent_fix_plan.md
lite_review/retest_checklist.md
```

## Example Result

```text
Decision: BLOCK

Why:
The password reset route appears to accept reset tokens without expiry or single-use checks.
If a reset link leaks, someone may reuse it later to take over an account.

First safe fix:
Ask a coding Agent to add reset-token expiry and single-use enforcement,
after you confirm the intended account recovery policy.

Retest:
Confirm expired and already-used reset tokens are rejected.
```

This is the kind of output the Skill is designed to produce: short, practical, and tied to launch risk.

## Default Lite Package

The default Lite package is **prompt-only**. A first-time user should not need to install this Python project, run repository tests, understand internal scoring, read calibration notes, or use release tooling.

The full repository contains a deeper engine for maintainers and advanced users, but the first user path stays lightweight:

```text
copy Skill -> ask Agent to review project -> read four files -> fix/retest
```

## What It Reviews

VibeSpec_Gate-skill focuses on launch-impacting problems that vibe coding users commonly miss:

- secrets, API keys, service-role keys, database URLs, and credentials;
- login, signup, password reset, OTP, magic-link, session, token, account-enumeration, rate-limit, and admin-auth mistakes;
- missing login checks or broken user-data ownership checks;
- overly open Supabase, Firebase, storage, or database rules;
- risky CORS, cookie, session, header, upload, logging, and deployment config;
- prompt or prompt-log exposure;
- excessive Agent/tool authority, including MCP/IPC, Electron, shell, local files, email, database, and payment tools;
- missing evidence that should be confirmed before launch.

## Safety Boundary

`agent_fix_plan.md` is a repair plan, not permission for blind edits.

Before asking a coding Agent to change the project:

- confirm the finding is real;
- confirm the files and scope;
- do not auto-write suppressions;
- do not broaden permissions, remove validation, or add bypasses;
- do not let an Agent choose CAPTCHA providers, rate-limit thresholds, MFA policy, identity providers, recovery policy, or production account changes without human confirmation;
- do not print full OTPs, reset tokens, JWTs, cookies, session ids, authorization headers, or secrets.

VibeSpec_Gate-skill is not a professional security certification, penetration test, legal review, or compliance attestation.

## Optional Core-Powered Path

If you cloned the full repository and want more repeatable local evidence, you can run the optional Core-powered Python CLI:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

This CLI is an optional evidence engine. It is not required for the prompt-only Lite Skill.
When deeper review evidence is available, `llm_review_packet.json` is the LLM-native handoff packet for model-assisted review workflows.

## Which Path Should I Use?

| You are... | Start here |
| --- | --- |
| A vibe coding builder who wants to know if a product can launch | `examples/lite_review_prompt.md` |
| A user who wants step-by-step usage | `docs/usage/lite_quickstart.md` |
| A developer who cloned the full repo | Optional CLI path above |
| A maintainer validating package quality | `scripts/verify_lite_package.py` and `scripts/verify_release.py` |

## Documentation

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Lite review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](docs/usage/agent_review_cookbook.md)
- [Documentation index](docs/README.md)

Maintainer references:

- [Lite package manifest](docs/design/lite_skill_package_manifest.md)
- [Lite package verification](docs/maintainers/lite_package_verification.md)
- [Release verification](docs/maintainers/release_verification.md)

## Local Development

Install from a source checkout:

```bash
python -m pip install -e .
```

Verify the Lite package boundary:

```powershell
py -3 scripts\verify_lite_package.py
```

Build the prompt-only Lite zip:

```powershell
py -3 scripts\build_lite_package_zip.py
```

Run focused tests:

```powershell
py -3 -m pytest tests/test_lite_package_verifier.py tests/test_lite_release_validation.py tests/test_lite_review_bundle.py tests/test_lite_rc_hardening.py
```

Generated folders such as `outputs/` and `test output/` are intentionally ignored by Git.

## Governance

- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## License

No open-source license has been selected yet. Until a `LICENSE` file is added, do not assume reuse, redistribution, or relicensing rights.
