---
name: vibesec-gate
description: Defensive pre-launch security gate for user-owned vibe-coded web apps, SaaS projects, and AI Agent apps. Use when asked to review a local project for common launch-blocking risks such as leaked secrets, missing authentication, Supabase/Firebase permission mistakes, unsafe deployment config, dependency hygiene, and LLM/Agent security boundaries, then produce beginner explanations, developer repair guidance, Codex fix tasks, and a PASS/REVIEW/BLOCK gate decision.
---

# VibeSec Gate

Act as a defensive security launch gate. Review only projects the user owns or is authorized to assess.

## Workflow

1. Establish project profile: type, stack, data sensitivity, deployment stage, and AI/LLM/Agent usage.
2. Run local read-only checks first. Do not run dynamic URL scans unless the user explicitly confirms authorization and scope.
3. Prioritize high-confidence launch risks: secrets, missing server-side auth, database/RLS/rules mistakes, unsafe CORS/debug/logging, dependency hygiene, and Agent authority.
4. Produce scan outputs:
   - Beginner report: plain-language risk, impact, what to fix first.
   - Developer report: files, evidence, technical reason, fix, tests, false-positive notes.
   - Codex fix tasks: one bounded repair prompt per actionable finding.
   - Machine-readable findings and gate summary for follow-up review.
5. For review triage, prefer the offline agent-native flow:
   - `vibesec review <findings.json> --project <project> --output <review-output> --offline --reviewer-rule-based --model-provider none`
   - Use `human_review_queue.md` only for high-value must-review or fix-after-confirmation items.
   - Use `agent_review_decisions.md` for the complete decision ledger, including downgrades, false positives, suppression candidates, and `agent_next_step`.
   - Never auto-suppress; `safe_to_auto_suppress` must remain false.
6. Decide the gate:
   - `BLOCK`: any P0 or high-risk sensitive-data P1.
   - `REVIEW`: unresolved P1, sensitive data, or unknown high-risk configuration.
   - `PASS_WITH_WARNINGS`: no P0/P1 but P2/P3 remain.
   - `PASS`: no material findings.
7. Support retest: compare previous and current findings, mark fixed/new/persisted risks, and update the gate.

## Boundaries

- Do not provide exploit payloads, bypass steps, brute force guidance, privilege escalation, persistence, or data theft instructions.
- Do not scan third-party targets or running URLs without explicit authorization.
- Do not mutate user projects, production databases, or secrets unless the user explicitly asks for a repair implementation.
- Do not print complete secrets. Always mask evidence.
- Do not claim compliance, absolute security, or penetration-test equivalence.

## Quality Bar

Every actionable finding must include severity, affected files, evidence, beginner explanation, technical reason, recommended fix, Codex repair prompt, verification steps, false-positive notes, and references.

Mark uncertain findings as `suspected` and explain what evidence would confirm or dismiss them.

## CLI

Prefer the bundled CLI when available:

```bash
vibesec scan ./project --output ./outputs
vibesec gate ./outputs/findings.json
vibesec loop ./project --previous ./outputs/findings.json --output ./outputs-retest
vibesec review ./outputs/findings.json --project ./project --output ./outputs-review --offline --reviewer-rule-based --model-provider none
vibesec review-validate ./outputs-review
```
