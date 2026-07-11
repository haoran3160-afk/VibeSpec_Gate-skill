# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required before changing auth or ownership behavior.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Verify and harden order route protection

- Finding IDs: `VSG-AUTH-001`
- Files to inspect: `src/app/api/orders/route.ts`, middleware files, auth helpers.
- Allowed change scope: add or reuse session and ownership checks for this route only.
- Missing evidence to confirm first: route middleware and intended tenant model.

## Prohibited Changes

- Do not weaken existing authorization.
- Do not migrate data or change schemas without explicit approval.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
py -3 -m vibespec_gate.cli scan . --output outputs/retest --no-adapters
```
