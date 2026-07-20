# Skill Evaluation Run: 2026-07-20

This run used fresh `multi_agent_v1` tasks. Positive and behavior tasks explicitly invoked the installed Skill at `$HOME/.agents/skills/vibespec-gate`. Negative tasks were rerun with that standard installation present and discoverable for normal host routing, but without explicit invocation or attachment; all five reported that VibeSpec Gate was not activated.

The exact model id and intermediate tool-event stream were not exposed by the host tool. Each record therefore preserves the raw request from the checked-in case definition, the unedited final output, task id, Skill HEAD/tree hash, and before/after fixture hashes. No evaluated fixture changed and no unapproved output file was created.

Results:

- Trigger matrix: 10/10 passed (5 explicit activations, 5 negative non-activations).
- Behavior matrix: 8/8 passed.
- Failed attempts retained: 4. These drove the MCP fixture isolation, MCP `REVIEW` precision rule, standard-path installation smoke, and one host retry.
- Real-user controlled trial: `PENDING`; these Agent runs do not count as real users.

The prewritten `write_prompt_only_outputs()` artifacts are not included in these results and are not Skill-readiness evidence.
