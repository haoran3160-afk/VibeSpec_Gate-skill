# behavior-mcp-missing-allowlist

Agent id: `019f7eef-f68a-73b3-9551-2f242f5a1af3`

Invocation: explicit `vibespec-gate` Skill attachment, fresh subagent, `fork_context=false`

Authorized isolated fixture: `test output/skill_eval_isolated/3580a3d/behavior-mcp-missing-allowlist/fixture/server.py`

## Raw Request

Use $vibespec-gate to review this MCP tool boundary before release. Keep the fixture read-only and answer in chat.

## Unedited Final Output

Coverage: partial

- `auth` — missing: caller authentication and MCP transport/session configuration were not provided.
- `authorization` — missing: `document_service.read_document` and its owner/project/tenant checks were not provided.
- `secrets` — reviewed: no credentials or secret handling appear in [server.py](D:/personal/Vibespec_gate_skill/test%20output/skill_eval_isolated/3580a3d/behavior-mcp-missing-allowlist/fixture/server.py:1).
- `data_rules` — missing: document storage, access policies, and identifier validation are unavailable.
- `deployment` — missing: exposure, production configuration, and abuse controls are unavailable.
- `agent_tools` — reviewed: the tool schema and direct handler registration appear at [server.py](D:/personal/Vibespec_gate_skill/test%20output/skill_eval_isolated/3580a3d/behavior-mcp-missing-allowlist/fixture/server.py:1).
- `desktop_ipc` — not_applicable: this scoped Python fixture contains an MCP registration boundary and no desktop renderer, preload bridge, or IPC interface.
- Inventory: 1 fixture file discovered and inspected; 0 skipped, unreadable, or truncated.

Decision: REVIEW

**Highest-Impact Risks**

**High, release review required: document-read authorization boundary is unverified.**

- Evidence: the tool accepts any string `document_id` and directly registers `document_service.read_document`; no caller identity, project/tenant scope, document allowlist, or confirmation policy is visible.
- Impact: if downstream enforcement is absent, an MCP caller could request documents outside its authorized project or user scope.
- Technical reason: schema validation establishes input shape, not authorization.
- Confidence: suspected/manual review. This is not a confirmed blocker because the service implementation and runtime reachability are unavailable.
- Recommended fix: enforce default-deny authorization using authenticated caller context and server-derived project/tenant scope before document lookup. Use an allowlist where the product permits only a bounded document set.
- Allowed scope: MCP registration policy, authorization wrapper, and document-service access checks.
- Prohibited changes: do not broaden document access, trust caller-supplied tenant identity, expose raw filesystem paths, or silently add privileged fallback behavior.
- Human confirmation: define which identities may read which document collections and whether each read requires confirmation.
- Downgrade condition: authenticated, default-deny object-level authorization already exists inside `read_document` and tests demonstrate cross-user and cross-project denial.

**Missing Evidence**

- `document_service.read_document` implementation and storage policies.
- MCP authentication, session identity, and transport exposure.
- Tool allowlist and confirmation policy.
- Production deployment and rate-limit configuration.
- Representative authorization tests.

**Human-Gated Repair Tasks**

1. Trace the registered handler through document lookup and record every identity and authorization check.
2. Decide the permitted user, role, project, and tenant relationships.
3. Add or verify server-side default-deny checks; keep `document_id` validation separate from authorization.
4. Confirm whether reads are allowlisted, automatically permitted, or require user confirmation.
5. Review logs and errors to ensure document contents, identifiers, and credentials are not unnecessarily exposed.

**Project-Specific Retests**

- Reject unauthenticated MCP calls.
- Reject unknown and malformed `document_id` values without leaking document existence.
- Deny cross-user, cross-project, and cross-tenant reads.
- Deny documents outside the configured allowlist.
- Verify confirmation is required where policy demands it and cannot be bypassed by repeated calls.
- Confirm authorization occurs before document content is fetched or logged.
- Verify safe rate limiting and generic error responses at the deployed MCP boundary.
