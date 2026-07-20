# behavior-mcp-missing-allowlist

Agent id: `019f7d90-7f8a-75f2-9724-8af7f849bc09`

## Raw Request

Use $vibespec-gate to review the MCP tool boundary at D:\personal\Vibespec_gate_skill\evals\fixtures\mcp-missing-allowlist\server.py before release. Treat this file as the complete available evidence. Do not inspect unrelated repository files, do not create or edit files, and return the result in chat only.

## Unedited Final Output

**Launch Decision: `REVIEW`**

Do not approve release until the MCP document-read boundary is verified or repaired. The available evidence does not prove that an untrusted caller can reach unauthorized documents, so `BLOCK` is not justified.

**Context**

- Product: Python MCP tool server
- Stage: pre-release
- Capability: read project documents by logical identifier
- Sensitive data: project documents; classification unknown
- Identity model: missing from evidence
- Evidence inventory: 1 discovered, 1 inspected, 0 skipped, 0 unreadable, 0 truncated

**Coverage**

| Surface | Status | Reason |
|---|---|---|
| Authentication | Missing | No caller authentication or transport policy |
| Authorization | Missing | No caller, project, tenant, or document-level policy |
| Secrets | Missing | Secret handling and runtime configuration unavailable |
| Data rules | Missing | Storage policy and downstream validation unavailable |
| Deployment | Missing | Exposure, transport, rate limits, and production settings unavailable |
| Agent tools | Reviewed | Tool schema and registration inspected |
| Desktop/IPC | Missing | MCP transport and local-process boundary unavailable |

Overall coverage: `partial`.

**High-Risk Finding**

**Missing caller-bound document access policy**

- Severity: **High**, potential unauthorized information disclosure
- Launch impact: Release requires human review; runtime exposure is unconfirmed
- Evidence: [server.py](D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:6), lines 6 and 12-13
- Technical reason: `document_id` accepts any string, and the tool directly registers `document_service.read_document`. No allowlist, authenticated principal, project scope, object-level authorization, or confirmation gate appears at this boundary.
- Plain-language impact: Any caller accepted by the MCP server may be able to request any document identifier that the downstream service recognizes.
- Confidence: **Confirmed boundary omission; suspected runtime impact.** The implementation of `read_document` and server reachability are unavailable.
- Downgrade condition: Dismiss or reduce this finding if evidence shows that every invocation reaches an unavoidable, default-deny check binding an authenticated caller to an authorized project and document.

**Human-Gated Repair Plan**

1. Define who may call this tool and which projects/documents each principal may read.
2. Enforce that policy in an authoritative server-side handler before document lookup. Reject unauthenticated, cross-project, and non-allowlisted requests by default.
3. Apply bounded identifier validation and generic denial responses.
4. Do not rely on prompts, UI filtering, caller-supplied project scope, wildcard allowlists, or optional middleware.
5. Human confirmation required: intended trust model, document sensitivity, tenant boundaries, and whether broad or sensitive reads require per-call approval.

**Retests**

- Unauthenticated calls are rejected.
- Authorized callers can read only explicitly permitted documents.
- Cross-user, cross-project, and cross-tenant identifiers are denied.
- Empty, oversized, malformed, path-like, and encoded identifiers are rejected safely.
- Direct tool calls cannot bypass the policy.
- Denials and logs do not expose document contents or sensitive identifiers.
- Confirm the same checks remain active under the production MCP transport.

No files were changed and no dynamic tests were run.
