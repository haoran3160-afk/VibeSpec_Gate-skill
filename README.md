# VibeSpec Gate

[English](README.md) | [简体中文](README.zh-CN.md)

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**A launch security review Skill for products built with vibe coding.**

Before shipping, ask your coding Agent to inspect project evidence and answer one practical question:

> Could this product leak secrets, expose user data, ship weak login or authorization, or give an Agent/tool too much authority?

VibeSpec Gate produces a launch decision, the highest-impact risks, scoped repair steps that require human confirmation, and a retest checklist.

<!-- section:capabilities -->
## Core Capabilities

VibeSpec Gate focuses on controls that can change a launch decision, not general code quality:

- **Identity and access:** login, signup, password reset, OTP, session, token, ownership, and admin authorization.
- **Secrets and sensitive data:** exposed credentials, unsafe client-side data access, and weak database or storage rules.
- **Agent and tool authority:** excessive LLM tool, MCP, IPC, Electron, filesystem, shell, database, email, or payment permissions.
- **Deployment exposure:** dangerous production configuration, public debug surfaces, missing rate limits, and insecure defaults.

For each issue, it separates confirmed risks from unanswered questions, requires human confirmation before changes, and produces project-specific retests.

<!-- section:see-it-work -->
## See It Work

VibeSpec Gate runs through your coding Agent. During a review, the Agent creates this bundle under an approved output directory outside the reviewed project:

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
ILLUSTRATIVE EXAMPLE - NOT A REAL SECURITY REVIEW

Decision: BLOCK
Risk: A private orders route does not verify the caller or record owner.
Evidence: app/api/orders/route.ts
Human confirmation: Confirm the intended ownership model.
Agent task: Add server-side auth and constrain reads/writes to the authenticated owner.
Retest: Verify user A cannot read or mutate user B's order.
```

This example is for illustration only. Do not use it as a launch decision, audit result, or evidence that any project is secure. See the [full example](examples/synthetic_review_example.md).

<!-- section:how-it-works -->
## How It Works

```text
project files you authorize
        -> coding Agent review
        -> BLOCK / REVIEW / PASS_WITH_WARNINGS / PASS
        -> human confirmation
        -> scoped repair task
        -> project-specific retest
```

<!-- section:install -->
## Install VibeSpec Gate

Install the entire `vibespec-gate/` directory from the zip in your coding Agent's Skill directory. The Agent reads `vibespec-gate/SKILL.md` when the Skill is invoked.

### Build And Install From Source

Requires Git and Python 3.10 or newer. Python is used to build the zip; the installed Skill does not require Python.

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

The build command should print a `PASS` message. The final check should return `True` on PowerShell or exit successfully on macOS/Linux.

Open a new coding Agent task and check the installation before reviewing code:

```text
Use $vibespec-gate. Without reading a project, state its four launch decisions and
the required confirmation rule before Agent edits, then stop.
```

Expected terms: `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, `PASS`, and `human confirmation`. If they appear, the coding Agent has loaded the Skill instructions.

### Install From GitHub Releases

Open the [Releases page](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases), choose a version, and download both `vibespec-gate-lite.zip` and `SHA256SUMS`. Verify the zip against the checksum before extracting it into your coding Agent's Skill directory.

### Compatibility

| Environment | Installation notes |
| --- | --- |
| Codex | Install `vibespec-gate/` under `$CODEX_HOME/skills`, then open a new task. |
| Coding Agents that support `SKILL.md` | Place `vibespec-gate/` in the Skill location documented by that Agent. |
| Optional CLI | Requires Python 3.10 or newer. |

<!-- section:quick-start -->
## 60-Second Review

Open the product repository in your coding Agent and ask:

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Before writing files, ask me for an approved output directory outside the reviewed
project. Do not default to writing lite_review/ inside the project.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, ownership,
and admin-auth risks. Produce scoped coding-Agent fix tasks only after human
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

<!-- section:data-boundary -->
## Data And Privacy Boundary

- **Coding Agent review:** your coding Agent reads project files under the permissions you grant it. Whether content leaves your machine depends on that Agent, model provider, and configuration. Review those policies before using private code.
- **Local CLI with `--no-adapters`:** repository code reads local files and writes review output to the path you choose. This option does not call an LLM provider or run external scanners.
- **External scanners:** tools such as Semgrep, Gitleaks, Trivy, or ZAP run only when you enable them. Review each tool's network and data-handling behavior before use.
- **Review files:** reports and `evidence/` may contain paths, code excerpts, findings, or sensitive project context. Inspect and sanitize them manually before sharing, even when a report says sensitive values were redacted.

VibeSpec Gate does not silently choose an identity provider, CAPTCHA provider, rate-limit threshold, MFA policy, secret-rotation plan, or production-account change.

<!-- section:safety -->
## Safety Boundary

`agent_fix_plan.md` is a repair plan, not permission for blind edits.

- Confirm each finding, affected file, and allowed scope with a human before mutation.
- Do not automatically hide findings, broaden permissions, remove security checks, or add bypasses.
- Do not print full OTPs, reset tokens, JWTs, cookies, session IDs, authorization headers, or secrets.
- Do not run brute-force, CAPTCHA-bypass, credential-stuffing, phishing, destructive, or unauthorized scans.
- Keep all real-project review output outside the reviewed project.

VibeSpec Gate is not a professional security certification, penetration test, legal review, compliance attestation, or guarantee of absolute security.

<!-- section:optional-cli -->
## Optional CLI

Use the CLI when you want a repeatable command-line review or need results that can be archived and compared. The coding Agent workflow above remains the simplest way to start.

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

<!-- section:project -->
## Project Resources

- [Quickstart](docs/usage/lite_quickstart.md)
- [Review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/usage/agent_review_cookbook.md)
- [Documentation index](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/README.md)
- [Contributing](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CONTRIBUTING.md)
- [Security policy](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/SECURITY.md)
- [Changelog](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CHANGELOG.md)

Apache License 2.0. See [LICENSE](LICENSE).
