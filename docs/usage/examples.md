# Examples

These examples show how the CLI supports the LLM-native VibeSec Gate Skill.

## Ask For A Launch Security Review

Use this when working inside Codex, Claude, Cursor, or another Agent environment:

```text
Review this project as VibeSec Gate. Tell me whether it can safely launch, what could leak secrets or user data, and what an Agent should fix first.
```

The Skill should inspect project evidence, explain launch risk, and produce a prioritized repair plan.

## Generate Local Evidence

```bash
vibesec scan ./my-project --output ./outputs
```

This creates `findings.json`, user/developer reports, fix tasks, and a gate summary.

## Force An AI-Agent Profile

```bash
vibesec scan ./my-agent --mode ai-agent --output ./outputs-agent
```

Use this when the project has LLM tool calls, autonomous actions, shell/file/database/email/payment tools, or prompt-sensitive workflows.

## Rebuild Reports From Findings

```bash
vibesec report ./outputs/findings.json --output ./outputs
```

## Print The Gate Summary

```bash
vibesec gate ./outputs/findings.json
```

## Build Agent Review Outputs

```bash
vibesec review ./outputs/findings.json --project ./my-project --output ./outputs-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibesec review-validate ./outputs-review
```

This deterministic baseline produces compact queues and complete decision ledgers. A Skill runtime can then use LLM reasoning over those files and the project code.

`llm_review_packet.json` is the LLM-native handoff packet. It combines product profile, sensitive assets, attack surfaces, auth/data context, Agent/tool surfaces, evidence files, and rule findings marked as baseline hints rather than final truth.

`human_review_queue.md` contains only must-review or fix-after-confirmation items.

`agent_review_decisions.json` and `agent_review_decisions.md` cover every reviewed finding, including downgrade and suppression decisions.

## Build A Host-Agent LLM Review Workspace

```powershell
py -3 scripts\build_llm_review_workspace.py ./outputs-review
```

This creates `./outputs-review/llm_review_workspace` with `llm_review_packet.json`, `llm_review_prompt.md`, output templates, and a README. It does not call a model provider or copy project source.

Use the workspace prompt when a host Agent should produce the required LLM-native outputs. For contract testing only:

```powershell
py -3 scripts\stub_llm_review_outputs.py ./outputs-review/llm_review_workspace
py -3 scripts\validate_llm_review_outputs.py ./outputs-review/llm_review_workspace
vibesec llm-output-validate ./outputs-review/llm_review_workspace
```

Stub outputs always state that they are not completed LLM security reviews.

## Consume Structured Decisions

Phase 6+ decision JSON is a versioned object:

```bash
jq '.decisions[] | {finding_id, decision_type, must_review, blocks_launch, safe_for_agent_fix, agent_next_step}' ./outputs-review/agent_review_decisions.json
```

Agents should treat `must_review=true` as a confirmation task before fix preparation. They should not write suppressions automatically; `safe_to_auto_suppress` is always false.

## Retest After Fixes

```bash
vibesec loop ./my-project --previous ./outputs/findings.json --output ./outputs-retest
```

Use the loop output to decide whether the launch gate improved after repairs.
