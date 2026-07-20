# VibeSpec Gate

[简体中文](README.md) | English

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0rc1-orange.svg)](CHANGELOG.md)

**Review vibe-coded products for launch-blocking security risks and turn evidence into bounded, retestable fixes.**

VibeSpec Gate reviews the authorized scope for authentication, authorization, user data, secrets, database rules, deployment configuration, and Agent, MCP, IPC, and Electron permission boundaries. It returns a launch decision, highest-impact risks, bounded repair tasks, and project-specific retests.

Insufficient, incomplete, or truncated evidence cannot produce `PASS` or `PASS_WITH_WARNINGS`: confirmed blocking evidence still produces `BLOCK`; otherwise the result is `REVIEW`. `PASS` means only that no material risk was found within an explicitly stated, complete review scope. It is not proof of security.

> VibeSpec Gate provides decision support. It does not replace a professional penetration test, security certification, legal opinion, or compliance audit.

## Example Output

```text
SYNTHETIC EXAMPLE, NOT A REAL PROJECT REVIEW

Decision: BLOCK
Coverage: partial
Risk: A private orders route does not verify the caller or record owner.
Evidence: app/api/orders/route.ts:18
Human confirmation: Confirm the ownership and administrator-access policy.
Agent task: After confirmation, add server-side identity and owner/tenant checks only.
Retest: User A cannot read or mutate user B's order.
```

A real review first returns these items in chat:

- coverage for all seven evidence surfaces and missing evidence;
- `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, or `PASS`;
- highest-impact risks with file evidence;
- bounded repair tasks that require human confirmation;
- a project-specific retest checklist.

Only after you ask to save results and approve an outside directory does the Agent use the four templates to create `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, `retest_checklist.md`, and `evidence/`.

## What It Reviews

- **Identity and access:** login, signup, password reset, OTP, sessions, tokens, owner, tenant, and admin authorization.
- **Secrets and data:** source credentials, log exposure, client-side data access, database and storage rules, uploads, and data boundaries.
- **Agent and tool authority:** LLM tools, MCP, files, shell, databases, email, payments, and human confirmation gates.
- **Desktop and IPC:** Electron preload, IPC handlers, renderers, filesystem access, and process boundaries.
- **Deployment exposure:** debug endpoints, CORS, cookies, headers, rate limits, abuse controls, and production configuration.

VibeSpec Gate does not silently choose an identity provider, CAPTCHA, MFA, recovery policy, rate-limit threshold, secret rotation, retention policy, or production-account change. It does not run dynamic or live-target tests without authorization.

## Install

The recommended path is to ask `$skill-installer` to install the repository's single Skill unit:

```text
Use $skill-installer to install the Skill from https://github.com/haoran3160-afk/VibeSpec_Gate-skill/tree/master/skills/vibespec-gate.
```

After installation, restart Codex, then open a new Agent task. `$skill-installer` uses `$CODEX_HOME/skills/vibespec-gate` by default, normally `$HOME/.codex/skills/vibespec-gate`. Manual installs may instead use the user-level `$HOME/.agents/skills/vibespec-gate` or repository-level `.agents/skills/vibespec-gate`.

For manual installation, copy the complete `skills/vibespec-gate/` directory, not only `SKILL.md`.

Windows PowerShell:

```powershell
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
Set-Location VibeSpec_Gate-skill
$Target = Join-Path $HOME ".agents/skills/vibespec-gate"
if (Test-Path -LiteralPath $Target) { throw "Target already exists: $Target" }
New-Item -ItemType Directory -Force (Split-Path -Parent $Target) | Out-Null
Copy-Item -LiteralPath "skills/vibespec-gate" -Destination $Target -Recurse
Test-Path -LiteralPath (Join-Path $Target "SKILL.md")
```

macOS or Linux:

```bash
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
cd VibeSpec_Gate-skill
test ! -e "$HOME/.agents/skills/vibespec-gate"
mkdir -p "$HOME/.agents/skills"
cp -R skills/vibespec-gate "$HOME/.agents/skills/vibespec-gate"
test -f "$HOME/.agents/skills/vibespec-gate/SKILL.md"
```

## 60-Second Review

Open a new Agent task in the product repository and enter:

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Keep the project read-only. Start with a chat-only result and do not create files.
Show evidence coverage, the launch decision, the highest-impact risks, repair tasks
that require human confirmation, and a project-specific retest checklist.
```

If you need saved files, separately approve an output directory that does not overlap the project. Review and repair are separate authorizations: receiving a repair plan is not permission for the Agent to modify the project.

## Evidence And Decisions

Every review must cover or explain these seven surfaces: `auth`, `authorization`, `secrets`, `data_rules`, `deployment`, `agent_tools`, and `desktop_ipc`.

| Decision | Meaning |
| --- | --- |
| `BLOCK` | Confirmed launch-blocking evidence exists. Incomplete coverage can still block. |
| `REVIEW` | Evidence is insufficient, partial, truncated, ambiguous, or requires human judgment. |
| `PASS_WITH_WARNINGS` | Coverage is complete and no blocker remains, but a lower-priority or accepted warning remains. |
| `PASS` | Coverage is complete, no surface is missing, and no material risk or remaining warning was found. |

"No findings" alone cannot produce `PASS`; complete coverage with no material risk or remaining warning can. No security score is shown for incomplete coverage.

## Data And Change Boundaries

- Your coding Agent reads project content under the permissions you grant. Whether content leaves your machine depends on that Agent, model provider, and configuration.
- Results are chat-first. Saving reports requires an approved directory outside the project; input and output cannot be equal or contain one another.
- Reports and `evidence/` can contain paths, snippets, and sensitive context. Inspect them manually before sharing.
- Before repairs, confirm the finding, file scope, allowed changes, and prohibited changes again. The Skill does not auto-fix, auto-suppress, or broaden permissions.
- Do not expose complete secrets, OTPs, reset tokens, JWTs, cookies, session IDs, or authorization headers.

## Skill And Optional CLI

| | VibeSpec Gate Skill | Optional CLI |
| --- | --- | --- |
| Purpose | Evidence review, coverage judgment, risk explanation, human confirmation, repair planning, and retesting | Repeatable static checks and structured local evidence |
| Install | Copy `skills/vibespec-gate/` | Install the Python project from source |
| Runtime | A coding Agent with Skill support | Python 3.10+ |
| Default output | Chat | An explicit outside directory |
| Boundary | Does not automatically have CLI scanning capabilities | Does not replace Agent judgment about context and missing evidence |

CLI example from a source checkout:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review D:\path\to\project --output D:\reviews\project-review --no-adapters
```

`--output` is required, must not overlap the project directory, and must not already exist.

## Validation And Boundaries

- CI continuously checks package integrity and supported platforms.
- Review results cover only evidence available in the current task; missing, unreadable, or truncated evidence produces `REVIEW`.
- Read-only review still depends on the Agent environment's permissions and auditable records; the Skill cannot independently prove that the filesystem was never modified.
- Automated checks cannot prove the absence of vulnerabilities or replace professional assessment.

## Project Resources

- [Chinese README](README.md)
- [Documentation index](docs/README.md)
- [Quickstart](docs/usage/lite_quickstart.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

Apache License 2.0. See [LICENSE](LICENSE).
