# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\secret_runtime_block\outputs --final
py -3 -m vibespec_gate.cli scan . --output outputs/retest --no-adapters
```

## Evidence To Inspect

- Finding IDs: `VSG-SEC-001`
- Evidence files: `src/server.ts`
- Expected gate change: BLOCK should clear only after the literal is gone and rotation is confirmed.

## Manual Checks

- Confirm the production key was rotated if it was active.
- Confirm the deployment secret exists in the target environment.

## Safety

- `safe_to_auto_suppress`: false
