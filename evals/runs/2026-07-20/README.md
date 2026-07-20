# Skill Evaluation Run: 2026-07-20

This run used fresh `multi_agent_v1` tasks. Positive and behavior tasks requested the installed Skill at `$HOME/.agents/skills/vibespec-gate`. Negative tasks were rerun with that standard installation present and discoverable for normal host routing, but without explicit invocation or attachment; all five self-reported that VibeSpec Gate was not activated.

The exact model id, Skill activation event, and intermediate tool/write-event stream were not exposed by the host tool. Some executed requests also contain harness-specific scope text that differs from the checked-in case prompt. Each record preserves the actual request, unedited final output, task id, Skill HEAD/tree hash, and before/after fixture hashes. The fixture hashes did not change, but the unavailable host events mean activation and no-write claims cannot be independently verified.

Results:

- Trigger matrix: 10/10 `PENDING`; outputs exist, but host-observable activation evidence is unavailable.
- Behavior matrix: 8/8 `PENDING`; outputs are reviewable and fixture hashes are unchanged, but exact prompt matching and write-event evidence are incomplete.
- Failed attempts retained: 4. These drove the MCP fixture isolation, MCP `REVIEW` precision rule, standard-path installation smoke, and one host retry.
- Real-user controlled trial: `PENDING`; these Agent runs do not count as real users.

These outputs remain scenario evidence, not Skill-readiness evidence. The prewritten `write_prompt_only_outputs()` artifacts are not included in these results either.
