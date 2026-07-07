# Rubric Precision Report

Generated on 2026-07-06.

## Coverage Added

The review evaluation set now has 17 total cases:

- Desktop/Electron: 4 cases
- MCP/IPC: 4 cases
- LLM/Agent: 4 cases

## Desktop/Electron

Rules sharpened:

- `nodeIntegration: true` returns `likely_true` with fix guidance.
- `contextIsolation: false` returns `likely_true` with fix guidance.
- Broad preload file capability returns `needs_human_review`.
- User-selected and workspace-constrained file paths return `should_downgrade`.
- LLM/tool-reachable file operations without a boundary return `likely_true` or human review depending on evidence.

## MCP/IPC

Rules sharpened:

- Command/file operations are prioritized for `needs_human_review` unless explicit boundaries are proven.
- Schema plus explicit allowlist returns `should_downgrade`.
- Local-only status/process-boundary evidence without risky operation returns `should_downgrade`.
- Missing schema remains `needs_human_review`.

## LLM/Agent

Rules sharpened:

- Plain chat without tools returns `should_downgrade`.
- Explicit approval or confirmation signals return `needs_human_review` instead of blind fix.
- Autonomous shell/file/database/email/payment-style tools without approval return `likely_true`.
- System prompt exposure returns `likely_true`.
- Rate/cost-limit findings return `should_downgrade` to P2.

## Regression Found And Fixed

During testing, the phrase `without approval` was initially treated as an approval signal. The LLM rubric now requires positive confirmation evidence such as `approval is required`, `requires approval`, `user confirmation`, `confirm(`, allowlist, audit, or rate-limit signals.
