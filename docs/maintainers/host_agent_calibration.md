# Host-Agent Calibration

This page is for maintainers collecting and calibrating real host-agent output samples.

Host-agent calibration is not part of the normal Lite user path. It exists to keep the scorer aligned with natural Codex, Claude, Cursor, or similar outputs.

## Phase 11 Evidence Root

```text
test output/phase11_real_host_agent_calibration/
```

Important helper scripts:

```powershell
py -3 scripts\build_phase11_host_agent_prompts.py "test output\phase11_real_host_agent_calibration"
py -3 scripts\import_phase11_host_agent_sample.py "<sample_dir>" "test output\phase11_real_host_agent_calibration"
py -3 scripts\build_phase11_human_review_drafts.py "test output\phase11_real_host_agent_calibration"
py -3 scripts\import_phase11_human_review.py "<record_json>" "test output\phase11_real_host_agent_calibration"
py -3 scripts\verify_phase11_calibration.py "test output\phase11_real_host_agent_calibration"
```

## Calibration Rules

- Repository scripts must not call provider APIs, provider CLIs, browsers, or hidden model generation paths.
- Host-agent outputs are manually supplied.
- Human review records are explicit calibration evidence.
- Scorer changes require a real disagreement or repeatable real-output failure mode.

## Completion Gate

Phase 11 is complete only when the verifier exits `0` and all acceptance gates in the plan are satisfied.
