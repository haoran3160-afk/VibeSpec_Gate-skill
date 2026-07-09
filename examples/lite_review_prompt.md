# Lite Review Prompt

Use this prompt when asking a coding Agent to run the prompt-only Lite VibeSpec Gate flow.

```text
Review this project for launch-blocking security risks.

Goal:
- Tell me whether this AI-built product can safely launch.
- Explain the top security and data-safety risks in plain language.
- Review login, signup, password reset, OTP/magic-link, session, token, account-enumeration, rate-limit/CAPTCHA, and admin-auth evidence when present.
- Produce bounded coding-Agent fix tasks after human confirmation.
- Produce a retest checklist.

Constraints:
- Do not auto-fix code.
- Do not auto-write suppressions.
- Do not call external model/provider APIs from repository scripts.
- Do not mutate the reviewed project unless I explicitly approve a fix task.
- Do not provide brute-force, CAPTCHA-bypass, credential-stuffing, phishing, live OTP interception, or exploit instructions.
- Do not print full OTPs, reset tokens, JWTs, cookies, session ids, authorization headers, or secrets.

Preferred output shape:
- launch_decision.md
- top_security_risks.md
- agent_fix_plan.md
- retest_checklist.md
- evidence/ for machine-readable review data

Decision meanings:
- BLOCK: do not launch yet.
- REVIEW: human confirmation or missing evidence remains.
- PASS_WITH_WARNINGS: no launch blocker is present, but warnings remain.
- PASS: no material launch risk was found in the reviewed evidence.
```

Optional repository overlay:

If you cloned the full source repository and want repeatable local evidence, build the Lite bundle with:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review .\my-project --output .\lite_review --no-adapters
```
