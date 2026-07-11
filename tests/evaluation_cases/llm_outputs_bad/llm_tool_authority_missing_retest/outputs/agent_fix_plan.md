# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Add tool confirmation

- Finding IDs: `VSG-AGENT-001`
- Files to inspect: `src/agent/tools.ts`
- Allowed change scope: require confirmation for tool authority.

## Prohibited Changes

- Do not add new tools.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
