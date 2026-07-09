# Agent Review Cookbook

VibeSpec Gate is an LLM-native security review Skill for vibe coding products. The CLI can generate structured evidence, but the product value comes from model-assisted security judgment, prioritization, explanation, and repair planning.

## Common Flow

In an Agent environment, ask:

```text
Review this project as VibeSpec Gate. Identify launch-blocking security or data-safety risks, explain them for a non-security user, and prepare an Agent-ready fix plan.
```

When CLI evidence is useful:

```powershell
vibespec-gate scan ./my-project --output ./outputs
vibespec-gate review ./outputs/findings.json --project ./my-project --output ./outputs-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibespec-gate review-validate ./outputs-review
```

The CLI review command is the deterministic baseline. The Skill should use the generated packets and decision ledgers as evidence, then apply LLM reasoning to validate context and plan repairs.

Use:

- `llm_review_packet.json` as the LLM-native review input packet.
- `human_review_queue.md` for human confirmation.
- `agent_review_decisions.json` for tools, agents, or UI.
- `agent_review_decisions.md` when a human wants the full decision ledger.

Treat `rule_findings[*].evidence_role=baseline_hint_not_final_judgment` literally. Rule findings identify evidence to inspect; they do not decide final launch risk without model/context review.

## Web / SaaS Projects

Review:

- auth middleware and protected routes;
- object ownership checks;
- Supabase RLS and service-role key placement;
- Firebase rules;
- CORS, cookies, sessions, headers, uploads, and logs;
- environment variables and deployment config.

For auth findings:

- `must_review=true` means confirm route middleware, ownership checks, RLS, Firebase rules, or equivalent guards before preparing a fix.
- `decision_type=downgrade_candidate` means local evidence suggests the finding should not block launch at P1, but a human still confirms before changing records.

## LLM / Agent Projects

Tool authority findings usually fall into three groups:

- Plain chat without tools: downgrade candidate.
- Tool call with immediate user confirmation or allowlist: verify the boundary before fixing.
- Autonomous file, shell, database, email, or payment tool without confirmation: fix after confirmation.

Do not treat scanner title text such as "approval missing" as approval evidence. The review packet or project code should show runtime confirmation logic near the tool call.

## Desktop / Electron Projects

Use the queue for:

- `nodeIntegration: true`;
- `contextIsolation: false`;
- broad preload APIs;
- LLM/tool-reachable file operations;
- IPC handlers that cross renderer/main trust boundaries.

Typical handling:

- `nodeIntegration: true`: confirm and prepare a hardening fix.
- `contextIsolation: false`: confirm and prepare a hardening fix.
- Broad preload API: verify renderer reachability, schema, and path boundaries.
- User-selected constrained workspace path: usually a downgrade candidate, not a must-fix queue item.

## MCP / IPC Projects

For MCP and IPC boundaries, downgrade only when the evidence shows schema validation, explicit allowlist, and local process/user boundary evidence.

Handle common cases this way:

- Dynamic tool name without allowlist: must review.
- Schema but no allowlist: must review.
- Allowlist but no argument schema: must review.
- Schema plus allowlist plus local-only process boundary: downgrade candidate.

## Passing Work To Humans And Agents

Give `human_review_queue.md` to a human reviewer. It is compact by design and contains only high-value confirmation tasks.

Give `llm_review_packet.json` to a host Agent or explicitly configured model runtime when final LLM review outputs are needed. The required output contract is documented in `docs/usage/llm_review_contract.md`.

Give `agent_review_decisions.json` to automation. Each decision includes:

- `schema_version` at the top-level contract.
- `decision_type`
- `must_review`
- `agent_next_step`
- `blocks_launch`
- `safe_for_agent_fix`
- `inspect_files`
- `prohibited_changes`
- `verification_commands`
- `safe_to_auto_suppress`

Agents should inspect listed files, confirm evidence, then prepare bounded repair tasks. They should not blindly edit or suppress.

## Host-Agent Workspace

Create a workspace when a host Agent needs a direct prompt and output templates:

```powershell
py -3 scripts\build_llm_review_workspace.py ./outputs-review
```

The workspace contains:

- `llm_review_packet.json`
- `llm_review_prompt.md`
- `output_templates/`
- `README.md`

The builder does not call external model/API providers and does not copy large project source into the workspace.

For schema and safety contract testing:

```powershell
py -3 scripts\stub_llm_review_outputs.py ./outputs-review/llm_review_workspace
py -3 scripts\validate_llm_review_outputs.py ./outputs-review/llm_review_workspace
```

Do not confuse stub outputs with a completed review. Real host-agent outputs must replace the stub content before making launch-risk claims.

## Evaluating Real Host-Agent Outputs

Use Phase 9 fixtures and scoring when host-agent outputs are meant to be completed review artifacts:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs\secret_runtime_block
py -3 scripts\build_llm_quality_matrix.py
```

The scorer checks launch decision consistency, finding IDs, evidence files, missing evidence, bounded Agent tasks, prohibited changes, verification commands, `safe_to_auto_suppress=false`, and absence of the Phase 8 stub disclaimer.

Treat the score as regression evidence. It does not make the review professionally certified, legally complete, or absolutely secure.

Phase 10 adds adversarial fixtures:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\secret_runtime_overoptimistic
py -3 scripts\compare_host_agent_samples.py "test output\phase10_host_agent_quality_expansion\host_agent_samples"
```

Bad fixtures should fail for declared reasons. Manually supplied host-agent samples can be placed under `host_agent_samples\<agent>\<case_id>` and compared with the same scorer. The comparator only reads files; it never invokes a provider.

## Suppression Safety

Suppression and false-positive decisions are advisory. Do not write `vibespec_gate.suppressions.json` automatically. `safe_to_auto_suppress` is always false and must remain false unless a future reviewed design changes the safety contract.

## Interpreting Review Count Changes

When a rubric changes, compare:

- `must_review_count`
- `downgrade_candidate_count`
- `suppression_candidate_count`
- `agent_decision_count`

Then inspect `test output/phase7_release_hardening/review_count_change_log.md` and the evaluation matrix. A larger queue can be correct when a rubric becomes stricter, for example when MCP downgrade now requires schema, allowlist, and local process boundary evidence.

## Baseline Workflow

Before creating a baseline commit:

```powershell
py -3 scripts\verify_release.py
git status --short --ignored
```

Review `test output/phase7_release_hardening/baseline_commit_readiness.md`. Stage selectively; do not use `git add .`.
