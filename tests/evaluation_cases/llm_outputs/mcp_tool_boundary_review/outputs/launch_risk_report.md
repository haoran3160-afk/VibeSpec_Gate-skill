# Launch Risk Report

Launch decision: REVIEW

## Findings

### VSG-MCP-001: MCP file tool boundary needs review

- Severity: P1
- Launch impact: review
- Confidence: medium
- Evidence files: `src/mcp/server.ts`
- Confirmed risk: local file tool authority exists.
- Likely true risk: possible boundary gap.
- Needs review: schema, allowlist, path constraints, and caller scope.
- Downgrade candidate: if controls are present.
- Suppression candidate: no.
- Missing evidence: complete argument schema and explicit allowlist.
- Recommended action: verify_before_fix.

## Safety Notes

- Human confirmation required before editing tool boundaries.
- `safe_to_auto_suppress`: false
