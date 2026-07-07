# Agent-Native Output Report

Generated on 2026-07-06.

## Verdict Fields

Each verdict in `ai_review.json` now includes:

- `agent_next_step`
- `inspect_files`
- `prohibited_changes`
- `verification_commands`

## Agent Next Step Mapping

- `confirmed` plus `fix`: `prepare_fix_task`
- `likely_true` plus `fix`: `confirm_and_prepare_fix`
- `needs_human_review`: `verify_before_fix`
- `should_downgrade` or `false_positive`: `confirm_before_suppress_or_downgrade`

## Human Queue Layout

`human_review_queue.md` is organized into:

- Must confirm before fix
- Likely true, fix after confirmation
- Downgrade candidates
- Suppression candidates

Each item includes the finding id, reason, files to inspect, human questions, prohibited changes, and verification suggestions.

## Safety Behavior

The outputs tell agents to verify local evidence before editing real projects. Suppression and downgrade candidates remain advisory and require confirmation. `safe_to_auto_suppress` is false everywhere.

## Phase 4 Output Refresh

The existing Phase 4 review outputs were regenerated with the Phase 5 schema so `review-validate` continues to pass on:

- `personal-voice-light-agent`: 36 packets, 25 suppression candidates
- `personal-claude-ipc-mcp`: 21 packets, 13 suppression candidates
- `agent-programs-file-manager`: 27 packets, 7 suppression candidates
