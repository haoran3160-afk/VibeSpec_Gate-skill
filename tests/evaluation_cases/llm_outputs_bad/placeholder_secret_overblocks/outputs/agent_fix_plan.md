# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Treat example placeholder as blocker

- Finding IDs: `VSG-SEC-002`
- Files to inspect: `.env.example`
- Allowed change scope: edit example placeholder only.

## Prohibited Changes

- Do not add real credentials.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
