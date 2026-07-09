from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .review_llm_packet import REQUESTED_OUTPUTS
from .review_schema import SchemaValidationError, validate_llm_review_packet


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "llm_outputs"


def build_llm_review_workspace(review_output_dir: str | Path) -> dict[str, Any]:
    review_root = Path(review_output_dir)
    packet_path = review_root / "llm_review_packet.json"
    packet = _load_packet(packet_path)
    validate_llm_review_packet(packet, len(packet.get("rule_findings", [])))

    workspace = review_root / "llm_review_workspace"
    templates_dir = workspace / "output_templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(packet_path, workspace / "llm_review_packet.json")
    for output_name in REQUESTED_OUTPUTS:
        source = TEMPLATE_DIR / output_name
        if not source.exists():
            raise SchemaValidationError(f"missing template: {source}")
        shutil.copyfile(source, templates_dir / output_name)

    prompt = render_llm_review_prompt(packet)
    (workspace / "llm_review_prompt.md").write_text(prompt, encoding="utf-8")
    (workspace / "README.md").write_text(render_workspace_readme(review_root, packet), encoding="utf-8")
    return {
        "workspace": str(workspace),
        "packet": str(workspace / "llm_review_packet.json"),
        "prompt": str(workspace / "llm_review_prompt.md"),
        "templates": [str(templates_dir / name) for name in REQUESTED_OUTPUTS],
        "model_api_called": False,
        "project_source_copied": False,
    }


def render_llm_review_prompt(packet: dict[str, Any]) -> str:
    project_type = packet.get("project_profile", {}).get("project_type", "unknown")
    requested = "\n".join(f"- `{name}`" for name in REQUESTED_OUTPUTS)
    boundaries = "\n".join(f"- {item}" for item in packet.get("safety_boundaries", []))
    questions = "\n".join(f"- {item}" for item in packet.get("review_questions", []))
    return f"""# VibeSpec Gate Host-Agent Review Prompt

You are a defensive security reviewer for vibe-coded products.

Audience:

- A non-security builder who needs a launch-risk answer.
- A coding Agent that needs bounded, human-confirmed repair tasks.

Input file:

- `llm_review_packet.json`

Project type:

- {project_type}

Required outputs:

{requested}

Safety boundaries:

{boundaries}

Quality rules:

- Treat `rule_findings[*].evidence_role=baseline_hint_not_final_judgment` literally.
- Use rule findings as baseline hints and evidence pointers, not final judgment.
- Cite finding IDs and evidence files when making claims.
- Separate confirmed risk, likely true risk, needs review, downgrade candidate, and suppression candidate.
- Mark missing evidence explicitly.
- Keep repair tasks bounded to named files and behaviors.
- Require human confirmation before risky edits, auth changes, data migrations, suppressions, or production-impacting actions.
- Keep `safe_to_auto_suppress=false`.
- Do not include exploit payloads, auth-bypass instructions, credential theft guidance, brute-force steps, persistence instructions, or destructive test plans.
- Do not call external model/API providers from this workspace unless the user has explicitly configured that outside this prompt.
- Do not mutate real reviewed projects while producing these review outputs.

Review questions:

{questions}

Write the required outputs in this workspace root. Use `output_templates/` as the format guide. If you cannot complete real LLM review, say so clearly instead of producing a launch-ready claim.
"""


def render_workspace_readme(review_root: Path, packet: dict[str, Any]) -> str:
    project_profile = packet.get("project_profile", {})
    requested = "\n".join(f"- `{name}`" for name in REQUESTED_OUTPUTS)
    return f"""# LLM Review Workspace

This workspace was generated from:

```text
{review_root}
```

It contains no copied project source. It contains the existing `llm_review_packet.json`, a host-agent prompt, and reusable output templates.

## Inputs

- `llm_review_packet.json`: product profile, evidence pointers, rule findings, review questions, and safety boundaries.
- `llm_review_prompt.md`: direct prompt for a host Agent.
- `output_templates/`: required output shapes.

## Project Profile

- Project type: {project_profile.get("project_type", "unknown")}
- Launch stage: {project_profile.get("launch_stage", "unknown")}
- Risk level: {project_profile.get("risk_level", "unknown")}

## Required Outputs

{requested}

## Safety

- No external model/API was called to build this workspace.
- Rule findings are baseline hints, not final judgment.
- Do not mutate real projects while filling the review outputs unless the user explicitly asks for repair implementation.
- Keep `safe_to_auto_suppress=false`.
"""


def _load_packet(path: Path) -> dict[str, Any]:
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(packet, dict):
        raise SchemaValidationError("llm_review_packet.json must be an object")
    return packet

