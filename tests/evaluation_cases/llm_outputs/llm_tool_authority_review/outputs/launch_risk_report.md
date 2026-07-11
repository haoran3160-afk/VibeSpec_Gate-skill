# Launch Risk Report

Launch decision: BLOCK

## Findings

### VSG-AGENT-001: Agent tool authority needs review

- Severity: P1
- Launch impact: block
- Confidence: high
- Evidence files: `src/agent/tools.ts`
- Confirmed risk: high-risk tool authority is reachable by Agent workflow.
- Likely true risk: yes, because confirmation evidence is missing.
- Needs review: immediate user confirmation and argument allowlists.
- Downgrade candidate: only after confirmation gates are proven.
- Suppression candidate: no.
- Missing evidence: confirmation UI and tool argument constraints.
- Recommended action: fix.

## Safety Notes

- Human confirmation required before changing tool authority.
- `safe_to_auto_suppress`: false
