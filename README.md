# VibeSec Gate

VibeSec Gate is a defensive security launch gate for vibe-coded web apps, SaaS projects, and AI Agent prototypes. It reads a local project, runs non-destructive static checks, and generates beginner-friendly reports, developer repair notes, Codex fix tasks, and a launch gate decision.

It is not a penetration testing tool, compliance certificate, legal opinion, or guarantee of absolute security.

## Who It Is For

- AI builders and vibe-coding users preparing to launch a web app.
- Indie developers who want a basic pre-launch security gate.
- Teams that need Codex-ready repair prompts for common issues.

## Who It Is Not For

- Unauthorized scanning of third-party systems.
- Offensive exploit development.
- Formal compliance, legal, or professional penetration-testing replacement.

## What It Checks

- Secret exposure in code, env files, docs, logs, and frontend-like paths.
- Dependency hygiene and selected known risky versions.
- Debug/source-map/logging risks.
- Missing API authentication and possible IDOR/BOLA patterns.
- Supabase RLS and Firebase broad rule risks.
- CORS, cookie flags, and basic security headers.
- LLM/Agent risks such as exposed system prompts, excessive tool authority, sensitive prompt logging, and missing resource limits.

## What It Cannot Guarantee

- It cannot prove a project is fully secure.
- It cannot prove ASVS, OWASP, NIST, or legal compliance.
- It cannot fully understand custom framework middleware or production infrastructure.
- It does not scan running websites by default.

## Safety Boundary

Only scan projects you own or are explicitly authorized to review. VibeSec Gate is read-only by default. It does not generate exploit payloads, bypass login, brute force accounts, mutate production databases, rotate keys, or upload code to unknown third parties. Secret evidence is masked.

## Install

```bash
python -m pip install -e .
```

If an offline or proxied Python environment cannot create the editable install, run without installation:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec scan .\tests\fixtures\vulnerable_next_supabase_app --output .\outputs\example-next
```

## Quick Start

```bash
vibesec scan ./my-project --output ./outputs
vibesec gate ./outputs/findings.json
```

For an AI Agent app:

```bash
vibesec scan ./my-agent --mode ai-agent --output ./outputs-agent
```

## Example Reports

Each scan writes:

```text
outputs/
  vibesec_report_user.md
  vibesec_report_developer.md
  codex_fix_tasks.md
  gate_summary.json
  findings.json
  loop_review.md
```

## External Tools

VibeSec Gate can coexist with mature scanners:

- Gitleaks: deeper secret scanning and git history checks.
- Trivy: dependency, filesystem, container, and IaC checks.
- Semgrep: static code rules.
- OWASP ZAP: dynamic scanning only when explicitly authorized against your own local or staging target.

The MVP does not require these tools. If missing, adapters emit informational status and the built-in scanners still run.

## Codex Repair Flow

1. Run `vibesec scan`.
2. Open `outputs/codex_fix_tasks.md`.
3. Give one task at a time to Codex.
4. After fixes, run:

```bash
vibesec loop ./my-project --previous ./outputs/findings.json --output ./outputs-retest
```

## Agent-Native Review Flow

Use `vibesec review` when scan output needs a second offline triage pass before an agent prepares repairs:

```bash
vibesec review ./outputs/findings.json --project ./my-project --output ./outputs-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibesec review-validate ./outputs-review
```

The review command is deterministic and offline. It writes:

```text
outputs-review/
  review_packets.json
  ai_review.json
  ai_review_summary.md
  human_review_queue.md
  agent_review_decisions.md
  suppression_candidates.json
```

`human_review_queue.md` contains only high-value items that need human confirmation before an agent prepares a fix: `needs_human_review`, `confirmed`, or `likely_true` P0/P1 fix items. Downgrades, suppressions, and false positives are kept out of the human queue and recorded in `agent_review_decisions.md`.

Every AI review verdict includes `agent_next_step`, files to inspect, prohibited changes, verification suggestions, and `safe_to_auto_suppress=false`.

## Common False Positives

- Auth may be enforced in global middleware the scanner cannot see.
- RLS may be enabled in a different migration file.
- Security headers may be set by a reverse proxy or hosting platform.
- Test fixtures may contain fake keys. Real-looking secrets should still be reviewed and rotated if they may have been exposed.

## Disclaimer

VibeSec Gate is a basic pre-launch security gate and remediation assistant. It does not replace professional security review, formal penetration testing, compliance certification, or legal advice.
