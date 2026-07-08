from __future__ import annotations

from pathlib import Path

from scripts.run_lite_release_validation import (
    PRIMARY_OUTPUTS,
    review_validation_outputs,
    stage_candidate_package,
    write_prompt_only_outputs,
    write_release_readiness_decision,
    write_release_notes,
    write_usability_notes,
)
from scripts.verify_lite_package import REQUIRED_INCLUDE, check_package


def test_stage_candidate_package_uses_manifest_required_files(tmp_path):
    candidate = stage_candidate_package(tmp_path)

    assert check_package(candidate) == []
    for file_name in REQUIRED_INCLUDE:
        assert (candidate / file_name).exists()


def test_prompt_only_outputs_cover_blocker_and_low_risk_cases(tmp_path):
    write_prompt_only_outputs(tmp_path)

    for case_name in (
        "prompt_only_case_1_secret_leak_web_app",
        "prompt_only_case_2_missing_auth_or_ownership_check",
        "prompt_only_case_3_agent_or_mcp_tool_overreach",
        "prompt_only_case_4_low_risk_clean_project",
    ):
        for output_name in PRIMARY_OUTPUTS:
            assert (tmp_path / case_name / output_name).exists()

    review = review_validation_outputs(tmp_path)

    assert review == {"passed": True, "failures": []}
    assert "Decision: BLOCK" in (tmp_path / "prompt_only_case_1_secret_leak_web_app" / "launch_decision.md").read_text(encoding="utf-8")
    assert "Decision: BLOCK" in (tmp_path / "prompt_only_case_2_missing_auth_or_ownership_check" / "launch_decision.md").read_text(encoding="utf-8")
    assert "Decision: REVIEW" in (tmp_path / "prompt_only_case_3_agent_or_mcp_tool_overreach" / "launch_decision.md").read_text(encoding="utf-8")
    assert "Decision: PASS" in (tmp_path / "prompt_only_case_4_low_risk_clean_project" / "launch_decision.md").read_text(encoding="utf-8")


def test_release_readiness_decision_requires_cli_when_not_skipped(tmp_path):
    write_prompt_only_outputs(tmp_path)
    write_usability_notes(tmp_path)
    write_release_notes(tmp_path)
    review = review_validation_outputs(tmp_path)
    command_results = {
        "package_verifier_source": {"returncode": 0},
        "package_verifier_candidate": {"returncode": 0},
        "pytest_lite_focused": {"returncode": 0},
        "cli_smoke": {"returncode": 0},
    }

    write_release_readiness_decision(tmp_path, command_results, review, skipped_cli=False)

    decision = (tmp_path / "release_readiness_decision.md").read_text(encoding="utf-8")
    assert "Decision: READY_FOR_RELEASE_CANDIDATE" in decision
    assert "professional security certification" in decision
