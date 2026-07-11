# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\placeholder_secret_downgrade\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-SEC-002`
- Evidence files: `.env.example`
- Expected gate change: warning remains acceptable after placeholder cleanup.

## Manual Checks

- Confirm example value is fake.
- Confirm no real secret was added.

## Safety

- `safe_to_auto_suppress`: false
