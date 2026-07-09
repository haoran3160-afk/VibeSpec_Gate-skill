# Quickstart

VibeSpec Gate is an LLM-native security review Skill. The CLI provides evidence collection, deterministic checks, and repeatable review outputs that the Skill or an Agent can reason over.

## Install For Local Development

```bash
python -m pip install -e .
```

Without installation:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec scan .\tests\fixtures\vulnerable_next_supabase_app --output .\outputs\example-next
```

## Basic Gate Flow

```bash
vibesec scan tests/fixtures/vulnerable_next_supabase_app --output outputs/demo-next
vibesec gate outputs/demo-next/findings.json
vibesec loop tests/fixtures/vulnerable_next_supabase_app --previous outputs/demo-next/findings.json --output outputs/demo-loop
```

This creates findings, reports, repair prompts, and a launch gate decision.

## Agent-Native Review Flow

After a scan, build structured review evidence and decision ledgers:

```powershell
vibesec review outputs/demo-next/findings.json --project tests/fixtures/vulnerable_next_supabase_app --output outputs/demo-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibesec review-validate outputs/demo-review
```

The command above is the deterministic CLI baseline. In a full Skill runtime, use the generated evidence plus LLM reasoning to explain the risk, confirm uncertainty, and prepare bounded repair tasks.

Read:

- `llm_review_packet.json` for product profile, sensitive assets, attack surfaces, auth/data context, Agent/tool surfaces, and rule findings marked as baseline hints.
- `human_review_queue.md` for high-value confirmation tasks.
- `agent_review_decisions.json` for stable Agent/UI fields such as `decision_type`, `must_review`, `blocks_launch`, `safe_for_agent_fix`, and `agent_next_step`.
- `agent_review_decisions.md` for the same decision ledger in human-readable form.
- `docs/usage/llm_review_contract.md` before asking a model or host Agent to produce final review outputs from the packet.

Build a host-agent workspace:

```powershell
py -3 scripts\build_llm_review_workspace.py outputs/demo-review
```

For contract testing without a model:

```powershell
py -3 scripts\stub_llm_review_outputs.py outputs/demo-review/llm_review_workspace
py -3 scripts\validate_llm_review_outputs.py outputs/demo-review/llm_review_workspace
```

The stub outputs are only schema/safety test fixtures. They are not completed LLM security review results.

## What To Ask The Skill

Useful user prompts:

```text
Review this vibe coding product for launch-blocking security risks.
Tell me whether this can leak user data or API keys.
Find the security issues that would let someone bypass auth or read other users' records.
Create a prioritized fix plan for Codex/Cursor/Claude.
After these fixes, retest and tell me if the gate improves.
```

## Release Verification

Before a baseline commit or release candidate:

```powershell
py -3 scripts\verify_release.py
```
