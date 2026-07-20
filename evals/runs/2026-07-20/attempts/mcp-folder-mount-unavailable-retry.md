# mcp-folder-mount-unavailable-retry

Agent id: `019f7d86-1a79-7c93-a02a-c69ff880658e`

This failed retry used the corrected fixture but the same folder-valued Skill attachment. It demonstrated that checking the source folder alone was not an activation smoke.

## Unedited Final Output

**Gate Result: FAIL**

- **[P1] Missing allowlist at the MCP boundary.** [`server.py:12`](D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:12) registers `document_service.read_document` directly, while the schema accepts any string `document_id`. No boundary-level authorization or allowlist prevents access to unintended documents. Because this file is the complete evidence, downstream protection cannot be assumed.

**Required before release:** register a fail-closed wrapper that verifies `document_id` against the caller’s explicit permitted set before invoking `read_document`. Add tests proving allowed IDs succeed and unknown, empty, malformed, and alias/case-variant IDs are rejected.

`$vibespec-gate` was unavailable, so this result uses a direct equivalent review of the permitted file only.
