# VibeSpec Gate Lite Review Prompt

Use this prompt with the default prompt-only Lite Skill after confirming that the host Agent is allowed to read the project and that its provider/data policy is acceptable for the code being reviewed.

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Before writing files, ask me for an approved output directory outside the reviewed
project. Do not default to writing lite_review/ inside the project.

Goal:
- Decide whether the project should be BLOCK, REVIEW, PASS_WITH_WARNINGS, or PASS.
- Explain the top security and data-safety risks in plain language.
- Review login, signup, password reset, magic-link, OTP, session, token, rate-limit,
  account-enumeration, ownership, and admin-auth evidence when accounts or private data exist.
- Review secret exposure, database/storage rules, deployment configuration, prompts,
  and Agent/MCP/IPC/Electron/tool authority when those surfaces exist.
- Produce launch_decision.md, top_security_risks.md, agent_fix_plan.md,
  and retest_checklist.md, plus an evidence/ directory.

Constraints:
- Treat this as a prompt-only Agent review. The optional repository overlay is not required.
- Read only files within the authorized project scope.
- Do not mutate the project until a human confirms each finding and allowed scope.
- Keep all review output outside the reviewed project when operating under a read-only boundary.
- If no outside output directory is approved, stop before creating files and ask for one.
- Do not generate exploit payloads, brute-force or CAPTCHA-bypass instructions,
  credential-stuffing, phishing, live OTP interception, persistence, or destructive tests.
- Do not auto-write suppressions, broaden permissions, remove validation, or add bypasses.
- Do not print complete secrets, OTPs, reset tokens, JWTs, cookies, session IDs,
  or authorization headers.
- Mark missing or ambiguous evidence as REVIEW instead of assuming safety.
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

The optional repository CLI flow remains available for local evidence generation, but it is not required for this prompt-only path.

VibeSpec Gate is not a professional security certification, penetration test, legal review, compliance attestation, or guarantee of absolute security.
