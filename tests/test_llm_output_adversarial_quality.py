from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.build_llm_quality_matrix import build_matrix
from scripts.compare_host_agent_samples import compare_samples, write_reports
from vibespec_gate.core.llm_output_quality import score_llm_review_outputs


BAD_FIXTURE_ROOT = Path("tests/evaluation_cases/llm_outputs_bad")
EXPECTED_BAD_CASES = {
    "secret_runtime_overoptimistic",
    "placeholder_secret_overblocks",
    "missing_auth_ignores_uncertainty",
    "mcp_tool_boundary_no_evidence",
    "electron_ipc_unbounded_fix",
    "llm_tool_authority_missing_retest",
}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def test_bad_output_fixtures_exist():
    case_dirs = {path.parent.name for path in BAD_FIXTURE_ROOT.glob("*/expected_quality.json")}
    assert case_dirs == EXPECTED_BAD_CASES


def test_bad_outputs_fail_even_when_soft_score_is_nonzero():
    result = score_llm_review_outputs(BAD_FIXTURE_ROOT / "secret_runtime_overoptimistic")

    assert result["passed"] is False
    assert result["hard_fail_passed"] is False
    assert "launch_decision" in result["hard_failures"]
    assert result["soft_score"] > 0


def test_cross_output_coverage_detects_missing_fix_plan_reference():
    result = score_llm_review_outputs(BAD_FIXTURE_ROOT / "llm_tool_authority_missing_retest")

    assert result["passed"] is False
    assert "p1_cross_output_coverage" in result["failed_checks"]


def test_bad_fixture_expected_failures_are_met():
    for expected_path in sorted(BAD_FIXTURE_ROOT.glob("*/expected_quality.json")):
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        result = score_llm_review_outputs(expected_path.parent)

        assert result["passed"] is expected["expected_pass"], expected_path
        for check_id in expected["expected_failed_checks"]:
            assert check_id in result["failed_checks"], (expected_path, result)


def test_quality_matrix_uses_expectation_semantics():
    matrix = build_matrix()

    assert matrix["schema_version"] == "1.1"
    assert matrix["total_cases"] == 12
    assert matrix["golden_cases"] == 6
    assert matrix["bad_cases"] == 6
    assert matrix["expectations_met"] == 12
    assert matrix["expectations_failed"] == 0
    assert all("expectation_met" in case for case in matrix["cases"])


def test_compare_host_agent_samples_empty_root(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/compare_host_agent_samples.py", str(tmp_path / "host_agent_samples")],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0"
    assert payload["sample_count"] == 0
    assert "No host-agent samples found" in payload["message"]


def test_compare_host_agent_samples_non_empty_root_writes_reports(tmp_path):
    sample_case = tmp_path / "host_agent_samples" / "codex" / "secret_runtime_block"
    shutil.copytree(Path("tests/evaluation_cases/llm_outputs/secret_runtime_block"), sample_case)
    (sample_case / "sample_metadata.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "agent": "codex",
                "case_id": "secret_runtime_block",
                "generated_by": "manual_host_agent_session",
                "generated_at": "2026-07-07",
                "human_quality_decision": "pass",
                "scorer_human_agreement": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = compare_samples(tmp_path / "host_agent_samples")
    write_reports(tmp_path / "host_agent_samples", result)

    assert result["sample_count"] == 1
    assert result["agents"] == ["codex"]
    assert result["cases"][0]["generated_by"] == "manual_host_agent_session"
    assert result["cases"][0]["scorer_human_agreement"] is True
    assert (tmp_path / "reports" / "host_agent_sample_matrix.json").exists()
    assert (tmp_path / "reports" / "host_agent_sample_matrix.md").exists()
    assert (tmp_path / "reports" / "scorer_disagreement_log.md").exists()
