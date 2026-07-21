Coverage: partial

Decision: REVIEW

Review Surfaces
- `auth`: not_applicable. The reviewed scope is a single MCP tool registration helper with no login, session, token, or identity-handling code present in [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:1).
- `authorization`: missing. No caller identity, tenant scope, ACL, document ownership check, or server-side policy is visible before the tool is bound to `document_service.read_document` in [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:12).
- `secrets`: not_applicable. No credentials, tokens, env loading, or secret material are present in the only reviewed file, [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:1).
- `data_rules`: missing. The tool claims to read a project document by logical identifier, but there is no visible evidence of document classification, allowed-id constraints, or downstream data access rules because `document_service.read_document` is not present in the fixture, [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:2).
- `deployment`: missing. No runtime config, network exposure, transport boundary, or MCP server deployment settings are included in the reviewed evidence set.
- `agent_tools`: reviewed. The tool schema accepts an arbitrary string `document_id` and registers the tool directly to `document_service.read_document` with no visible allowlist, confirmation gate, or least-privilege wrapper in [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:1) and [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:12).
- `desktop_ipc`: not_applicable. No desktop, Electron, preload, IPC, or local process boundary code is present in the reviewed fixture.

**Highest-Impact Risks**
- Severity: high. Launch impact: an untrusted MCP caller may be able to request any logical document the backing service will return, with no visible boundary at registration time. Affected files: [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:12). Evidence: `server.register_tool(TOOL_SCHEMA, document_service.read_document)` binds the exposed tool directly to the document-read function, and the schema constrains only that `document_id` is a string. Plain-language impact: if downstream protections are weak or absent, the MCP surface can become a generic document exfiltration path. Technical reason: there is no visible allowlist of readable document IDs, no caller-to-document authorization check, and no confirmation or mediation layer in the exposed boundary. Confidence: suspected, because downstream enforcement is not included in the fixture. Recommended fix: add an explicit boundary wrapper that validates `document_id` against an approved set or policy and enforces caller-scoped authorization before invoking the service. Allowed scope: the MCP registration layer and the document-read policy hook. Prohibited changes: do not broaden readable document scope or silently trust client-supplied IDs. Human confirmation: confirm which document classes are intentionally exposed through MCP and whether caller identity is available at this boundary. Verification: prove that unauthorized, cross-project, and unknown IDs are rejected before the service read occurs. False-positive or downgrade condition: this drops if the missing service layer evidence shows a mandatory server-side allowlist and per-caller authorization that cannot be bypassed from this tool registration path.

**Missing Evidence**
- The implementation of `document_service.read_document`, including document lookup rules and any authorization checks.
- The MCP server’s caller identity model and whether tool invocations carry authenticated principal context.
- Any allowlist, confirmation, or policy middleware between tool registration and service execution.
- Deployment/runtime configuration showing who can reach this MCP server and over what transport.

**Limitations**
- Reviewed scope: one local file, [server.py](/D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/behavior/behavior-mcp-missing-allowlist/project/server.py:1), discovered as the only file in the authorized fixture.
- Files discovered: 1. Files inspected: 1. Files skipped: 0. Unreadable: 0. Truncated: 0.
- This evidence is enough to confirm that the exposed MCP boundary has no visible policy layer in this fixture, but not enough to establish runtime reachability, downstream authorization, deployment exposure, or whether a separate wrapper exists outside the reviewed project.

**Human Confirmation Required**
- Whether `read_project_document` is intended to be callable by untrusted or semi-trusted MCP clients before release.
- Which document identifiers or document classes are allowed to cross this boundary.
- Whether caller identity and project/tenant context are available to the tool handler at runtime.
- Whether downstream service authorization is mandatory and non-bypassable for every invocation path.

**Human-Gated Repair Tasks**
- Add an MCP-facing wrapper around `document_service.read_document` that enforces explicit document allowlisting or a deny-by-default policy before any read.
- Bind tool execution to caller identity or session context and require server-side authorization for the requested document, not just input shape validation.
- Narrow the tool contract if possible so callers cannot pass arbitrary logical IDs; expose only pre-approved operations or enumerated safe identifiers.
- Document the intended trust boundary for this tool in code or config so later registrations cannot bypass the policy layer.

**Project-Specific Retests**
- Invoke `read_project_document` with an authorized document ID and confirm the read succeeds only for the intended caller scope.
- Invoke it with an unknown or malformed `document_id` and confirm the request is rejected before any document lookup.
- Attempt a cross-scope or disallowed document ID and confirm deny-by-default behavior.
- Verify that direct registration cannot call the raw service method without the new policy wrapper in place.
- Re-review the MCP registration file and the service implementation together to confirm the boundary is enforced in runtime code, not only in comments or tests.