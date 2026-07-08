---
name: vibesec-gate
description: LLM-native security review Skill for vibe-coded products. Use to review AI-built apps, SaaS projects, AI Agents, MCP/IPC tools, Electron apps, and local tools for launch-blocking security or data-safety risks, then produce plain-language explanations, gate decisions, and Agent-ready repair plans.
---

# VibeSec Gate

Follow the root `SKILL.md` instructions.

VibeSec Gate is not just a local scanner. It is an LLM-native review Skill that helps users decide whether a vibe-coded product is safe enough to launch and what an Agent should fix first.

Use the bundled resources as support:

- `skill/checklists/`: review prompts and risk checklists.
- `skill/templates/`: output and repair-task templates.
- `skill/rules/risk_scoring.yaml`: severity and gate guidance.
- `src/vibesec/`: CLI evidence extraction, deterministic review baseline, and regression support.
- `docs/usage/llm_review_contract.md`: `llm_review_packet.json` input and required LLM output contract.
- `docs/design/model_invocation_strategy.md`: host-agent, API-backed, local/private, and no-model baseline boundaries.
- `scripts/build_llm_review_workspace.py`: create a host-agent workspace from a review output directory.
- `scripts/validate_llm_review_outputs.py`: validate completed or stub LLM output files.
- `scripts/score_llm_review_outputs.py`: score completed host-agent outputs against `expected_quality.json`.
- `scripts/build_llm_quality_matrix.py`: build the Phase 9 LLM output quality matrix.
- `scripts/compare_host_agent_samples.py`: compare manually supplied host-agent samples without invoking providers.
- `docs/usage/llm_quality_human_review.md`: ten-minute human calibration loop for golden and bad outputs.

Always focus on:

- leaked secrets and sensitive data exposure;
- missing auth and broken ownership checks;
- unsafe database rules and deployment config;
- excessive LLM/Agent/MCP/Electron authority;
- clear launch decision and repair priority for non-security users.

Never generate exploit payloads, bypass instructions, credential theft guidance, or unauthorized scan plans. Mask complete secrets and state that the result is a launch-risk review, not a guarantee of absolute security or formal compliance.
