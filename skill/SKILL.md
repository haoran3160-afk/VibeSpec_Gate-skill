---
name: vibesec-gate
description: Defensive pre-launch security gate for user-owned vibe-coded web apps, SaaS projects, and AI Agent apps. Use when asked to review a local project for leaked secrets, missing authentication, Supabase/Firebase permission mistakes, unsafe deployment config, dependency hygiene, and LLM/Agent security boundaries, then produce beginner explanations, developer repair guidance, Codex fix tasks, and a PASS/REVIEW/BLOCK gate decision.
---

# VibeSec Gate

Follow the root `SKILL.md` instructions. Use the checklists in `skill/checklists/`, templates in `skill/templates/`, and severity rules in `skill/rules/risk_scoring.yaml`.

Never generate exploit payloads or scan unauthorized third-party systems. Always mask secrets and state that results are a basic pre-launch gate, not a professional security audit.
