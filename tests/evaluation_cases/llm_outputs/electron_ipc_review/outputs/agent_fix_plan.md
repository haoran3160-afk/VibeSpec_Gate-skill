# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required before editing Electron IPC boundaries.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Verify Electron IPC file boundary

- Finding IDs: `VSG-ELECTRON-001`
- Files to inspect: `src/main/ipc.ts`, preload entry, Electron window config.
- Allowed change scope: add schema validation and constrain file paths for this IPC handler.
- Missing evidence to confirm first: contextIsolation setting and allowed workspace root.

## Prohibited Changes

- Do not broaden renderer access.
- Do not disable contextIsolation.
- Do not add unrelated IPC channels.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
