# VibeSpec Gate Quickstart

VibeSpec Gate reviews authorized project evidence and returns coverage, one launch decision, the highest-impact risks, human-gated repair tasks, and project-specific retests.

## Install

Recommended:

```text
Use $skill-installer to install the Skill from https://github.com/haoran3160-afk/VibeSpec_Gate-skill/tree/master/skills/vibespec-gate.
```

Open a new Agent task after installation. `$skill-installer` defaults to `$CODEX_HOME/skills/vibespec-gate`, normally `$HOME/.codex/skills/vibespec-gate`. Manual installs may use `$HOME/.agents/skills/vibespec-gate`; a repository-specific installation uses `.agents/skills/vibespec-gate`.

Manual Windows PowerShell installation from a source checkout:

```powershell
$Target = Join-Path $HOME ".agents/skills/vibespec-gate"
if (Test-Path -LiteralPath $Target) { throw "Target already exists: $Target" }
New-Item -ItemType Directory -Force (Split-Path -Parent $Target) | Out-Null
Copy-Item -LiteralPath "skills/vibespec-gate" -Destination $Target -Recurse
Test-Path -LiteralPath (Join-Path $Target "SKILL.md")
```

Manual macOS or Linux installation:

```bash
test ! -e "$HOME/.agents/skills/vibespec-gate"
mkdir -p "$HOME/.agents/skills"
cp -R skills/vibespec-gate "$HOME/.agents/skills/vibespec-gate"
test -f "$HOME/.agents/skills/vibespec-gate/SKILL.md"
```

Copy the complete directory so both references and all four output templates remain available.

The [`v0.2.0-rc.1` Release](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/tag/v0.2.0-rc.1) also provides [`vibespec-gate-lite.zip`](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/download/v0.2.0-rc.1/vibespec-gate-lite.zip) and [`SHA256SUMS`](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/download/v0.2.0-rc.1/SHA256SUMS). Verify the checksum before installing the extracted `vibespec-gate/` directory.

## Start In Chat

Open the product repository in a new Agent task and ask:

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Keep the project read-only. Start with a chat-only result and do not create files.
Show evidence coverage, the launch decision, the highest-impact risks, repair tasks
that require human confirmation, and a project-specific retest checklist.
```

The first result should include all seven surfaces: `auth`, `authorization`, `secrets`, `data_rules`, `deployment`, `agent_tools`, and `desktop_ipc`.

Decision meanings:

- `BLOCK`: confirmed launch-blocking evidence exists.
- `REVIEW`: evidence is insufficient, partial, truncated, ambiguous, or needs human judgment.
- `PASS_WITH_WARNINGS`: coverage is complete and no blocker remains, but a warning remains.
- `PASS`: coverage is complete, no surface is missing, and no material risk or remaining warning was found.

`PASS` is evidence-scoped and is not proof that the product is secure.

## Save Results

Saving is optional. Approve an output directory outside the reviewed project only when you need files. The Agent then creates:

```text
launch_decision.md
top_security_risks.md
agent_fix_plan.md
retest_checklist.md
evidence/
```

Input and output must not be equal or contain one another. Reports can contain paths, snippets, and sensitive context; inspect them manually before sharing.

Review does not authorize repair. Confirm the finding, allowed files, prohibited changes, and product choices before any edit.

## Optional CLI

The source repository also contains a Python 3.10+ CLI for repeatable static checks and structured local evidence. It is not included in the installed Skill and does not replace the Agent's coverage judgment.

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review D:\path\to\project --output D:\reviews\project-review --no-adapters
```

The CLI requires explicit `--output` outside the project, and the target directory must not already exist.

VibeSpec Gate is not a professional security certification, penetration test, legal review, compliance attestation, or guarantee of absolute security.
