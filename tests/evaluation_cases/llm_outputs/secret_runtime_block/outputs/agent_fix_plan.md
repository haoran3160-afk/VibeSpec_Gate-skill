# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required before editing deployment configuration or rotating credentials.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Move runtime secret out of source

- Finding IDs: `VSG-SEC-001`
- Files to inspect: `src/server.ts`
- Allowed change scope: replace the literal with an environment variable lookup and document the required deployment secret.
- Missing evidence to confirm first: active key status and secret-store naming.

## Prohibited Changes

- Do not commit real replacement secrets.
- Do not write suppression files.
- Do not change unrelated auth or billing behavior.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
py -3 -m vibespec_gate.cli scan . --output outputs/retest --no-adapters
```
