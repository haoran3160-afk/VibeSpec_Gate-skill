# VibeSec Gate

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Package mode](https://img.shields.io/badge/package-prompt--only%20Skill-green)](#default-lite-package)
[![Security boundary](https://img.shields.io/badge/security-not%20a%20certification-orange)](#safety-boundary)

VibeSec Gate is an **LLM-native security review Skill for AI-built products**.

Use it before launch when you need a practical answer to one question:

> Can this app leak secrets, expose user data, ship broken auth, or give an Agent/tool too much authority?

VibeSec Gate reviews project evidence and produces:

- a launch decision;
- the top security and data-safety risks;
- bounded coding-Agent fix tasks after human confirmation;
- a retest checklist.

## Default Lite Package

The default Lite package is **prompt-only** and **Agent-native**. A first-time user does not need to install the Python project, run repository tests, inspect scorer output, read calibration data, or use release tooling.

Use it like this:

1. Install or copy the Lite package into your Agent environment.
2. Ask the Agent to review your project with `examples/lite_review_prompt.md`.
3. Read the generated Lite review files.

Starter prompt:

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

Expected output:

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

## Read The Results

Read the generated files in this order:

1. `launch_decision.md`: whether the project is blocked, needs review, can launch with warnings, or can pass.
2. `top_security_risks.md`: the highest-impact risks and affected evidence.
3. `agent_fix_plan.md`: bounded fix tasks for a coding Agent, after human confirmation.
4. `retest_checklist.md`: checks to run after fixes.

Launch decision meanings:

- `BLOCK`: do not launch yet; one or more findings currently block launch.
- `REVIEW`: do not treat as launch-ready yet; human confirmation or missing evidence remains.
- `PASS_WITH_WARNINGS`: no launch blocker is present, but warnings remain.
- `PASS`: no material launch risk was found in the reviewed evidence.

## Safety Boundary

`agent_fix_plan.md` is a repair plan, not permission for blind edits.

- Confirm evidence before asking a coding Agent to change the project.
- Do not auto-write suppressions.
- Do not broaden permissions, remove validation, add bypasses, or mutate production systems while fixing.
- Retest with `retest_checklist.md` after fixes.
- Do not treat VibeSec Gate as a professional security certification, penetration test, legal review, or compliance attestation.

## What It Reviews

VibeSec Gate focuses on launch-impacting issues:

- exposed API keys, service-role keys, database URLs, and credentials;
- missing auth, broken ownership checks, and unsafe database rules;
- risky CORS, cookie, session, header, upload, logging, and deployment config;
- prompt or prompt-log exposure;
- excessive Agent, MCP/IPC, Electron, shell, file, email, database, or payment tool authority;
- uncertainty that needs human confirmation before launch.

## Optional Core-Powered Path

The full repository also provides an optional Core-powered CLI overlay for deterministic local evidence generation:

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

The CLI is repository infrastructure. It is not required for the default prompt-only Skill package.

## Documentation

Start here:

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Lite review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](docs/usage/agent_review_cookbook.md)
- [Documentation index](docs/README.md)

For maintainers:

- [Lite package manifest](docs/design/lite_skill_package_manifest.md)
- [Lite package verification](docs/maintainers/lite_package_verification.md)
- [Release verification](docs/maintainers/release_verification.md)

## Local Development

Install from a source checkout:

```bash
python -m pip install -e .
```

Verify the Lite package boundary:

```powershell
py -3 scripts\verify_lite_package.py
```

Run focused tests:

```powershell
py -3 -m pytest tests/test_lite_package_verifier.py tests/test_lite_release_validation.py tests/test_lite_review_bundle.py tests/test_lite_rc_hardening.py
```

Repository layout:

```text
.
|-- SKILL.md
|-- examples/
|-- skill/
|-- src/vibesec/
|-- scripts/
|-- tests/
|-- docs/
`-- .github/
```

Generated folders such as `outputs/` and `test output/` are intentionally ignored by Git.

## Governance

- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## License

No open-source license has been selected yet. Until a `LICENSE` file is added, do not assume reuse, redistribution, or relicensing rights.

