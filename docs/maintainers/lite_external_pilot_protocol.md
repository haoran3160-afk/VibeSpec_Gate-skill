# Lite External Pilot Protocol

Use this protocol after RC hardening evidence has been generated.

The current promotion authority is:

```text
test output/lite_rc_hardening/2026-07-08/release_decision.md
```

Do not promote to controlled external pilot while that file says `NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT`.
If blind users are unavailable, the runner may produce `READY_FOR_CONTROLLED_EXTERNAL_PILOT_SYNTHETIC`; treat that as a contract-test state based on maintainer-authored walkthroughs, not executed Agent sessions or real external user validation.

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
- every recorded session includes sanitized observation notes and a transcript or trace.

The certification and blind-edit conditions are all-participant vetoes. An 80% aggregate score cannot override either failure.

## Synthetic Walkthrough Fallback

When no blind users are available, maintainers may generate deterministic, prewritten role walkthroughs to test documentation and scoring contracts:

```powershell
py -3 scripts\run_lite_rc_hardening.py --simulate-subagents
```

The runner generates:

```text
test output/lite_rc_hardening/2026-07-08/synthetic_walkthrough_sessions/
  walkthrough_summary.md
  *_prompt.md
  *_transcript.md
```

Walkthrough roles cover:

- non-security product builder;
- developer who uses coding Agents;
- AI/Agent or SaaS builder;
- security-minded reviewer.

Boundary:

- walkthroughs must be marked `source=synthetic_walkthrough`;
- walkthroughs are maintainer-authored files, not executed sub-agent sessions;
- walkthroughs may exercise package and scoring contracts but are not usability evidence;
- record real blind sessions before treating the gate as GA or broad-market validation.

## Recording Format

The `--external-session` shorthand accepts six strict booleans but cannot satisfy the external evidence gate because it has no notes or transcript. Use it only for non-promoting drafts.

Format:

```powershell
py -3 scripts\run_lite_rc_hardening.py `
  --external-session "non_security_builder:true,true,true,true,true,true"
```

Fields after the participant name:

```text
started,files,fix,retest,certification_safe,blind_edit_safe
```

Use `true` only when the observation is supported by sanitized session notes and a transcript or trace. String values such as `"false"` are parsed strictly as false, not as a truthy non-empty string.

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
      "blind_edit_safe": true,
      "notes": "Observed from session notes.",
      "transcript": "Sanitized participant trace."
    },
    {
      "name": "participant_agent_developer",
      "profile": "coding_agent_developer",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "blind_edit_safe": true,
      "notes": "Observed from session notes.",
      "transcript": "Sanitized participant trace."
    },
    {
      "name": "participant_saas_builder",
      "profile": "ai_agent_or_saas_project",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "blind_edit_safe": true,
      "notes": "Observed from session notes.",
      "transcript": "Sanitized participant trace."
    }
  ]
}
```

Then run:

```powershell
py -3 scripts\run_lite_rc_hardening.py --external-session-file .\pilot_sessions.json
```

Use pseudonyms and remove personal data, private repository paths, secrets, and customer identifiers from notes and transcripts. The runner also writes a starter template to:

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

For a synthetic walkthrough fallback, the equivalent no-go is `NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT`; a successful contract-only state is labeled separately as `READY_FOR_CONTROLLED_EXTERNAL_PILOT_SYNTHETIC` and does not satisfy the real-user gate.

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
  --real-project "project_a=C:\path\to\project-a" `
  --real-project "project_b=C:\path\to\project-b"
```

Before resetting or creating evidence, the runner rejects any overlap between an authorized project and the RC output tree. It then records `source_state_before.json` and `source_state_after.json` and fails when an included source file path, size, timestamp, or SHA-256 content hash differs at process completion.

This is a final-state integrity check, not proof that no transient write, permission change, empty-directory change, symlink/junction change, or excluded dependency/cache/build write occurred. A run with no `--real-project` inputs is reported as `SKIPPED`, never `PASS`.
