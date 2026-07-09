# Launch Risk Report

Stub status: {{STUB_STATUS}}

Launch decision: {{LAUNCH_DECISION: BLOCK|REVIEW|PASS_WITH_WARNINGS|PASS}}

## Review Scope

- Input packet: `llm_review_packet.json`
- Rule findings role: baseline hints, not final judgment
- External model/API called: {{YES_OR_NO}}

## Findings

### {{FINDING_ID}}: {{TITLE}}

- Severity: {{SEVERITY: P0|P1|P2|P3|Info}}
- Launch impact: {{LAUNCH_IMPACT: block|review|warning|none}}
- Confidence: {{CONFIDENCE: high|medium|low}}
- Evidence files: {{EVIDENCE_FILES}}
- Confirmed risk: {{CONFIRMED_RISK}}
- Likely true risk: {{LIKELY_TRUE_RISK}}
- Needs review: {{NEEDS_REVIEW}}
- Downgrade candidate: {{DOWNGRADE_CANDIDATE}}
- Suppression candidate: {{SUPPRESSION_CANDIDATE}}
- Missing evidence: {{MISSING_EVIDENCE}}
- Recommended action: {{RECOMMENDED_ACTION}}

## Safety Notes

- `safe_to_auto_suppress`: false
- Do not include offensive instructions.

