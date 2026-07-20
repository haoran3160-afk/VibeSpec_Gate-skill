# mcp-pre-refinement-overblock

Agent id: `019f7d89-91bb-78d3-b1e0-08382a965f98`

This run attached `SKILL.md` directly and activated the workflow, but it overblocked missing policy evidence. The result caused the protocol to distinguish a confirmed privileged operation from an unavailable downstream allowlist.

## Unedited Final Output

**Decision: `BLOCK`**

The MCP document-read boundary is not ready for release. The tool accepts any string `document_id` and directly registers the unrestricted service method, with no visible agent-scoped allowlist or default-deny guard.

**High-Severity Finding**

Affected code: [server.py](D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:6), especially [line 13](D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:13).

- **Evidence:** `document_id` permits any string, and `document_service.read_document` is exposed directly.
- **Impact:** An agent influenced by untrusted content could request project documents outside its intended authority.
- **Technical reason:** JSON Schema type validation is not authorization. No MCP-specific document allowlist, caller/project scope, or confirmation gate is applied before the service executes.
- **Confidence:** Confirmed for the shown MCP boundary. Whether downstream code independently blocks unauthorized IDs is unavailable evidence.
- **Downgrade condition:** `read_document` must demonstrably enforce an authenticated, agent-scoped, default-deny allowlist before reading data. General user access alone is insufficient if the agent should have narrower authority.

**Coverage**

`coverage_status: partial`

| Surface | Status | Reason |
|---|---|---|
| Authentication | Missing | MCP transport identity and session controls are absent. |
| Authorization | Reviewed | No authorization guard appears at this boundary. |
| Secrets | Reviewed | No embedded credentials appear in the file. |
| Data rules | Missing | Document storage and access policies are unavailable. |
| Deployment | Missing | Production exposure and transport configuration are unavailable. |
| Agent tools | Reviewed | Tool schema and registration were fully inspected. |
| Desktop IPC | Not applicable | The authorized evidence is a Python MCP registration boundary with no desktop IPC surface. |

Files discovered: 1. Inspected: 1. Skipped: 0. Truncated/unreadable: 0.

**Human-Gated Repair Plan**

Introduce a wrapper around `read_document` that normalizes the logical identifier, checks it against an explicit default-deny allowlist scoped to the authenticated project/session, and only then calls the service. A human must approve the permitted document set and decide whether sensitive documents require per-call confirmation.

Do not use prompt instructions, tool descriptions, wildcard prefixes, or client-provided scope as authorization. Do not broaden document access or log document contents.

**Release Retests**

1. An explicitly allowed document succeeds.
2. Unknown, cross-project, empty, malformed, and normalization-variant identifiers are rejected before the service is called.
3. Untrusted prompt content cannot expand the allowlist.
4. Missing identity or scope fails closed.
5. Denials return generic errors without document contents or sensitive identifiers in logs.

No files were changed and no dynamic tests were run.
