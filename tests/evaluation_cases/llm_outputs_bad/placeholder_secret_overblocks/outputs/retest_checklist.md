# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\placeholder_secret_overblocks\outputs --final
```

## Evidence To Inspect

- Finding IDs: `VSG-SEC-002`
- Evidence files: `.env.example`

## Safety

- `safe_to_auto_suppress`: false
