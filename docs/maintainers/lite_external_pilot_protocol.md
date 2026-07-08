# Lite External Pilot Protocol

Use this protocol after RC hardening evidence has been generated.

The current promotion authority is:

```text
test output/lite_rc_hardening/2026-07-08/release_decision.md
```

Do not promote to controlled external pilot while that file says `NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT`.
If blind users are unavailable and the maintainer explicitly accepts simulation, the runner may produce `READY_FOR_CONTROLLED_EXTERNAL_PILOT_SIMULATED`; treat that as internal RC hardening evidence, not as real external user validation.

## Participant Requirements

Run 3 to 5 blind sessions.

Required minimum profile:

- at least one non-security builder;
- at least one developer who uses coding Agents;
- at least one user with an AI/Agent or SaaS project.

Optional:

- one security-aware reviewer for calibration.

## Session Setup

Give the participant only:

```text
test output/lite_rc_hardening/2026-07-08/candidate-lite-package/
```

Do not explain:

- Phase documents;
- scorer;
- calibration;
- fixtures;
- release verifier;
- repository internals.

Ask them to trigger a launch-blocking review on their project or on an agreed demo project.

The RC runner generates supporting pilot materials for the maintainer:

```text
test output/lite_rc_hardening/2026-07-08/pilot_session_materials/
  participant_brief.md
  observer_scorecard.md
  pilot_sessions.example.json
```

Use `participant_brief.md` as the participant-facing task sheet. Use `observer_scorecard.md` to record what happened. Do not include these materials in the Lite package itself unless a future manifest update explicitly allows them.

## Questions To Answer

Record whether the participant can identify:

1. the launch decision;
2. the top risk;
3. the first safe Agent fix task;
4. what must be confirmed by a human;
5. how to retest;
6. that the result is not certification, penetration testing, legal review, or compliance attestation.

## Pass Threshold

The external blind usability gate passes only when:

- at least 3 real sessions are recorded;
- at least 80% can start the review without maintainer help;
- at least 80% can identify the four output files and read order;
- no participant interprets the result as certification;
- no participant believes `agent_fix_plan.md` permits blind edits;
- at least 80% can explain the retest path.

## Simulated Sub-Agent Fallback

When no blind users are available, maintainers may run a structured simulation to exercise the same usability gate:

```powershell
py -3 scripts\run_lite_rc_hardening.py --simulate-subagents
```

The runner generates:

```text
test output/lite_rc_hardening/2026-07-08/simulated_subagent_sessions/
  simulation_summary.md
  *_prompt.md
  *_transcript.md
```

Simulation roles cover:

- non-security product builder;
- developer who uses coding Agents;
- AI/Agent or SaaS builder;
- security-minded reviewer.

Boundary:

- simulated sessions must be marked `source=simulated_subagent`;
- simulated sessions may unblock maintainer-approved RC hardening when blind users are unavailable;
- simulated sessions are not real external blind user evidence;
- record real blind sessions before treating the gate as GA or broad-market validation.

## Recording Format

Use `scripts/run_lite_rc_hardening.py --external-session` to record each session result.

Format:

```powershell
py -3 scripts\run_lite_rc_hardening.py `
  --external-session "non_security_builder:true,true,true,true,true" `
  --external-session "agent_developer:true,true,true,true,true" `
  --external-session "saas_builder:true,true,true,true,true"
```

Fields after the participant name:

```text
started,files,fix,retest,certification_safe
```

Use `true` only when the observation is supported by the session notes.

Preferred format for real evidence is a JSON session file:

```json
{
  "sessions": [
    {
      "name": "participant_non_security",
      "profile": "non_security_builder",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "notes": "Observed from session notes."
    },
    {
      "name": "participant_agent_developer",
      "profile": "coding_agent_developer",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "notes": "Observed from session notes."
    },
    {
      "name": "participant_saas_builder",
      "profile": "ai_agent_or_saas_project",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "notes": "Observed from session notes."
    }
  ]
}
```

Then run:

```powershell
py -3 scripts\run_lite_rc_hardening.py --external-session-file .\pilot_sessions.json
```

The runner also writes a starter template to:

```text
test output/lite_rc_hardening/2026-07-08/external_session_template.json
```

## No-Go Conditions

Do not promote if:

- fewer than 3 real sessions are recorded;
- any user believes the result is certification;
- any user believes Agent fix tasks allow blind edits;
- two or more participants cannot trigger the review without maintainer help;
- repeated confusion points to README, `SKILL.md`, quickstart, or prompt wording.

For a maintainer-approved simulated fallback, the equivalent no-go is `NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT`; the successful simulated state is labeled separately as `READY_FOR_CONTROLLED_EXTERNAL_PILOT_SIMULATED`.

## Evidence

After recording sessions, inspect:

```text
test output/lite_rc_hardening/2026-07-08/pilot_usability_notes.md
test output/lite_rc_hardening/2026-07-08/release_decision.md
```

Only `release_decision.md` can promote the RC to controlled external pilot readiness.

## Optional Real-Project Read-Only Validation

With explicit authorization, maintainers may run the RC evidence generator against real local projects.

Strict boundary:

- do not edit the source project;
- do not write outputs inside the source project;
- use `--no-adapters` through the runner's Lite CLI path;
- store all outputs under `test output/lite_rc_hardening/<date>/`.

Example:

```powershell
py -3 scripts\run_lite_rc_hardening.py `
  --real-project "file_manager=D:\Agent_programs\file_manager" `
  --real-project "voice_light_agent=D:\personal\voice-light-agent"
```

The runner records `source_state_before.json` and `source_state_after.json` for each project and fails the real-project gate if source file metadata changes.
