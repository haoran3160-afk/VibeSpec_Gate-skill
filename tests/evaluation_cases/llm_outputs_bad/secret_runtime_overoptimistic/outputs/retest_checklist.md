# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\secret_runtime_overoptimistic\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-SEC-001`
- Evidence files: `src/server.ts`

## Safety

- `safe_to_auto_suppress`: false
