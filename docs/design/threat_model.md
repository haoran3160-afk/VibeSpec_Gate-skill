# VibeSpec Gate Threat Model

## Assets Protected

- User source code and repository metadata.
- Secrets, tokens, connection strings, and environment variables.
- Security reports that may contain sensitive paths or masked evidence.
- User trust in launch decisions.

## Trusted Boundary

The MVP operates on local files in a user-owned or explicitly authorized project. It does not upload code or logs to third-party services. External tools are local CLI adapters only.

## Threats

| Threat | Risk | MVP control |
|---|---|---|
| Secret disclosure in reports | A report could leak a full API key. | Mask detected values and store only snippets. |
| Unauthenticated dynamic scanning | Tool could scan third-party targets. | No default dynamic URL scan; ZAP adapter is authorization-gated. |
| False sense of safety | User may treat a PASS as absolute security. | Every report includes a disclaimer and manual-review conditions. |
| Unsupported exploit guidance | Tool could drift into offensive instructions. | Scanners report defensive evidence and remediation only. |
| Tool absence causing failure | Gitleaks/Trivy/Semgrep may be missing. | Adapters degrade to informational findings and built-in heuristics. |
| Noisy unsupported claims | Static heuristics may overstate risks. | Findings include evidence, false-positive notes, and review-required markers. |
| User project mutation | Scanner could alter files. | MVP scanners are read-only. No auto-fix mode. |

## Abuse Cases Explicitly Out of Scope

- Scanning sites not owned by the user.
- Generating exploit payloads or bypass instructions.
- Brute forcing, privilege escalation, backdoors, or data exfiltration.
- Secret rotation or production data mutation.

## Residual Risk

Static scanning cannot prove absence of vulnerabilities. Framework-specific authorization can be inherited from middleware or platform configuration not visible to the scanner. High-risk launches need human review.
