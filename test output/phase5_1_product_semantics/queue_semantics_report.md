# Queue Semantics Report

Generated on 2026-07-07.

## Product Fix

`human_review_queue.md` now includes only:

- `needs_human_review` P0/P1 items.
- `confirmed` or `likely_true` P0/P1 items with recommended action `fix`.

It excludes:

- `should_downgrade`
- `false_positive`
- `suppress`
- downgrade-only decisions

Those excluded decisions are recorded in `agent_review_decisions.md`.

## Phase 4 Output Compression

| Project | Reviewed findings | Human queue items | Agent decisions covered |
| --- | ---: | ---: | ---: |
| personal-voice-light-agent | 36 | 7 | 36 |
| personal-claude-ipc-mcp | 21 | 6 | 21 |
| agent-programs-file-manager | 27 | 6 | 27 |

## Summary Counts

| Project | must_review_count | agent_decision_count | downgrade_candidate_count | suppression_candidate_count |
| --- | ---: | ---: | ---: | ---: |
| personal-voice-light-agent | 7 | 36 | 17 | 25 |
| personal-claude-ipc-mcp | 6 | 21 | 13 | 13 |
| agent-programs-file-manager | 6 | 27 | 21 | 7 |

## Regression Test

`tests/test_review_runner.py::test_product_queue_semantics_do_not_expand_to_all_findings` verifies:

- `human_review_queue.md` is not equal to all reviewed findings.
- Downgrade and suppression findings do not appear in the queue.
- `agent_review_decisions.md` includes every reviewed finding id.
- Downgrade/suppress decisions do not count toward `must_review_count`.
- `safe_to_auto_suppress` stays false in verdicts and suppression candidates.
