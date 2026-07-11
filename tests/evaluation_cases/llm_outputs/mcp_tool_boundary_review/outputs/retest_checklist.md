# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\mcp_tool_boundary_review\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-MCP-001`
- Evidence files: `src/mcp/server.ts`
- Expected gate change: REVIEW clears only after schema, allowlist, and path boundary are evidenced.

## Manual Checks

- Confirm allowed tool names and allowed path roots.
- Confirm invalid arguments are rejected.

## Safety

- `safe_to_auto_suppress`: false
