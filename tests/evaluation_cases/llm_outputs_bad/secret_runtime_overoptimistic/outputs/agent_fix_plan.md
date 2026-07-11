# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation not required.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: No immediate fix

- Finding IDs: none
- Files to inspect: `src/server.ts`
- Allowed change scope: none.

## Prohibited Changes

- Do not change anything.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
