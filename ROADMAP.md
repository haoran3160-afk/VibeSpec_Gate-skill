# Roadmap

## Current Stage

```text
Stage: Release candidate hardening
Default package: prompt-only Agent-native Skill
Optional overlay: Core-powered repository CLI
Public GA: not claimed
```

## Near Term

- Keep the Lite package manifest and verifier aligned.
- Run controlled external pilot sessions with real users.
- Replace simulated usability evidence with real blind-session evidence.
- Expand validation coverage across SaaS, Agent/MCP, Supabase/Firebase, Electron/Desktop, upload/logging, and low-risk projects.
- Document host-Agent variance.

## Mid Term

- Add a reproducible package builder from `docs/design/lite_skill_package_manifest.md`.
- Publish a small release artifact for the prompt-only Lite package.
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

