# Agent Fix Plan

## Human Confirmation Gate

- Human confirmation required.
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Rewrite all Electron IPC

- Finding IDs: `VSG-ELECTRON-001`
- Files to inspect: `src/main/ipc.ts`
- Allowed change scope: rewrite all IPC handlers and preload behavior across the app.

## Prohibited Changes

- Do not remove tests.

## Verification Commands

```powershell
py -3 -m pytest -q -p no:cacheprovider
```
