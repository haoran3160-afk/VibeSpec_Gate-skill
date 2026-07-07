# Phase 5.1 Design Summary

Generated on 2026-07-07.

## Objective

Phase 5.1 fixes the product semantics regression introduced by Phase 5: `human_review_queue.md` had become a full decision ledger. The queue is now compact again and contains only high-value findings that require human confirmation before an agent prepares a fix.

## Output Contract

The review command now writes:

- `review_packets.json`: local, redacted evidence packets.
- `ai_review.json`: structured verdicts with `agent_next_step`, files to inspect, prohibited changes, verification suggestions, and `safe_to_auto_suppress=false`.
- `human_review_queue.md`: compact must-review/fix-after-confirmation queue only.
- `agent_review_decisions.md`: complete decision ledger for all reviewed findings.
- `suppression_candidates.json`: advisory candidates only, never auto-applied.
- `ai_review_summary.md`: product-level counts for queue and decision surfaces.

## Summary Field Changes

`ai_review_summary.md` and the returned summary now include:

- `must_review_count`
- `agent_decision_count`
- `downgrade_candidate_count`
- `suppression_candidate_count`

`human_queue_count` remains in the JSON summary as a compatibility alias for `must_review_count`.

## Safety Boundaries

- No external LLM or API calls.
- No source uploads.
- No real project writes.
- No automatic suppression file writes.
- Downgrade and suppression candidates are decisions for review, not must-fix queue entries.
