# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\electron_ipc_review\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-ELECTRON-001`
- Evidence files: `src/main/ipc.ts`
- Expected gate change: REVIEW can clear after contextIsolation and constrained IPC evidence are present.

## Manual Checks

- Confirm renderer input cannot select arbitrary paths.
- Confirm preload API exposes only bounded operations.

## Safety

- `safe_to_auto_suppress`: false
