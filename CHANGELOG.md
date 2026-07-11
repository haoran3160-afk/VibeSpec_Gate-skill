# Changelog

All notable changes to VibeSpec Gate are documented here.

## 0.2.0rc1 - 2026-07-11

Release-candidate productization update.

- Reworked the GitHub README around evidence, installation, trust boundaries, and a synthetic result example.
- Made the Lite archive directly installable as a single `vibespec-gate/` Skill directory.
- Added Codex UI metadata in `agents/openai.yaml`.
- Added cross-platform CI and a tag-gated GitHub Release workflow.
- Added version, tag, changelog, and archive consistency checks.
- Removed the incomplete `skill/SKILL.md` compatibility entry; install the repository-root `SKILL.md` or the Lite archive instead.
- Strengthened real-project read-only validation with SHA-256 content snapshots.

## 0.1.0 - 2026-07-09

Initial public pre-release tag. This tag predates the VibeSpec Gate package rename and was not published as a GitHub Release.

- Added the prompt-only Lite Skill package.
- Added the four-file Lite review output: `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, and `retest_checklist.md`.
- Added login-security review coverage for login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks.
- Added the optional Core-powered CLI path for repeatable local evidence generation.
- Added Lite zip packaging with the Apache-2.0 license.
- Added the first GitHub CI and release-candidate verification pass.
