# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\missing_auth_review\outputs --final
py -3 -m pytest -q -p no:cacheprovider
```

## Evidence To Inspect

- Finding IDs: `VSG-AUTH-001`
- Evidence files: `src/app/api/orders/route.ts`
- Expected gate change: REVIEW can clear after auth and ownership are evidenced.

## Manual Checks

- Confirm unauthenticated users cannot read orders.
- Confirm users cannot read other users' orders.

## Safety

- `safe_to_auto_suppress`: false
