# VibeSpec Gate

[中文](README.md) | [English](README.en.md)

**A launch gate for products built with vibe coding.**

AI helped you build it. Can it actually go live?

VibeSpec Gate asks your coding Agent to answer the launch-risk question first:

> Could this leak secrets, expose user data, break login/permissions, or give an Agent/tool too much authority?

It then produces a launch decision, top risks, bounded Agent fix tasks, and a retest checklist.

## What You Get

VibeSpec Gate produces four primary files:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

Read them in this order:

1. `launch_decision.md`: whether the product can launch.
2. `top_security_risks.md`: the highest-impact risks and affected evidence.
3. `agent_fix_plan.md`: bounded fix tasks for a coding Agent after human confirmation.
4. `retest_checklist.md`: safe checks to run after fixes.

Decision meanings:

- `BLOCK`: do not launch yet; fix this first.
- `REVIEW`: do not assume it is safe; a human needs to confirm something.
- `PASS_WITH_WARNINGS`: no launch blocker was found, but warnings remain.
- `PASS`: no launch-blocking risk was found in the reviewed evidence.

## Quick Start

Use the prompt-only Lite flow first. It is the default Lite package path.

1. Copy or install this Skill into your Agent environment.
2. Open your product in that Agent.
3. Paste this prompt:

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

## What It Reviews

VibeSpec Gate focuses on launch-impacting problems:

- leaked secrets, API keys, service-role keys, database URLs, and credentials;
- login, signup, password reset, OTP, magic-link, session, token, account-enumeration, rate-limit, and admin-auth mistakes;
- missing login checks or broken user-data ownership checks;
- overly open Supabase, Firebase, storage, or database rules;
- risky CORS, cookie, session, header, upload, logging, and deployment config;
- prompt or prompt-log exposure;
- excessive Agent/tool authority, including MCP/IPC, Electron, shell, local files, email, database, and payment tools;
- missing evidence that should be confirmed before launch.

## Safety Boundary

`agent_fix_plan.md` is a repair plan, not permission for unapproved edits.

Before asking a coding Agent to change the project:

- confirm the finding is real;
- confirm the files and scope;
- do not auto-write suppressions;
- do not broaden permissions, remove validation, or add bypasses;
- do not let an Agent choose CAPTCHA providers, rate-limit thresholds, MFA policy, identity providers, recovery policy, or production account changes without human confirmation;
- do not print full OTPs, reset tokens, JWTs, cookies, session ids, authorization headers, or secrets.

VibeSpec Gate is not a professional security certification, penetration test, legal review, or compliance attestation.

## Default Lite Package

The default Lite package is prompt-only. A first-time user only needs the Skill instructions and a coding Agent.

## Optional Core-Powered Path

The optional Core-powered path is available from a source checkout when you want repeatable local evidence:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

The CLI is optional. It is not required for the prompt-only Lite Skill.

When deeper evidence is available, `llm_review_packet.json` is the LLM-native handoff packet for model-assisted review workflows.

## Documentation

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Lite review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](docs/usage/agent_review_cookbook.md)
- [Changelog](CHANGELOG.md)

## Build The Lite Zip

```powershell
py -3 scripts\build_lite_package_zip.py
```

The zip contains the prompt-only Lite package files and the Apache-2.0 license.

## License

Apache License 2.0. See [LICENSE](LICENSE).

The license controls reuse and distribution rights. It does not make VibeSpec Gate a professional security certification, penetration test, legal review, or compliance attestation.
