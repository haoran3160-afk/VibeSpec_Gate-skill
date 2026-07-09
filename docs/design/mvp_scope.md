# VibeSpec Gate MVP Scope

> Historical note: this document describes the original CLI/MVP scope. The current product positioning is in `context.md`, `README.md`, and `SKILL.md`: VibeSpec Gate is an LLM-native security review Skill for vibe coding products. The CLI/static checks described here are supporting evidence and regression infrastructure, not the full product ceiling.

## In Scope

- Local static scanning of user-owned project directories.
- Project intake for common web, SaaS, and AI Agent stacks.
- Secret, dependency, configuration, auth/data, deployment, and LLM/Agent checks.
- Optional local adapters for Gitleaks, Trivy, Semgrep, and ZAP status.
- Beginner, developer, Codex repair, gate summary, findings JSON, and loop review outputs.
- Retest loop by comparing current and previous finding sets.
- Fixture projects and automated tests.

## Out of Scope

- Unauthenticated or unapproved URL scanning.
- Exploit generation.
- Active destructive tests.
- Password attacks, bypasses, privilege escalation, or data extraction.
- Guaranteed OWASP/ASVS/NIST compliance.
- SaaS upload integrations.
- Automatic production fixes.

## Completion Criteria

- `vibesec scan <project> --output <dir>` creates all required reports.
- `vibesec gate <findings.json>` prints a gate decision.
- `vibesec loop <project> --previous <findings.json>` creates a comparison report.
- Tests cover intake, secret scanning, auth/data scanning, LLM/Agent scanning, report generation, gate decision, and loop review.
- Reports mask secret values and contain safety boundaries.
