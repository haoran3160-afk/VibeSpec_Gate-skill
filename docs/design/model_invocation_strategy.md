# Model Invocation Strategy

VibeSpec Gate is an LLM-native security review Skill. The current deterministic CLI is evidence, regression, and fallback infrastructure; it is not the full review intelligence.

## Host-Agent Mode

Primary Skill mode for Codex, Claude, Cursor, Gemini CLI, or similar environments.

The host agent:

- reads project files under user-authorized scope;
- uses `vibespec-gate scan` and `vibespec-gate review` when useful to collect evidence;
- consumes `llm_review_packet.json`;
- can use `scripts\build_llm_review_workspace.py` to get a direct prompt and output templates;
- produces the required review outputs in the active workspace;
- respects safety boundaries and does not call hidden providers.

This mode relies on the model context already provided by the host environment.

## API-Backed Mode

Optional future mode. A user may configure a provider explicitly.

Requirements:

- no hidden default provider;
- no automatic upload without user/environment authorization;
- provider, model, and data handling must be visible in configuration;
- packets should be redacted and scoped before sending;
- deterministic CLI output remains available for local verification.

## Local / Private Model Mode

Optional future mode for users who need local or private inference.

Requirements:

- same `llm_review_packet.json` contract;
- same output contract;
- same safety boundaries;
- clear model limitations and uncertainty handling.

## No-Model Deterministic Baseline

The current rule-based CLI review is retained as:

- evidence collection;
- regression baseline;
- release verifier;
- structured packet generator;
- host-agent workspace generator;
- contract stub generator for validation tests;
- fallback when model review is unavailable.

It should not be described as the product ceiling.

## Invocation Boundary

VibeSpec Gate should generate packets and contracts first. Any actual model call must be decided by the host runtime, user configuration, or explicit future provider integration. The CLI must not silently call external LLM/API providers.
