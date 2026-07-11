# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation not required.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: No MCP change

- Finding IDs: `VSG-MCP-001`
- Files to inspect: `src/mcp/server.ts`
- Allowed change scope: none.

## Prohibited Changes

- Do not change MCP tools.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
