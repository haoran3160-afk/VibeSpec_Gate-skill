from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.build_llm_quality_matrix import build_matrix
from vibesec.core.llm_output_quality import score_llm_review_outputs
from vibesec.core.llm_output_schema import STUB_DISCLAIMER, validate_llm_review_outputs


FIXTURE_ROOT = Path("tests/evaluation_cases/llm_outputs")
EXPECTED_CASES = {
    "secret_runtime_block",
    "placeholder_secret_downgrade",
    "missing_auth_review",
    "mcp_tool_boundary_review",
    "electron_ipc_review",
    "llm_tool_authority_review",
}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _fixture_dirs() -> list[Path]:
    return sorted(path.parent for path in FIXTURE_ROOT.glob("*/expected_quality.json"))


def test_llm_output_fixtures_exist_and_are_not_stubs():
    fixtures = _fixture_dirs()

    assert {path.name for path in fixtures} == EXPECTED_CASES
    for fixture in fixtures:
        assert (fixture / "llm_review_packet.json").exists()
        assert (fixture / "expected_quality.json").exists()
        output_dir = fixture / "outputs"
        for name in (
            "nontechnical_user_summary.md",
            "launch_risk_report.md",
            "security_review_findings.json",
            "agent_fix_plan.md",
            "retest_checklist.md",
        ):
            text = (output_dir / name).read_text(encoding="utf-8")
            assert STUB_DISCLAIMER not in text, fixture


def test_score_llm_review_outputs_shape_and_passes_all_fixtures():
    for fixture in _fixture_dirs():
        result = score_llm_review_outputs(fixture)

        assert {"schema_version", "case_id", "passed", "score", "max_score", "checks"} <= set(result)
        assert result["schema_version"] == "1.0"
        assert result["passed"] is True, result
        assert result["score"] >= result["minimum_score"]
        assert result["max_score"] == 100
        assert result["checks"]
        assert not result["failed_checks"]


def test_final_validator_accepts_real_fixture_outputs():
    for fixture in _fixture_dirs():
        result = validate_llm_review_outputs(fixture / "outputs", allow_stub=False)

        assert result["valid"] is True
        assert result["allow_stub"] is False
        assert result["security_findings"] >= 1


def test_score_script_success_path():
    result = subprocess.run(
        [sys.executable, "scripts/score_llm_review_outputs.py", str(FIXTURE_ROOT / "secret_runtime_block")],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["case_id"] == "secret_runtime_block"


def test_score_script_failure_path_for_invalid_launch_decision(tmp_path):
    fixture = tmp_path / "bad_secret_runtime_block"
    shutil.copytree(FIXTURE_ROOT / "secret_runtime_block", fixture)
    findings_path = fixture / "outputs" / "security_review_findings.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    findings["launch_decision"] = "PASS"
    findings_path.write_text(json.dumps(findings, indent=2), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/score_llm_review_outputs.py", str(fixture)],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert "launch_decision" in payload["failed_checks"]


def test_build_llm_quality_matrix_shape():
    matrix = build_matrix()

    assert matrix["schema_version"] == "1.1"
    assert matrix["total_cases"] == 12
    assert matrix["golden_cases"] == 6
    assert matrix["bad_cases"] == 6
    assert matrix["expectations_failed"] == 0
    golden_cases = {case["case_id"] for case in matrix["cases"] if case["fixture_kind"] == "golden"}
    assert golden_cases == EXPECTED_CASES
    assert all(case["expectation_met"] for case in matrix["cases"])
