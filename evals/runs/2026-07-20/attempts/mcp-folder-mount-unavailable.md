# mcp-folder-mount-unavailable

Agent id: `019f7d80-0654-79b3-984b-95601ccd5329`

This failed attempt used a folder-valued Skill attachment before standard-path installation. The fixture also contained unrestricted shell execution, so it did not isolate the intended missing-allowlist behavior.

## Unedited Final Output

**Result: BLOCK RELEASE**

`$vibespec-gate` is unavailable in the configured skill roots, so this is a manual MCP-boundary review.

- **Critical:** [`server.py:7`](D:/personal/Vibespec_gate_skill/evals/fixtures/mcp-missing-allowlist/server.py:7) accepts arbitrary MCP input and passes it to `subprocess.check_output(..., shell=True)` at line 8. Any caller can execute unrestricted shell commands under the server’s identity. There is no command allowlist, argument validation, or authorization boundary.
- **High:** Execution has no timeout or output limit, allowing commands to hang the worker or exhaust memory.

Required before release: replace free-form command input with narrowly defined operations, enforce an explicit executable/argument allowlist, use `shell=False`, and add timeout/output limits.

::code-comment{title="[P0] Unrestricted command execution" body="MCP-controlled input is passed directly to a shell without an allowlist or validation, allowing arbitrary host command execution. Replace the free-form command boundary with explicit permitted operations and invoke validated argv with shell=False." file="D:\personal\Vibespec_gate_skill\evals\fixtures\mcp-missing-allowlist\server.py" start=7 end=8 priority=0}

No files were created or modified.
