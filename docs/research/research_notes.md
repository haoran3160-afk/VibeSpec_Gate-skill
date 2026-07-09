# VibeSpec Gate Research Notes

Date: 2026-07-06

> Historical note: these notes informed the original MVP. The current product positioning is in `context.md`, `README.md`, and `SKILL.md`: VibeSpec Gate is an LLM-native security review Skill for vibe-coded products. Local tools and rule-based checks are supporting evidence sources, not the product's ceiling.

VibeSpec Gate should be a defensive launch gate and repair assistant, not a penetration testing tool. The MVP should orchestrate local static checks, normalize findings, explain them for non-specialists, and produce repair and retest tasks.

## Official Standards

| Source | Version / Date | Relevant conclusion for this MVP |
|---|---:|---|
| OWASP Top 10 | 2025 current release, OWASP project page: https://owasp.org/Top10/2025/en/ and https://owasp.org/www-project-top-ten/ | Use as the top-level web risk vocabulary. Broken access control, injection, misconfiguration, vulnerable components, and auth failures map directly to VibeSpec scanner categories. |
| OWASP ASVS | 5.0.0, released May 2025: https://owasp.org/www-project-application-security-verification-standard/ and https://github.com/OWASP/ASVS | Use ASVS as the control checklist source, but the MVP should not claim ASVS compliance. VibeSpec should map obvious repo evidence to beginner-friendly findings and mark unknown controls as review-required. |
| OWASP API Security Top 10 | 2023 stable release, Feb 14 2023: https://owasp.org/www-project-api-security/ and https://owasp.org/API-Security/editions/2023/en/0x00-header/ | API risks should emphasize BOLA/IDOR, broken authentication, unrestricted resource consumption, and unsafe object-property exposure. These are common in AI-generated CRUD apps. |
| OWASP Top 10 for LLM / GenAI Applications | 2025 release: https://genai.owasp.org/llm-top-10/ | LLM checks must include prompt injection, sensitive information disclosure, supply chain, excessive agency, unbounded consumption, and output/tool-call governance. |
| NIST SSDF / SP 800-218 | SP 800-218 final, Feb 2022: https://csrc.nist.gov/pubs/sp/800/218/final and SSDF project page https://csrc.nist.gov/projects/ssdf | The MVP should frame security as an SDLC gate: prepare, protect, produce well-secured software, and respond. It should produce repair tasks and retest loops rather than one-off warnings. |
| GitHub Advanced Security | GitHub docs: https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security | GHAS combines secret protection, code security, dependency review, and code scanning. VibeSpec should mirror this grouping locally without requiring GitHub Advanced Security. |
| GitHub secret scanning | GitHub docs: https://docs.github.com/code-security/secret-scanning/about-secret-scanning | Secret scanning should consider entire git history in real deployments. MVP static scan can detect current working-tree leaks and warn that history scanning requires Gitleaks/GitHub secret scanning. |

## Open Source Tools

| Tool | Source | What to reuse | MVP fallback |
|---|---|---|---|
| Semgrep | GitHub README: https://github.com/semgrep/semgrep and docs repo https://github.com/semgrep/semgrep-docs | Use for static pattern rules when installed. Useful for framework-specific code risks. | Built-in text and path heuristics for high-confidence beginner mistakes. |
| Gitleaks | GitHub README: https://github.com/gitleaks/gitleaks and https://gitleaks.io/ | Use for hardcoded secrets in files and git history. | Built-in regex scanner with strict masking. |
| Trivy | GitHub README: https://github.com/aquasecurity/trivy | Use for filesystem, dependency, container, Kubernetes, and IaC scanning when installed. | Parse package manifests and warn about missing lockfiles or known risky versions. |
| OWASP ZAP | GitHub README: https://github.com/zaproxy/zaproxy | Use only for explicitly authorized local/staging passive or baseline scanning. | Adapter stub only; default is no dynamic scan. |
| TruffleHog | GitHub README: https://github.com/trufflesecurity/trufflehog | Alternative advanced secrets discovery, classification, and optional verification. | Not required in MVP because verification can call providers and may be too invasive for beginners. |
| CodeQL | Docs: https://codeql.github.com/ and GitHub repo https://github.com/github/codeql | Strong semantic analysis for supported languages and custom queries. | Defer to post-MVP because setup and database generation are heavy. |
| npm audit | npm docs: https://docs.npmjs.com/cli/v9/commands/npm-audit | Use for Node dependency vulnerability reports when user opts into registry queries. | Static lockfile/manifest review. Do not auto-run `npm audit fix`. |
| pnpm audit | pnpm docs: https://pnpm.io/cli/audit | Same as npm audit for pnpm projects. | Static review and actionable instructions. |
| pip-audit | GitHub README: https://github.com/pypa/pip-audit | Use for Python known-vulnerability checks. Its own security model warns against auditing packages you would not install. | Static requirements parsing and install instructions. |
| Safety CLI | Docs: https://docs.safetycli.com/safety-docs/safety-cli/introduction-to-safety-cli-vulnerability-scanning | Optional Python dependency scanner. | Defer unless user configures it. |
| OWASP Dependency-Check | OWASP page: https://owasp.org/www-project-dependency-check/ | Mature SCA for ecosystems such as Java. | Defer; too broad for a Python/Node-focused MVP. |

Design implication: the MVP should be an orchestration and explanation layer. It should gracefully degrade when tools are missing and must never require global installation, admin rights, or uploading user code.

## Platform Security Notes

| Platform | Source | Useful MVP checks |
|---|---|---|
| Supabase | RLS docs: https://supabase.com/docs/guides/database/postgres/row-level-security | Flag tables in public schema without `enable row level security`; flag use of service role keys in frontend paths; remind users that policies are required after RLS is enabled. |
| Firebase | Security Rules docs: https://firebase.google.com/docs/rules and Firestore guide https://firebase.google.com/docs/firestore/security/get-started | Flag `allow read, write: if true`; check for rules that lack `request.auth`; mark complex rule correctness as manual review. |
| Next.js | Headers docs: https://nextjs.org/docs/app/api-reference/config/next-config-js/headers and CSP guide https://nextjs.org/docs/app/guides/content-security-policy | Check whether security headers are configured, flag public source maps/debug, and watch the `NEXT_PUBLIC_` boundary for accidental secret exposure. |
| Vercel | Environment variables docs: https://vercel.com/docs/environment-variables and sensitive env vars https://vercel.com/docs/environment-variables/sensitive-environment-variables | Prefer platform env vars over checked-in values. Sensitive env vars are useful, but access controls and frontend exposure still need review. |

## Competitor and Adjacent Product Lessons

| Product | Source | Lesson for VibeSpec Gate |
|---|---|---|
| Snyk | https://snyk.io/product/open-source-security-management/ and https://docs.snyk.io/scan-fix-and-prevent/scan-with-snyk/snyk-open-source | Developer-first prioritization and remediation matter more than raw finding count. |
| GitGuardian | https://docs.gitguardian.com/ and https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/quick_start | Secrets findings need classification, masking, remediation guidance, and rotation advice. |
| Socket.dev | https://socket.dev/ and HN discussion https://news.ycombinator.com/item?id=30515090 | Supply-chain checks should consider malicious package signals, not only known CVEs. MVP can warn on risky package hygiene but should not overclaim. |
| Aikido Security | https://www.aikido.dev/ and https://www.aikido.dev/platform | Consolidation of SAST, SCA, secrets, IaC, and cloud posture reduces user burden. VibeSpec should consolidate outputs into one gate decision. |
| Semgrep Cloud / GHAS | https://semgrep.dev/products/community-edition and GitHub docs above | Strong tools still need triage and context. VibeSpec should translate tool output into beginner and Codex repair tasks. |

## Community and Pain-Point Signals

Community sources are useful as demand signals, not as standards:

- Hacker News discussion "Vibe Coding Is a Security Disaster That Is About to Happen" (2026): https://news.ycombinator.com/item?id=47479724 highlights the confidence gap: AI-generated code can look polished while containing serious security flaws.
- Reddit r/vibecoding thread "Vibe coding without a security audit..." (2026): https://www.reddit.com/r/vibecoding/comments/1sfa9sx/vibe_coding_without_a_security_audit_is_not_a/ describes recurring issues such as Supabase service role exposure and founders not recognizing the risk.
- GitHub community discussion on AI security headaches (2026): https://github.com/orgs/community/discussions/193727 mentions OWASP-style flaws and secret leakage from AI-suggested code.
- Reddit r/devops thread on securing AI-generated internal apps (2026): https://www.reddit.com/r/devops/comments/1td7mxp/how_are_you_securing_aigenerated_vibecoded/ shows governance needs: authentication from day one, approved domains, and deployment discovery.
- Reddit r/github thread on AI-generated vulnerability reports (2026): https://www.reddit.com/r/github/comments/1sjfmfw/received_our_very_first_aigenerated_security/ warns that low-context automated reports can create noise. VibeSpec must mark uncertainty and avoid unsupported claims.

## Reusable vs. VibeSpec-Owned Responsibilities

Reusable through adapters:

- Secret detection: Gitleaks first, TruffleHog optional.
- SAST patterns: Semgrep first, CodeQL later.
- Dependency/container/IaC scanning: Trivy, npm audit, pnpm audit, pip-audit, Safety, Dependency-Check where configured.
- Passive/baseline DAST: ZAP only with explicit authorization.

VibeSpec must own:

- Project intake and risk profile.
- Finding schema, deduplication, severity normalization, and gate decision.
- Beginner explanation and business impact wording.
- Codex repair task generation.
- Retest checklist and loop review.
- AI/LLM/Agent-specific local heuristics.
- Safety boundaries, masking, and disclaimers.

## MVP Design Corrections from Research

1. Do not promise full OWASP/ASVS compliance. The MVP maps to selected controls and clearly labels unknowns.
2. Do not default to dynamic URL scanning. ZAP remains opt-in and authorization-gated.
3. Do not auto-run package fixes or destructive remediations. Generate repair instructions only.
4. Do not upload code or secrets to SaaS tools by default. Local adapters only; registry-dependent audits should be explicit.
5. Treat AI-generated code as untrusted and require the same static, dependency, auth, and data checks as human-written code.
6. Report evidence without exposing full secrets. All detected secret-like values must be masked.
7. Favor high-confidence, beginner-relevant findings over exhaustive low-signal SAST output.
