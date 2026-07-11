# Launch Risk Report

Launch decision: PASS_WITH_WARNINGS

## Findings

### VSG-SEC-002: Placeholder secret in example env file

- Severity: P2
- Launch impact: warning
- Confidence: medium
- Evidence files: `.env.example`
- Confirmed risk: example material contains secret-shaped text.
- Likely true risk: low launch impact because the source type is example.
- Needs review: confirm no real matching key exists.
- Downgrade candidate: yes.
- Suppression candidate: after human confirmation only.
- Missing evidence: whole-repo check for matching runtime credentials.
- Recommended action: downgrade.

## Safety Notes

- Human confirmation required before suppression.
- `safe_to_auto_suppress`: false
