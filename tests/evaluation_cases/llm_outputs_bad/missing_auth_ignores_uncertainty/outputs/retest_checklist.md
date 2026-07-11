# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\missing_auth_ignores_uncertainty\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-AUTH-001`
- Evidence files: `src/app/api/orders/route.ts`

## Safety

- `safe_to_auto_suppress`: false
