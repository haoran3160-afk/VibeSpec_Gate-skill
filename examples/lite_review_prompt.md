# VibeSpec Gate Lite Review Prompt

Use this prompt after confirming that your coding Agent may read the project and that its provider and data policy are acceptable for the code being reviewed.

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Keep the project read-only. Start with a chat-only result and do not create files.

Goal:
- Decide whether the project should be BLOCK, REVIEW, PASS_WITH_WARNINGS, or PASS.
- Explain the top security and data-safety risks in plain language.
- Review login, signup, password reset, magic-link, OTP, session, token, rate-limit,
  account-enumeration, ownership, and admin-auth evidence when accounts or private data exist.
- Review secret exposure, database/storage rules, deployment configuration, prompts,
  and Agent/MCP/IPC/Electron/tool authority when those surfaces exist.
- Report all seven coverage surfaces and every missing, unreadable, or truncated area.
- Produce bounded repair tasks and a project-specific retest checklist in chat.

Constraints:
- Read only files within the authorized project scope.
- Do not mutate the project until a human confirms each finding and allowed scope.
- If I later ask to save results, require an approved output directory outside the project
  before creating launch_decision.md, top_security_risks.md, agent_fix_plan.md,
  retest_checklist.md, or evidence/.
- Do not generate exploit payloads, brute-force or CAPTCHA-bypass instructions,
  credential-stuffing, phishing, live OTP interception, persistence, or destructive tests.
- Do not auto-write suppressions, broaden permissions, remove validation, or add bypasses.
- Do not print complete secrets, OTPs, reset tokens, JWTs, cookies, session IDs,
  or authorization headers.
- Missing or ambiguous evidence prevents PASS and PASS_WITH_WARNINGS: use BLOCK when confirmed blocking evidence exists, otherwise REVIEW.
- Do not describe PASS as proof of security or as professional certification.
- Treat generated reports and evidence as potentially sensitive. Do not claim they are
  safe to share merely because a field says redacted; require manual inspection first.

For every actionable finding include:
- severity and launch impact;
- affected files and evidence;
- beginner explanation and technical reason;
- recommended fix;
- bounded Agent task;
- prohibited changes;
- verification steps;
- confidence and missing evidence.
```

The optional repository CLI remains available for repeatable static checks and structured local evidence. It is not included in the installed Skill.

VibeSpec Gate is not a professional security certification, penetration test, legal review, compliance attestation, or guarantee of absolute security.
