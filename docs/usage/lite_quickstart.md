# Lite Quickstart

Use the default prompt-only, Agent-native flow when you want a launch-risk review without installing the optional Python CLI.

## Install

The Lite archive contains one installable directory: `vibespec-gate/`. The entry point is `vibespec-gate/SKILL.md`.

From a source checkout on Windows PowerShell:

```powershell
py -3 -c "import sys; assert sys.version_info >= (3, 10), sys.version"
py -3 scripts/build_lite_package_zip.py
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$SkillRoot = Join-Path $CodexHome "skills"
New-Item -ItemType Directory -Force $SkillRoot | Out-Null
py -3 -m zipfile -e dist/vibespec-gate-lite.zip $SkillRoot
Test-Path (Join-Path $SkillRoot "vibespec-gate\SKILL.md")
```

From a source checkout on macOS or Linux:

```bash
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'
python3 scripts/build_lite_package_zip.py
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
python3 -m zipfile -e dist/vibespec-gate-lite.zip "${CODEX_HOME:-$HOME/.codex}/skills"
test -f "${CODEX_HOME:-$HOME/.codex}/skills/vibespec-gate/SKILL.md"
```

Expected build output: `PASS Lite package zip built`. Restart the host or open a new task after installation, then ask `$vibespec-gate` to state `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, `PASS`, and the `human confirmation` rule without reading a project. Other hosts may load the same `SKILL.md` contract, but their installation and behavior are not yet claimed as validated.

## Agent-Native Flow

Open the product repository in the host Agent and ask:

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Before writing files, ask me for an approved output directory outside the reviewed
project. Do not default to writing lite_review/ inside the project.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, ownership,
and admin-auth risks. Produce bounded coding-Agent fix tasks only after human
confirmation, and produce a project-specific retest checklist.
```

The Agent should produce:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

Read the files in that order.

## Launch Decision Meanings

- `BLOCK`: do not launch yet; reviewed evidence shows a launch blocker.
- `REVIEW`: missing or ambiguous evidence requires human review.
- `PASS_WITH_WARNINGS`: no blocker was identified, but warnings remain.
- `PASS`: no material launch blocker was identified in reviewed evidence.

`PASS` is not proof that a product is secure.

## Login-Security Evidence

For products with accounts or private data, inspect login, signup, logout, password reset, magic-link, OTP send/verify, CAPTCHA or abuse controls, rate limits, session cookies, JWT and refresh-token handling, frontend token storage, account enumeration, ownership checks, and admin authorization.

Use `REVIEW`, not `PASS`, when provider-side settings, rate limits, cookie settings, reset-token expiry, admin-role evidence, or equivalent controls are absent from reviewed files.

Safe retests include rejecting unauthenticated private requests, preventing user A from accessing user B's data, rejecting expired or reused reset/OTP tokens, exercising a safe rate-limit path, preventing account enumeration, omitting raw auth artifacts from logs, and rejecting non-admin users from admin routes.

## Data Boundary

- In prompt-only mode, the host Agent reads project content under its configured permissions and provider policy. Check that policy before using private code.
- `vibespec-gate lite-review ... --no-adapters` reads local files, writes to the selected output directory, does not call an LLM provider, and does not execute optional scanner adapters.
- Enabled adapters run installed third-party tools whose own data handling is outside this Skill's guarantee.
- Generated reports and `evidence/` may contain paths, snippets, or sensitive context. Inspect and sanitize them manually before sharing; a `redacted` field is not a complete sanitization guarantee.

## Safety Boundary

- Do not edit a reviewed project until a human confirms the evidence and scope.
- Do not auto-write suppressions, broaden permissions, remove validation, or add bypasses.
- Do not ask an Agent to choose CAPTCHA providers, rate-limit thresholds, MFA policy, identity providers, recovery policy, or production-account changes without human confirmation.
- Do not print full OTPs, reset tokens, JWTs, cookies, session IDs, authorization headers, or secrets.
- Keep review output outside every real project used for read-only validation.
- If an external output directory has not been approved, stop before creating the Lite files and ask for one.

VibeSpec Gate is not a professional security certification, penetration test, legal review, compliance attestation, or guarantee of absolute security.

## Optional Repository CLI Flow

Install from a source checkout when repeatable local evidence is useful:

```bash
python -m pip install -e .
vibespec-gate lite-review ./my-project --output ./lite_review --no-adapters
```

Without installation on macOS/Linux:

```bash
PYTHONPATH=src python -m vibespec_gate.cli lite-review ./my-project --output ./lite_review --no-adapters
```

Without installation on PowerShell:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review .\my-project --output .\lite_review --no-adapters
```

This optional Core-powered path is supporting infrastructure. It is not required for the default Lite package.
