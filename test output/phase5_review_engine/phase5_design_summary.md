# Phase 5 Design Summary

Generated on 2026-07-06.

## Objective

Phase 5 turns the review layer into an agent-native, offline, rule-based review engine. The outputs are designed for Codex, Claude, Cursor, Gemini CLI, or a human reviewer to consume before any real-project edit is attempted.

## Constraints Preserved

- No internal or default external LLM provider was added.
- `run_review(...)` and `vibesec review` remain backward compatible at the call surface.
- Review remains deterministic and offline.
- `safe_to_auto_suppress` remains false for verdicts and suppression candidates.
- Reports and generated artifacts stay inside `D:\personal\Vibespec_gate_skill`.

## Module Design

- `src/vibesec/core/review_runner.py`: orchestration only. Loads findings, builds packets, invokes rubrics, writes outputs, validates schema.
- `src/vibesec/core/review_packets.py`: packet construction, snippet capture, source-safe path handling, redaction, rubric routing helpers, text signals.
- `src/vibesec/core/review_rubrics.py`: rule-based verdict logic for secrets, auth, Desktop/Electron, MCP/IPC, LLM/Agent, deployment, dependency, config, and generic findings.
- `src/vibesec/core/review_outputs.py`: human queue markdown, suppression candidate generation, review summaries, counts, and gate-impact text.
- `src/vibesec/core/review_schema.py`: stricter schema validation for packets, verdicts, suppression candidates, redaction, and agent-next-step contracts.

## Agent-Native Contract

Every `ai_review.json` verdict now includes:

- `agent_next_step`
- `inspect_files`
- `prohibited_changes`
- `verification_commands`

The contract intentionally guides an agent to verify local evidence before editing and to treat downgrade/suppression decisions as confirmation tasks, not automatic changes.
