# Review Protocol

Use this protocol for every VibeSpec Gate review. Keep project access read-only until the user separately approves a fix.

## 1. Establish Scope

Confirm the authorized local project or evidence directory, launch stage, public exposure, sensitive data, identity model, and whether AI Agents, tools, MCP, IPC, desktop APIs, local files, shell commands, email, payments, or databases are in scope.

Inventory available files before drawing conclusions. Record the total discovered, inspected, skipped, unreadable, and truncated counts. Do not hide sampling limits.

## 2. Inspect Evidence

Inspect the smallest relevant set of runtime code and configuration first:

- authentication: login, signup, logout, password reset, magic links, OTP send/verify, sessions, cookies, JWTs, refresh and invalidation;
- authorization: owner, tenant, role, admin, server-side route guards, object-level checks, and default-deny behavior;
- secrets: source, environment files, client bundles, logs, analytics, errors, build output, and deployment variables;
- data rules: database policies, Supabase RLS, Firebase rules, storage, uploads, validation, retention, and public reads/writes;
- deployment: production flags, debug endpoints, CORS, headers, TLS assumptions, rate limits, abuse controls, and exposed services;
- Agent tools: prompts, tool schemas, allowlists, confirmation gates, least privilege, command/file/database/email/payment authority, and untrusted input;
- desktop IPC: preload bridges, renderer isolation, IPC validation, local file boundaries, shell/process execution, extension permissions, and update channels.

Treat tests, examples, generated code, vendored files, and scanner findings as context. Confirm runtime reachability before using them as launch blockers.

For Agent and MCP boundaries, distinguish a confirmed capability from missing policy evidence. A schema or tool registration with no visible allowlist, identity scope, or confirmation policy is `REVIEW` when downstream enforcement and runtime reachability are unknown. Use `BLOCK` only when evidence confirms that an untrusted caller can reach a privileged operation, sensitive data, arbitrary file/command access, or an equivalent launch blocker without an effective boundary.

## 3. Record Findings

Each finding must include:

- severity and launch impact;
- affected file or configuration reference;
- concise evidence with complete credentials masked;
- beginner explanation and technical reason;
- confidence: confirmed, suspected, or manual review;
- recommended change and bounded Agent task;
- prohibited changes and human confirmation;
- project-specific verification steps;
- false-positive or downgrade conditions.

Do not claim a missing control when evidence was not available. Record the gap as missing evidence.

## 4. Apply Decision Precedence

1. `BLOCK` for a confirmed launch blocker, including a confirmed runtime P0. Incomplete coverage does not erase confirmed blocking evidence.
2. `REVIEW` when any required evidence surface is missing, partial, truncated, ambiguous, or awaits human confirmation.
3. `PASS_WITH_WARNINGS` only with complete coverage, no blocker, and a remaining lower-priority or accepted warning.
4. `PASS` only with complete coverage, no missing surface, and no material finding.

An empty finding list is not proof of safety. Do not calculate or show a numeric security score for incomplete coverage.

## 5. Prepare Repairs

Repair tasks are plans, not permission to edit. For each task, identify files to inspect, allowed change scope, prohibited changes, required human decision, and verification. Never auto-suppress a finding or choose identity, CAPTCHA, MFA, recovery, retention, billing, or notification policy for the user.

## 6. Retest

Retest the exact control and its likely bypass paths. Typical checks include unauthenticated rejection, cross-user and cross-tenant denial, non-admin denial, expired/reused token rejection, safe rate limiting, generic account responses, secret-free logs, least-privilege tool behavior, rejected malformed IPC, and safe deployment configuration.

Do not run live, destructive, brute-force, CAPTCHA-bypass, credential-stuffing, phishing, OTP interception, or production lockout tests.

## 7. Output and Stop

Return coverage, one decision, the highest-impact risks, human-gated repair tasks, and retests in chat. If file output was approved, use all four bundled templates and an `evidence/` directory outside the reviewed project. Stop before project mutation until the user separately confirms the evidence and authorizes the fix.
