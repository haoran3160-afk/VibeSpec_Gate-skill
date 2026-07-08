# VibeSec Gate Design Review and Optimization

Date: 2026-07-06

> Historical note: this document reviewed the original MVP/CLI design. The current product positioning is broader: VibeSec Gate is an LLM-native security review Skill for vibe-coded products. Treat references to local static scanning as implementation baseline and evidence collection, not as the full product identity.

## 1. Fit with OWASP, NIST, and DevSecOps Practice

The original design aligns well with OWASP Top 10, OWASP API Security Top 10, OWASP ASVS, OWASP LLM/GenAI Top 10, and NIST SSDF in broad scope:

- OWASP Top 10 maps to secrets, access control, injection-prone code, misconfiguration, vulnerable components, and logging/privacy findings.
- OWASP API Security maps to BOLA/IDOR, missing authentication, excessive data exposure, unrestricted resource consumption, and unsafe admin APIs.
- OWASP ASVS is appropriate as a checklist source, but the MVP must not claim ASVS verification.
- OWASP LLM/GenAI maps to prompt injection, sensitive information disclosure, excessive agency, tool-call governance, and resource limits.
- NIST SSDF supports the repair-loop framing: identify, remediate, retest, and document.

## 2. Scope Assessment

The design is useful but too large if interpreted as a full security scanner. The MVP must narrow itself to:

- Local static repository inspection.
- Optional local tool adapters with graceful degradation.
- High-confidence checks for common vibe-coding mistakes.
- Reports, repair prompts, and retest loop output.

The MVP must not attempt full semantic proof of authorization, formal compliance, exploit validation, or broad DAST.

## 3. First-Version Modules

Build now:

- Project intake and risk profile.
- Unified finding schema and gate decision.
- Secret, dependency, config, auth/data, deployment, and LLM/Agent scanners.
- External adapters for Gitleaks, Trivy, Semgrep, and a disabled-by-default ZAP adapter.
- Markdown and JSON report generation.
- Three fixture projects and tests.

Delay:

- CodeQL database generation.
- Full OWASP ZAP scan execution.
- SaaS integrations with Snyk, GitGuardian, Socket, Aikido, or GitHub APIs.
- Git history rewrite, secret rotation, production DB changes, and auto-fix mode.
- Rich web UI and repository history dashboards.

## 4. Open Source Tool Reuse

- Gitleaks: preferred local secret scanner. If missing, use built-in regex fallback.
- Trivy: preferred filesystem/container/IaC scanner. If missing, warn and continue.
- Semgrep: preferred configurable SAST engine. If missing, built-in scanner handles only MVP heuristics.
- ZAP: optional adapter only; no default active scanning.
- npm/pnpm/pip-audit/Safety: recommended in docs; not auto-run unless user opts in.

## 5. Manual-Review Only Checks

The MVP cannot reliably prove:

- Whether every authorization path is correct.
- Whether every RLS/Firebase rule enforces the intended business ownership model.
- Whether LLM prompts are robust against all prompt injection variants.
- Whether source maps are publicly reachable in production.
- Whether production observability, incident response, and compliance requirements are adequate.
- Whether payment, medical, financial, enterprise, minor, or sensitive identity data handling is legally sufficient.

These must be reported as `UNKNOWN_REQUIRES_REVIEW` or manual checklist items.

## 6. Prohibited or Boundary-Risk Checks

The MVP must prohibit:

- Unauthorized third-party scanning.
- Exploit generation or payload construction.
- Password guessing, bypassing login, privilege escalation, data theft, or destructive testing.
- Automatic production database changes.
- Automatic key deletion, upload, or rotation.
- Dynamic URL scanning unless the user explicitly confirms authorization and scope.

## 7. Final MVP Boundary

VibeSec Gate MVP is a Python CLI plus Codex Skill instructions that:

- Reads a local project folder.
- Builds a project risk profile.
- Runs safe static scanners and optional local adapters.
- Emits unified findings.
- Generates beginner, developer, Codex repair, gate summary, and loop review outputs.
- Fails closed on unknown high-risk conditions by asking for review.

## 8. Non-Goals

- Not a professional penetration test.
- Not a legal or compliance certification.
- Not a vulnerability exploit framework.
- Not a replacement for an AppSec engineer on regulated/high-impact launches.
- Not a hosted SaaS or cloud scanning product.
- Not an auto-remediation tool for production data or secrets.

## 9. Technical Architecture

- Language: Python 3.10+ with standard library only for the MVP.
- CLI entry: `vibesec`.
- Core layers:
  - `project_intake`: file inventory and project profile.
  - `risk_model`: finding schema and severity normalization.
  - `gate_decision`: launch decision.
  - `report_builder`: Markdown and JSON outputs.
  - `loop_runner`: rescan and comparison.
- Scanners:
  - `secret_scanner`
  - `dependency_scanner`
  - `config_scanner`
  - `auth_data_scanner`
  - `deployment_scanner`
  - `llm_agent_scanner`
- Adapters:
  - Gitleaks, Trivy, Semgrep, ZAP.

## 10. Final File Structure

```text
README.md
SKILL.md
pyproject.toml
docs/
  research/research_notes.md
  design/design_review_and_optimization.md
  design/threat_model.md
  design/mvp_scope.md
  usage/quickstart.md
  usage/examples.md
skill/
  SKILL.md
  checklists/*.md
  templates/*.md
  rules/risk_scoring.yaml
src/vibesec/
  cli.py
  core/*.py
  scanners/*.py
  adapters/*.py
  rules/*.yaml
  templates/*.j2
tests/
  fixtures/*
  test_*.py
outputs/
```

## 11. Quality Gate

Before completion:

- All tests pass.
- Example fixture scan produces all required output files.
- Reports do not contain full secret values.
- No dynamic scan runs by default.
- Missing external tools do not crash the CLI.
- Loop review documents security, product, and engineering review.
- README includes setup, usage, boundaries, false positives, and disclaimer.
