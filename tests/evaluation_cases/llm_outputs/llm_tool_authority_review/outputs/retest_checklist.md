# Retest Checklist

## Commands To Rerun

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\llm_tool_authority_review\outputs --final
py -3 -m pytest -q -p no:cacheprovider
```

## Evidence To Inspect

- Finding IDs: `VSG-AGENT-001`
- Evidence files: `src/agent/tools.ts`
- Expected gate change: BLOCK can clear only after confirmation and allowlist evidence exists.

## Manual Checks

- Confirm high-risk tools require user confirmation.
- Confirm tool authority is bounded by explicit allowlists.

## Safety

- `safe_to_auto_suppress`: false
