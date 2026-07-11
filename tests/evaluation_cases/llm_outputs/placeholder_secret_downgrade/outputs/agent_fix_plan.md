# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required before suppressing or downgrading `VSG-SEC-002`.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Clarify example secret placeholder

- Finding IDs: `VSG-SEC-002`
- Files to inspect: `.env.example`
- Allowed change scope: replace the placeholder with an obviously fake value and add a comment.
- Missing evidence to confirm first: no real matching runtime secret.

## Prohibited Changes

- Do not add real credentials.
- Do not write suppression files automatically.

## Verification Commands

```powershell
py -3 -m vibespec_gate.cli scan . --output outputs/retest --no-adapters
```
