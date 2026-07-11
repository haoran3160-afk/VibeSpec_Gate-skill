# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\mcp_tool_boundary_no_evidence\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-MCP-001`
- Evidence files: `src/mcp/server.ts`

## Safety

- `safe_to_auto_suppress`: false
