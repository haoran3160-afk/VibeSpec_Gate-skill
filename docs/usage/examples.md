# Examples

## Scan a local project

```bash
vibesec scan ./my-project --output ./outputs
```

## Force an AI-Agent review mode

```bash
vibesec scan ./my-agent --mode ai-agent --output ./outputs-agent
```

## Rebuild reports from findings

```bash
vibesec report ./outputs/findings.json --output ./outputs
```

## Print the gate summary

```bash
vibesec gate ./outputs/findings.json
```

## Build offline agent review outputs

```bash
vibesec review ./outputs/findings.json --project ./my-project --output ./outputs-review --include-p2 --offline --reviewer-rule-based --model-provider none
vibesec review-validate ./outputs-review
```

`human_review_queue.md` is intentionally compact and contains only must-review or fix-after-confirmation items. `agent_review_decisions.md` covers every reviewed finding, including downgrade and suppression decisions.
