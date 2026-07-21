# Roadmap

## Current Stage

```text
Stage: 0.2.0rc2 controlled release candidate
Default package: prompt-only Agent-native Skill
Optional overlay: Core-powered repository CLI
Public GA: not claimed
```

## Near Term

- Monitor the `0.2.0rc2` package, activation contract, and cross-platform CI for regressions.
- Keep the verified Lite zip and checksum reproducible through the tag-gated GitHub Release workflow.
- Run controlled external pilot sessions with real users.
- Collect real blind-session evidence; synthetic walkthroughs remain contract tests only.
- Expand validation coverage across SaaS, Agent/MCP, Supabase/Firebase, Electron/Desktop, upload/logging, and low-risk projects.
- Document host-Agent variance.

## Mid Term

- Keep the reproducible package builder and archive validator aligned with the Lite manifest.
- Promote an RC to GA only after real external pilot evidence and release gates pass.
- Improve real-project validation summaries without committing raw generated output.
- Add more regression cases for false confidence and over-blocking.

## Later

- Decide whether the Core-powered CLI overlay should become a separate package.
- Add richer integration with host Agents where safe and authorized.
- Expand maintainer calibration only when it improves user-facing decisions.

## Non-Goals

- Offensive exploitation.
- Unauthorized scans.
- Claims of certification or compliance.
- Broad repo restructuring before package boundaries are stable.
