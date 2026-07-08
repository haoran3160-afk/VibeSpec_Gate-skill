from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from vibesec.core.lite_review_bundle import build_lite_review_bundle


def test_build_lite_review_bundle_creates_four_primary_outputs_and_evidence(tmp_path):
    review_output = tmp_path / "review"
    review_output.mkdir()
    _write_review_output(review_output)

    result = build_lite_review_bundle(review_output)

    bundle = review_output / "lite_review"
    assert result["launch_decision"] == "BLOCK"
    assert (bundle / "launch_decision.md").exists()
    assert (bundle / "top_security_risks.md").exists()
    assert (bundle / "agent_fix_plan.md").exists()
    assert (bundle / "retest_checklist.md").exists()
    assert (bundle / "evidence" / "agent_review_decisions.json").exists()
    assert (bundle / "evidence" / "raw_findings.json").exists()
    launch = (bundle / "launch_decision.md").read_text(encoding="utf-8")
    fix_plan = (bundle / "agent_fix_plan.md").read_text(encoding="utf-8")
    assert "Decision: BLOCK" in launch
    assert "not a professional security certification" in launch
    assert "Human Confirmation Gate" in fix_plan
    assert "Do not auto-suppress findings" in fix_plan


def test_build_lite_review_bundle_uses_pass_with_warnings_for_nonblocking_candidates(tmp_path):
    review_output = tmp_path / "review"
    review_output.mkdir()
    _write_review_output(review_output, blocks_launch=False, must_review=False, action="downgrade")

    result = build_lite_review_bundle(review_output)

    assert result["launch_decision"] == "PASS_WITH_WARNINGS"
    launch = (review_output / "lite_review" / "launch_decision.md").read_text(encoding="utf-8")
    assert "Decision: PASS_WITH_WARNINGS" in launch


def test_lite_review_cli_builds_bundle(tmp_path):
    review_output = tmp_path / "review"
    bundle = tmp_path / "lite"
    review_output.mkdir()
    _write_review_output(review_output)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibesec.cli",
            "lite-review",
            str(review_output),
            "--output",
            str(bundle),
        ],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["launch_decision"] == "BLOCK"
    assert (bundle / "launch_decision.md").exists()
    assert (bundle / "evidence" / "raw_findings.json").exists()


def test_lite_review_cli_can_run_project_facade(tmp_path):
    project = tmp_path / "project"
    bundle = tmp_path / "lite-project"
    project.mkdir()
    (project / "README.md").write_text("Demo project\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibesec.cli",
            "lite-review",
            str(project),
            "--output",
            str(bundle),
            "--no-adapters",
        ],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert "scan" in payload
    assert "review" in payload
    assert payload["lite"]["bundle_dir"] == str(bundle.resolve())
    assert (bundle / "launch_decision.md").exists()
    assert (bundle / "evidence" / "scan" / "findings.json").exists()
    assert (bundle / "evidence" / "review_output" / "agent_review_decisions.json").exists()


def _write_review_output(
    review_output: Path,
    *,
    blocks_launch: bool = True,
    must_review: bool = True,
    action: str = "fix",
) -> None:
    payload = {
        "schema_version": "1.0",
        "summary": {
            "project_type": "SaaS Web App",
            "reviewed_findings": 1,
            "must_review_count": 1 if must_review else 0,
        },
        "decisions": [
            {
                "finding_id": "VSG-SEC-001",
                "title": "Runtime secret in server source",
                "recommended_final_severity": "P1",
                "recommended_action": action,
                "blocks_launch": blocks_launch,
                "must_review": must_review,
                "safe_for_agent_fix": action == "fix",
                "inspect_files": ["src/server.ts"],
                "prohibited_changes": [
                    "Do not blindly edit a real project without confirming the local evidence first.",
                    "Do not auto-suppress findings; safe_to_auto_suppress is false.",
                ],
                "verification_commands": ["Run the smallest local test that covers the inspected file."],
                "reason": "A runtime credential can expose production data.",
            }
        ],
    }
    (review_output / "agent_review_decisions.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (review_output / "ai_review.json").write_text(json.dumps([], indent=2), encoding="utf-8")
    (review_output / "llm_review_packet.json").write_text(json.dumps({"schema_version": "1.0"}, indent=2), encoding="utf-8")
    (review_output / "human_review_queue.md").write_text("# Queue\n", encoding="utf-8")
    (review_output / "suppression_candidates.json").write_text(json.dumps([], indent=2), encoding="utf-8")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env
