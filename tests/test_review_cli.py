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
    "agent_review_decisions.json",
    "agent_review_decisions.md",
    "human_review_queue.md",
    "llm_review_packet.json",
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
        "vibespec_gate.cli",
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
    llm_packet = json.loads((output / "llm_review_packet.json").read_text(encoding="utf-8"))
    assert packets
    assert max(len(packet["evidence_context"]["snippet"].splitlines()) for packet in packets) <= 12
    assert "sk-proj-secret-value-1234567890" not in (output / "review_packets.json").read_text(encoding="utf-8")
    assert llm_packet["schema_version"] == "1.0"
    assert llm_packet["rule_findings"][0]["evidence_role"] == "baseline_hint_not_final_judgment"
    assert "nontechnical_user_summary.md" in llm_packet["requested_outputs"]
    verdicts = json.loads((output / "ai_review.json").read_text(encoding="utf-8"))
    decision_output = json.loads((output / "agent_review_decisions.json").read_text(encoding="utf-8"))
    decision_json = decision_output["decisions"]
    assert verdicts[0]["agent_next_step"] == "prepare_fix_task"
    assert verdicts[0]["inspect_files"]
    assert verdicts[0]["safe_to_auto_suppress"] is False
    assert decision_output["schema_version"] == "1.0"
    assert decision_output["reviewer"] == "rule-based"
    assert len(decision_json) == len(verdicts)
    assert decision_json[0]["finding_id"] == verdicts[0]["finding_id"]
    assert decision_json[0]["decision_type"] == "fix_after_confirmation"
    assert decision_json[0]["must_review"] is True
    assert decision_json[0]["source_output"] == "ai_review.json"
    assert decision_json[0]["blocks_launch"] is True
    assert decision_json[0]["safe_for_agent_fix"] is True
    assert decision_json[0]["safe_to_auto_suppress"] is False

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
        [sys.executable, "-m", "vibespec_gate.cli", "review-validate", str(output)],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr + validate.stdout
    validate_json = json.loads(validate.stdout)
    assert validate_json["valid"] is True
    assert validate_json["agent_decisions"] == len(verdicts)


def test_review_cli_rejects_external_model_provider(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibespec_gate.cli",
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


def test_lite_review_cli_marks_login_token_logging_as_block(tmp_path):
    project = tmp_path / "login_app"
    route = project / "app" / "api" / "login" / "route.ts"
    route.parent.mkdir(parents=True)
    route.write_text(
        """
export async function POST(req) {
  console.log("authorization", req.headers.get("authorization"))
  return Response.json({ ok: true })
}
""",
        encoding="utf-8",
    )
    output = tmp_path / "lite_review"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibespec_gate.cli",
            "lite-review",
            str(project),
            "--output",
            str(output),
            "--no-adapters",
        ],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Decision: BLOCK" in (output / "launch_decision.md").read_text(encoding="utf-8")
    assert "Authentication token or verification code may be logged" in (output / "top_security_risks.md").read_text(encoding="utf-8")
    assert "Do not auto-fix" in (output / "launch_decision.md").read_text(encoding="utf-8")
