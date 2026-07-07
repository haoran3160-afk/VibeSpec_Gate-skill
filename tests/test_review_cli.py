from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


CASE = Path("tests/evaluation_cases/review/secret_provider_runtime_confirmed")
REQUIRED_OUTPUTS = {
    "ai_review.json",
    "ai_review_summary.md",
    "agent_review_decisions.md",
    "human_review_queue.md",
    "suppression_candidates.json",
    "review_packets.json",
}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def test_review_cli_generates_and_validates_outputs(tmp_path):
    output = tmp_path / "review"
    command = [
        sys.executable,
        "-m",
        "vibesec.cli",
        "review",
        str(CASE / "findings.json"),
        "--project",
        str(CASE),
        "--output",
        str(output),
        "--include-p2",
        "--max-snippet-lines",
        "12",
        "--offline",
        "--reviewer-rule-based",
        "--model-provider",
        "none",
    ]
    result = subprocess.run(command, cwd=Path.cwd(), env=_env(), text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr + result.stdout
    assert REQUIRED_OUTPUTS <= {path.name for path in output.iterdir()}

    packets = json.loads((output / "review_packets.json").read_text(encoding="utf-8"))
    assert packets
    assert max(len(packet["evidence_context"]["snippet"].splitlines()) for packet in packets) <= 12
    assert "sk-proj-secret-value-1234567890" not in (output / "review_packets.json").read_text(encoding="utf-8")
    verdicts = json.loads((output / "ai_review.json").read_text(encoding="utf-8"))
    assert verdicts[0]["agent_next_step"] == "prepare_fix_task"
    assert verdicts[0]["inspect_files"]
    assert verdicts[0]["safe_to_auto_suppress"] is False

    queue = (output / "human_review_queue.md").read_text(encoding="utf-8")
    decisions = (output / "agent_review_decisions.md").read_text(encoding="utf-8")
    assert "Finding id: VSG-SEC-001" in queue
    assert "Recommended action: fix" in queue
    assert "Agent next step: prepare_fix_task" in queue
    assert "## Must confirm before fix" in queue
    assert "## Likely true, fix after confirmation" in queue
    assert "## Downgrade candidates" not in queue
    assert "## Suppression candidates" not in queue
    assert "## Downgrade candidates" in decisions
    assert "## Suppression and false-positive candidates" in decisions

    validate = subprocess.run(
        [sys.executable, "-m", "vibesec.cli", "review-validate", str(output)],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr + validate.stdout
    assert json.loads(validate.stdout)["valid"] is True


def test_review_cli_rejects_external_model_provider(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibesec.cli",
            "review",
            str(CASE / "findings.json"),
            "--project",
            str(CASE),
            "--output",
            str(tmp_path / "review"),
            "--model-provider",
            "openai",
        ],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
