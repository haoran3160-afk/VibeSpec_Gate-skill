# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation not required.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: No auth work

- Finding IDs: `VSG-AUTH-001`
- Files to inspect: `src/app/api/orders/route.ts`
- Allowed change scope: none.

## Prohibited Changes

- Do not change auth.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
