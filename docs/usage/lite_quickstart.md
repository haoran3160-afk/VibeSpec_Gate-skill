# Lite Quickstart

Use the Lite path when you want the shortest answer to the launch question:

> Can this AI-built product safely launch?

The Lite path is prompt-only. It asks your coding Agent to review project evidence and write a concise launch review. It does not auto-fix code, auto-write suppressions, call model/provider APIs from repository scripts, or mutate the reviewed project.

## Agent-Native Flow

1. Install or copy the Lite package into your Agent environment.
2. Ask the Agent to review your project with `examples/lite_review_prompt.md`.
3. Read the generated Lite review files in order.

Starter prompt:

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, and admin-auth risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

The review should produce:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

## What To Read First

1. `launch_decision.md`: whether to launch, block, review, or launch with warnings.
2. `top_security_risks.md`: the highest-impact risks and affected files.
3. `agent_fix_plan.md`: bounded tasks a coding Agent can perform after human confirmation.
4. `retest_checklist.md`: checks to rerun after fixes.

## Launch Decision Meanings

- `BLOCK`: do not launch yet; one or more findings currently block launch.
- `REVIEW`: do not treat as launch-ready yet; human confirmation or missing evidence remains.
- `PASS_WITH_WARNINGS`: no launch-blocking finding is present, but warnings remain.
- `PASS`: no material launch risk was found in the reviewed evidence.

## Login-Security Evidence

For products with accounts or private user data, ask the Agent to inspect login, signup, logout, password reset, magic-link, OTP send/verify, verification-code, CAPTCHA or abuse-control, rate-limit, session cookie, JWT, refresh-token, frontend token storage, account-enumeration, and admin-auth evidence.

Use `REVIEW`, not `PASS`, when provider-side login settings, rate limits, CAPTCHA/abuse controls, cookie settings, reset-token expiry, or admin-role evidence is missing from the reviewed files.

Safe retests include checking that unauthenticated private requests are rejected, user A cannot read or mutate user B's data, expired or reused OTP/reset tokens fail, repeated failed verification attempts hit a safe rate-limit path, public reset/signup responses do not reveal account existence, logs omit raw tokens and codes, and non-admin users cannot reach admin routes.

## Safety Boundary

- Do not ask an Agent to edit the project until a human confirms the evidence.
- Do not write suppressions automatically.
- Do not broaden permissions, remove validation, or add bypasses while fixing.
- Do not ask an Agent to choose CAPTCHA providers, rate-limit thresholds, MFA, identity-provider, recovery-policy, or production-account changes without human confirmation.
- Do not print full OTPs, reset tokens, JWTs, cookies, session ids, authorization headers, or secrets.
- Do not treat the Lite bundle as a professional security certification.

## Optional Repository CLI Flow

Use this only from a source checkout when you want repeatable local evidence:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review .\my-project --output .\lite_review --no-adapters
```

This CLI is optional. It is not required for the prompt-only Lite Skill.
