# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required before changing MCP tool behavior.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Confirm MCP boundary controls

- Finding IDs: `VSG-MCP-001`
- Files to inspect: `src/mcp/server.ts`
- Allowed change scope: add schema validation, allowlist checks, and path constraints for this tool only.
- Missing evidence to confirm first: caller boundary and intended allowed paths.

## Prohibited Changes

- Do not broaden file access.
- Do not add new tools while fixing this boundary.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
