# trigger-positive-mcp-permissions

Agent id: `019f7d92-924a-7401-a67a-2fa2f446b52e`

## Raw Request

Use $vibespec-gate to review D:\personal\Vibespec_gate_skill\evals\fixtures\mcp-missing-allowlist\server.py for MCP permission boundaries before release. Keep it read-only, create no files, and answer in chat.

## Unedited Final Output

**Launch Decision: REVIEW**

The file alone does not establish a safe MCP permission boundary. Per the gate protocol, this is not a confirmed `BLOCK` because downstream enforcement and runtime reachability are unavailable.

**Scope**
- Product: Python MCP tool registration fixture
- Stage: pre-release
- Capability: reads project documents by logical identifier
- Sensitive data: project documents; classification unknown
- Identity model: missing from evidence
- Files: 1 discovered, 1 inspected, 0 skipped, 0 unreadable/truncated
- Review was read-only; no files were created or modified

**High-Risk Finding**
**Suspected High: document-read tool lacks a visible caller-scoped allowlist**

Evidence:
- [`document_id` accepts any string](/D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:6).
- [`read_document` is registered directly](/D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:13), with no visible authentication context, project/tenant scope, allowlist, or confirmation policy.

Impact: If untrusted callers can reach this tool and `document_service.read_document` does not independently enforce access control, they may read documents outside their authorized project.

Confidence: **Suspected**. The service implementation and MCP server access policy were not available.

This finding is dismissed only if evidence shows that every call receives an authenticated principal and the service applies deny-by-default, project-scoped authorization before retrieving content.

**Coverage**
| Surface | Status | Reason |
|---|---|---|
| Authentication | Missing | No caller identity or session evidence |
| Authorization | Missing | Downstream `document_service` policy unavailable |
| Secrets | Not applicable | No secret handling in this registration file |
| Data rules | Missing | Storage and document-access rules unavailable |
| Deployment | Missing | Exposure and transport configuration unavailable |
| Agent tools | Reviewed | Schema and registration inspected |
| Desktop IPC | Not applicable | No desktop or IPC boundary in this Python artifact |

Overall coverage: **partial**.

**Human-Gated Repair Plan**
1. Decide which identities, projects, tenants, and document classes may use this tool.
2. Enforce authenticated, deny-by-default document authorization at the authoritative service boundary.
3. Pass caller context explicitly rather than trusting caller-supplied `document_id`.
4. Add identifier length/format constraints as defense in depth; do not treat schema validation as authorization.
5. Do not broaden permissions, rely solely on prompt/client checks, or log document contents or credentials.

**Required Retests**
- Unauthenticated calls are rejected.
- Authorized callers can read only explicitly permitted documents.
- Cross-user, cross-project, and cross-tenant reads are denied.
- Unknown, malformed, and path-like identifiers are rejected safely.
- Authorization cannot be bypassed through aliases or indirect identifiers.
- Denials and logs expose neither document contents nor credentials.
