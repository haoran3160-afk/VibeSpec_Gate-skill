# Quickstart

```bash
python -m pip install -e .
vibesec scan tests/fixtures/vulnerable_next_supabase_app --output outputs/demo-next
vibesec gate outputs/demo-next/findings.json
vibesec loop tests/fixtures/vulnerable_next_supabase_app --previous outputs/demo-next/findings.json --output outputs/demo-loop
```

The scanner is read-only. It does not run dynamic web scans by default and does not modify the target project.

## Offline Agent Review

After a scan, run a deterministic local triage pass before asking an agent to prepare repairs:

```powershell
vibesec review outputs/demo-next/findings.json --project tests/fixtures/vulnerable_next_supabase_app --output outputs/demo-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibesec review-validate outputs/demo-review
```

Read `human_review_queue.md` for high-value findings that need confirmation before a fix. Read `agent_review_decisions.md` for the full decision ledger, including downgrades, false positives, suppression candidates, and each `agent_next_step`.
