# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required before changing tool authority.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Add confirmation and allowlist for high-risk Agent tools

- Finding IDs: `VSG-AGENT-001`
- Files to inspect: `src/agent/tools.ts`
- Allowed change scope: require confirmation before privileged tool calls and constrain allowed arguments.
- Missing evidence to confirm first: which tools are intended to be autonomous.

## Prohibited Changes

- Do not add new tools.
- Do not broaden file, shell, payment, email, or database access.
- Do not remove audit logging.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
py -3 -m vibespec_gate.cli scan . --output outputs/retest --no-adapters
```
