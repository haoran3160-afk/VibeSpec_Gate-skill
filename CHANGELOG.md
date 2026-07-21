# Changelog

All notable changes to VibeSpec Gate are documented here.

## Unreleased

## 0.2.0rc2 - 2026-07-20

- Verified five explicit and five negative Skill-routing cases in fresh Codex tasks from the standard user installation.
- Verified eight launch-review behavior cases with canonical decisions, complete chat contracts, host-enforced read-only sandboxes, and unchanged fixture hashes.
- Prevented manifest-only or misclassified projects from receiving complete evidence coverage.
- Made release validation fail closed when Skill activation, prompt, decision, fixture-hash, or write evidence is not independently verifiable.
- Required canonical chat decision tokens and complete seven-surface coverage output from the Skill.
- Added a repeatable black-box runner that isolates non-candidate user Skills and records complete host traces, stderr, final output, Skill-resource reads, write events, and file/directory snapshots.
- Preserved unknown finding severity as fail-closed metadata across gate, review, and Lite bundle paths, and made security-relevant per-file truncation force `REVIEW`.
- Rejected project, findings, previous-findings, and suppression overlap, including hard-linked aliases, across every file-writing CLI path.
- Required affected files and bounded recommended fixes in packaged Skill templates.
- Kept installer and source-copy instructions as the primary installation paths instead of linking an older RC archive.
- Scoped pytest discovery to the maintained test suite so ignored validation artifacts cannot be collected as duplicate tests.
- Bound release readiness to an externally supplied SHA256 for the complete host-evaluation summary; repository records alone remain fail-closed.
- Reconstructed task identity, final Agent output, successful Skill-resource reads, completion state, and no-write traces before accepting black-box evidence.

## 0.2.0rc1 - 2026-07-20

Release-candidate productization update.

- Added evidence coverage states and prevented incomplete, unsupported, unknown, or truncated reviews from passing.
- Rejected every project/output directory overlap and existing output directory before `lite-review` writes files.
- Moved the single installable Skill to `skills/vibespec-gate/` with routed references and output templates.
- Disabled implicit Skill invocation and added fresh-task invocation and behavior evaluation traces.
- Changed the main README to Chinese, added a complete English README, and documented installer and manual Skill locations separately.
- Reworked the GitHub README around evidence, installation, trust boundaries, and a synthetic result example.
- Made the Lite archive directly installable as a single `vibespec-gate/` Skill directory.
- Added Codex UI metadata in `agents/openai.yaml`.
- Added cross-platform CI and a tag-gated GitHub Release workflow.
- Added version, tag, changelog, and archive consistency checks.
- Removed the incomplete `skill/SKILL.md` compatibility entry. This historical release used the repository-root entry; current source uses `skills/vibespec-gate/SKILL.md`.
- Strengthened real-project read-only validation with SHA-256 content snapshots.

## 0.1.0 - 2026-07-09

Initial public pre-release tag. This tag predates the VibeSpec Gate package rename and was not published as a GitHub Release.

- Added the prompt-only Lite Skill package.
- Added the four-file Lite review output: `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, and `retest_checklist.md`.
- Added login-security review coverage for login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks.
- Added the optional Core-powered CLI path for repeatable local evidence generation.
- Added Lite zip packaging with the Apache-2.0 license.
- Added the first GitHub CI and release-candidate verification pass.
