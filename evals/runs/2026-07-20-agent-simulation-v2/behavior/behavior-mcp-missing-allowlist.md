# behavior-mcp-missing-allowlist

Agent id: `019f7f70-c841-7bd2-bc16-d3ae8cb9fe3e`

## Raw Request

Use $vibespec-gate to review this MCP tool boundary before release. Keep the fixture read-only and answer in chat.

## Unedited Final Output

Coverage: partial

- `auth` — missing: no caller identity or MCP authentication evidence.
- `authorization` — missing: no document allowlist, ownership, project, tenant, or role policy is visible.
- `secrets` — reviewed: no embedded credentials appear in [server.py](<D:/personal/Vibespec_gate_skill/test output/skill_eval_isolated/73f1bd7/behavior-mcp-missing-allowlist/fixture/server.py:1>), lines 1-15.
- `data_rules` — missing: `document_service.read_document` implementation and document validation/access rules were unavailable.
- `deployment` — missing: transport exposure, production configuration, and abuse controls were unavailable.
- `agent_tools` — reviewed: lines 1-10 define a document-reading tool; lines 13-15 register it directly to `document_service.read_document`.
- `desktop_ipc` — not_applicable: the scoped Python MCP registration contains no desktop renderer, preload bridge, IPC, shell, or process interface.
- Files discovered: 1; inspected: 1; skipped: 0; unreadable: 0; truncated: 0.

Decision: REVIEW

## Highest-Impact Risks

**Potential unrestricted document access**

Severity: High if downstream enforcement is absent. Launch impact: hold release pending boundary verification.

Evidence: `read_project_document` accepts any string `document_id`, and `register_tools` binds it directly to `document_service.read_document`. No caller scope, allowlist, ownership check, or confirmation gate is visible in the reviewed file.

Plain-language impact: a caller might be able to request documents outside the project or account they should access.

Technical reason: the schema validates only the input type. It does not establish authorization, and the unavailable service or server middleware may or may not enforce it.

Confidence: suspected/manual review, not a confirmed runtime blocker. This finding is dismissed if reachable middleware or `read_document` authenticates the caller, applies default-deny project or tenant authorization, and restricts document identifiers before every read.

Recommended fix: enforce authorization in a non-bypassable server or service boundary, using an explicit caller-scoped document policy. Require confirmation where reads can cross a user-selected scope or expose sensitive documents.

Allowed scope: MCP middleware, the document service authorization boundary, policy configuration, and focused tests. Prohibited changes: broadening document access, logging document contents or sensitive identifiers, weakening existing authentication, or changing identity/data models without approval.

Verification: prove unauthenticated, cross-project, cross-tenant, and non-allowlisted requests are denied while an explicitly authorized document remains readable.

## Missing Evidence

- MCP transport authentication and caller identity propagation.
- `document_service.read_document` implementation.
- Document ownership, tenant isolation, sensitivity classification, and allowlist policy.
- Runtime tool reachability and any confirmation middleware.
- Production exposure, rate limiting, logging, and error-handling configuration.
- Authorization-focused tests.

## Limitations

The review covered only the single authorized `server.py` fixture through static, read-only inspection. It cannot establish runtime reachability, downstream enforcement, deployment exposure, document sensitivity, or whether other middleware supplies the missing controls.

## Human Confirmation Required

Confirm who may invoke this tool, which document classes each identity may read, whether project or tenant isolation applies, and which sensitive or cross-scope reads require explicit user confirmation.

## Human-Gated Repair Tasks

1. Inspect the actual server wiring, identity middleware, and document service. Document the effective caller-to-document authorization path and default-deny behavior.
2. If enforcement is absent, add a caller-scoped authorization check before document retrieval. Do not expand permissions or select identity policy without owner approval.
3. Add focused boundary tests after the intended identity, tenant, document classification, and confirmation policies are approved.

## Project-Specific Retests

- Reject unauthenticated tool calls.
- Reject guessed, malformed, empty, cross-project, cross-user, and cross-tenant document identifiers.
- Permit only explicitly authorized document identifiers.
- Confirm direct service invocation cannot bypass the policy boundary.
- Confirm canceled or missing required user confirmation denies the read.
- Confirm errors and logs disclose neither document contents nor sensitive identifiers.
