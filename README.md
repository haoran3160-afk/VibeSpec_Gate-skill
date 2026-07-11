# VibeSpec Gate

[English](README.md) | [简体中文](README.zh-CN.md)

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![Status: RC](https://img.shields.io/badge/status-0.2.0rc1-orange.svg)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/ROADMAP.md)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**An Agent-native, LLM-native launch security review for products built with vibe coding.**

Before shipping, ask your coding Agent to inspect project evidence and answer one practical question:

> Could this product leak secrets, expose user data, ship weak login or authorization, or give an Agent/tool too much authority?

VibeSpec Gate produces a launch decision, the highest-impact risks, bounded repair tasks that require human confirmation, and a retest checklist.

> **Release-candidate status:** the Skill has deterministic regression coverage and maintainer-authored synthetic walkthroughs, but no completed external blind-user pilot. Synthetic walkthroughs are contract tests, not usability evidence. It is not a professional security certification or penetration test.

<!-- section:see-it-work -->
## See It Work

The default Lite package is prompt-only. Its first review asks the host Agent to create:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

Example decision excerpt:

```text
SYNTHETIC EXAMPLE - NOT A REAL SECURITY REVIEW

Decision: BLOCK
Risk: A private orders route does not verify the caller or record owner.
Evidence: app/api/orders/route.ts
Human confirmation: Confirm the intended ownership model.
Agent task: Add server-side auth and constrain reads/writes to the authenticated owner.
Retest: Verify user A cannot read or mutate user B's order.
```

This example is synthetic. Do not use it as a launch decision, audit result, or evidence that any project is secure. See the [full synthetic example](examples/synthetic_review_example.md).

<!-- section:install -->
## Install The Lite Skill

The installable unit is the single `vibespec-gate/` directory inside the Lite zip. Its entry point is `vibespec-gate/SKILL.md`.

### Build And Install From Source

Requires Git and Python 3.10 or newer. Python is used to build the zip; the installed prompt-only Skill does not require the Python CLI.

Windows PowerShell:

```powershell
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
Set-Location VibeSpec_Gate-skill
py -3 -c "import sys; assert sys.version_info >= (3, 10), sys.version"
py -3 scripts/build_lite_package_zip.py
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$SkillRoot = Join-Path $CodexHome "skills"
New-Item -ItemType Directory -Force $SkillRoot | Out-Null
py -3 -m zipfile -e dist/vibespec-gate-lite.zip $SkillRoot
Test-Path (Join-Path $SkillRoot "vibespec-gate\SKILL.md")
```

macOS or Linux:

```bash
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
cd VibeSpec_Gate-skill
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'
python3 scripts/build_lite_package_zip.py
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
python3 -m zipfile -e dist/vibespec-gate-lite.zip "${CODEX_HOME:-$HOME/.codex}/skills"
test -f "${CODEX_HOME:-$HOME/.codex}/skills/vibespec-gate/SKILL.md"
```

The build command should print `PASS Lite package zip built`. The final check should return `True` on PowerShell or exit successfully on macOS/Linux.

Open a new host task and run this activation smoke before reviewing code:

```text
Use $vibespec-gate. Without reading a project, state its four launch decisions and
the required confirmation rule before Agent edits, then stop.
```

Expected terms: `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, `PASS`, and `human confirmation`. This confirms instruction loading more directly than a file-existence check, but host behavior still depends on the installed Agent.

### Install A Published Release

After a GitHub Release is published, download `vibespec-gate-lite.zip` and verify it against the attached `SHA256SUMS` before extracting it into the host's Skill directory. The tag workflow rebuilds, tests, validates, and attaches both files from the tagged commit.

- [Release page](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases)
- [Latest Lite zip](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/latest/download/vibespec-gate-lite.zip), available after the first RC Release
- [Latest SHA256SUMS](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/latest/download/SHA256SUMS), available after the first RC Release

There is currently no GA release. Do not treat the older `v0.1.0` tag as the renamed `vibespec-gate` package.

### Compatibility

| Host | Current evidence |
| --- | --- |
| Codex Skill directory | Package structure and `agents/openai.yaml` are validated; restart or open a new task after installation. |
| Other hosts that load `SKILL.md` | The prompt contract may be portable, but installation and behavior are not yet claimed as validated. |
| Optional Python CLI | Tested on Python 3.10 and 3.12; CI covers Linux, Windows, and macOS. |

<!-- section:quick-start -->
## 60-Second Review

Open the product repository in your coding Agent and ask:

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Before writing files, ask me for an approved output directory outside the reviewed
project. Do not default to writing lite_review/ inside the project.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, ownership,
and admin-auth risks. Produce bounded coding-Agent fix tasks only after human
confirmation, and produce a project-specific retest checklist.
```

Read the generated files in this order:

1. `launch_decision.md`: whether the project is blocked, needs review, or has no identified blocker.
2. `top_security_risks.md`: evidence and launch impact for the highest-priority risks.
3. `agent_fix_plan.md`: narrow repair tasks that still require human confirmation.
4. `retest_checklist.md`: checks to run after a confirmed fix.

Decision meanings:

- `BLOCK`: do not launch yet; reviewed evidence shows a launch blocker.
- `REVIEW`: missing or ambiguous evidence requires human review.
- `PASS_WITH_WARNINGS`: no blocker was identified, but warnings remain.
- `PASS`: no material launch blocker was identified in the reviewed evidence.

`PASS` is not proof that a product is secure.

<!-- section:how-it-works -->
## How It Works

```text
authorized project evidence
        -> host Agent review
        -> BLOCK / REVIEW / PASS_WITH_WARNINGS / PASS
        -> human confirmation
        -> bounded Agent repair task
        -> project-specific retest
```

The Skill prioritizes leaked secrets, login and session weaknesses, missing server-side authentication, broken ownership checks, unsafe database or storage rules, dangerous deployment settings, exposed prompts, and excessive Agent/MCP/IPC/Electron/tool authority.

<!-- section:data-boundary -->
## Data And Privacy Boundary

- **Prompt-only mode:** the current host Agent reads project files under the permissions you grant it. Whether content leaves your machine depends on that host, model provider, and configuration. Review those policies before using private code.
- **Local CLI with `--no-adapters`:** repository code reads local files and writes review output to the path you choose. It does not call an LLM provider or enable external scanner adapters.
- **Optional adapters:** installed tools such as Semgrep, Gitleaks, Trivy, or ZAP run only when enabled. Their own network and data-handling behavior is outside this Skill's guarantee.
- **Generated evidence:** reports and `evidence/` may contain paths, snippets, findings, or sensitive project context. Inspect and sanitize them manually before sharing. A `redacted` field is not a guarantee that every sensitive value was removed.

VibeSpec Gate does not silently choose an identity provider, CAPTCHA provider, rate-limit threshold, MFA policy, secret-rotation plan, or production-account change.

<!-- section:safety -->
## Safety Boundary

`agent_fix_plan.md` is a repair plan, not permission for blind edits.

- Confirm each finding, affected file, and allowed scope with a human before mutation.
- Do not auto-write suppressions, broaden permissions, remove validation, or add bypasses.
- Do not print full OTPs, reset tokens, JWTs, cookies, session IDs, authorization headers, or secrets.
- Do not run brute-force, CAPTCHA-bypass, credential-stuffing, phishing, destructive, or unauthorized scans.
- Keep all real-project review output outside the reviewed project.

VibeSpec Gate is not a professional security certification, penetration test, legal review, compliance attestation, or guarantee of absolute security.

<!-- section:optional-cli -->
## Optional Core-Powered CLI

The CLI is supporting evidence and regression infrastructure, not the default Skill experience.

When deeper review evidence exists, `llm_review_packet.json` is the structured handoff packet for host-Agent reasoning. It can contain sensitive project context and requires the same sharing review as other evidence.

```bash
python -m pip install -e .
vibespec-gate lite-review ./my-project --output ./lite_review --no-adapters
```

For a source checkout without installation:

```bash
PYTHONPATH=src python -m vibespec_gate.cli lite-review ./my-project --output ./lite_review --no-adapters
```

PowerShell equivalent:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review .\my-project --output .\lite_review --no-adapters
```

<!-- section:validation -->
## Validation And Maturity

- Full tests, package verification, archive validation, and version checks run in CI.
- Release tags rerun the full test and package gates before publishing an asset.
- Maintainer hardening uses deterministic fixtures, explicitly labeled synthetic walkthroughs, and authorized project checks with before/after source-file integrity comparison.
- Real external blind-user evidence is still pending; synthetic walkthroughs are not described as Agent or participant sessions.

See the [roadmap](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/ROADMAP.md) for the current maturity boundary.

<!-- section:project -->
## Project Resources

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/usage/agent_review_cookbook.md)
- [Documentation index](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/README.md)
- [Contributing](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CONTRIBUTING.md)
- [Security policy](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/SECURITY.md)
- [Changelog](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CHANGELOG.md)

Apache License 2.0. See [LICENSE](LICENSE).
