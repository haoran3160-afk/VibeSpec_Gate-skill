# Launch Risk Report

Launch decision: REVIEW

## Findings

### VSG-ELECTRON-001

- Severity: P1
- Launch impact: review
- Confidence: medium
- Evidence files: `src/main/ipc.ts`
- Confirmed risk: privileged IPC boundary.
- Missing evidence: contextIsolation and path constraints.
- Recommended action: verify_before_fix.

`safe_to_auto_suppress`: false
