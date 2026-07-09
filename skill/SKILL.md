---
name: vibespec-gate
description: LLM-native security review Skill for vibe coding products. Use to review AI-built apps, SaaS projects, AI Agents, MCP/IPC tools, Electron apps, and local tools for launch-blocking security or data-safety risks, then produce plain-language launch decisions and Agent-ready repair plans.
---

# VibeSpec Gate

Follow the root `SKILL.md` instructions.

VibeSpec Gate helps users decide whether a vibe coding product is safe enough to launch and what a coding Agent can fix after human confirmation.

Always focus on:

- leaked secrets and sensitive data exposure;
- login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks;
- missing auth and broken ownership checks;
- unsafe database rules and deployment config;
- excessive LLM/Agent/MCP/Electron authority;
- clear launch decision and repair priority for non-security users.

When deeper evidence is available, `llm_review_packet.json` is the LLM-native handoff packet for model-assisted review workflows.

Never generate exploit payloads, bypass instructions, credential theft guidance, or unauthorized scan plans. Mask complete secrets and state that the result is a launch-risk review, not a guarantee of absolute security or formal compliance.
