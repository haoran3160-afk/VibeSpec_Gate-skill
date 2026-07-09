from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from vibespec_gate.core.llm_output_schema import validate_llm_review_outputs
from vibespec_gate.core.llm_output_stub import STUB_DISCLAIMER, write_stub_llm_review_outputs
from vibespec_gate.core.llm_review_workspace import TEMPLATE_DIR, build_llm_review_workspace
from vibespec_gate.core.review_llm_packet import REQUESTED_OUTPUTS
from vibespec_gate.core.review_runner import run_review
from vibespec_gate.core.review_schema import SchemaValidationError


CASE = Path("tests/evaluation_cases/review/secret_provider_runtime_confirmed")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _review_output(tmp_path: Path) -> Path:
    output = tmp_path / "review"
    run_review(str(CASE / "findings.json"), str(CASE), str(output), include_p2=True)
    return output


def _workspace_with_stubs(tmp_path: Path) -> Path:
    review_output = _review_output(tmp_path)
    build_llm_review_workspace(review_output)
    workspace = review_output / "llm_review_workspace"
    write_stub_llm_review_outputs(workspace)
    return workspace


def test_workspace_builder_creates_prompt_readme_packet_and_templates(tmp_path):
    review_output = _review_output(tmp_path)
    result = build_llm_review_workspace(review_output)
    workspace = review_output / "llm_review_workspace"

    assert Path(result["workspace"]) == workspace
    assert result["model_api_called"] is False
    assert result["project_source_copied"] is False
    assert (workspace / "llm_review_packet.json").exists()
    assert (workspace / "llm_review_prompt.md").exists()
    assert (workspace / "README.md").exists()
    for output_name in REQUESTED_OUTPUTS:
        assert (workspace / "output_templates" / output_name).exists()

    prompt = (workspace / "llm_review_prompt.md").read_text(encoding="utf-8")
    assert "defensive security reviewer for vibe coding products" in prompt
    assert "llm_review_packet.json" in prompt
    assert "baseline_hint_not_final_judgment" in prompt
    assert "Safety boundaries" in prompt
    assert "Do not call external model/API providers" in prompt
    for output_name in REQUESTED_OUTPUTS:
        assert output_name in prompt


def test_llm_output_templates_have_required_placeholders():
    required_terms = {
        "nontechnical_user_summary.md": ["{{LAUNCH_DECISION", "{{EVIDENCE_FILES", "safe_to_auto_suppress"],
        "launch_risk_report.md": ["{{LAUNCH_DECISION", "{{CONFIDENCE", "{{MISSING_EVIDENCE"],
        "security_review_findings.json": ["{{FINDING_ID", "{{SEVERITY", "safe_to_auto_suppress"],
        "agent_fix_plan.md": ["{{PROHIBITED_CHANGE", "{{VERIFICATION_COMMAND", "{{MISSING_EVIDENCE"],
        "retest_checklist.md": ["{{RETEST_COMMAND", "{{EXPECTED_GATE_CHANGE", "safe_to_auto_suppress"],
    }
    for output_name, terms in required_terms.items():
        text = (TEMPLATE_DIR / output_name).read_text(encoding="utf-8")
        assert "{{STUB_STATUS}}" in text
        for term in terms:
            assert term in text, output_name


def test_stub_outputs_validate_and_are_clearly_not_completed_review(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    result = validate_llm_review_outputs(workspace)

    assert result["valid"] is True
    assert result["security_findings"] >= 1
    for output_name in REQUESTED_OUTPUTS:
        assert STUB_DISCLAIMER in (workspace / output_name).read_text(encoding="utf-8")
    assert "Launch decision: PASS" not in (workspace / "nontechnical_user_summary.md").read_text(encoding="utf-8")


def test_validator_rejects_missing_required_output_file(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    (workspace / "agent_fix_plan.md").unlink()

    with pytest.raises(SchemaValidationError, match="missing required LLM output file"):
        validate_llm_review_outputs(workspace)


def test_validator_rejects_malformed_security_review_json(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    (workspace / "security_review_findings.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="not valid JSON"):
        validate_llm_review_outputs(workspace)


def test_validator_rejects_unknown_enum_values(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    data = json.loads((workspace / "security_review_findings.json").read_text(encoding="utf-8"))
    data["findings"][0]["severity"] = "Critical"
    (workspace / "security_review_findings.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="severity"):
        validate_llm_review_outputs(workspace)


def test_validator_rejects_safe_to_auto_suppress_true(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    data = json.loads((workspace / "security_review_findings.json").read_text(encoding="utf-8"))
    data["findings"][0]["safe_to_auto_suppress"] = True
    (workspace / "security_review_findings.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="safe_to_auto_suppress"):
        validate_llm_review_outputs(workspace)


def test_validator_rejects_unknown_finding_id_without_new_llm_marker(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    data = json.loads((workspace / "security_review_findings.json").read_text(encoding="utf-8"))
    data["findings"][0]["finding_id"] = "UNKNOWN-FINDING"
    data["findings"][0]["new_llm_finding"] = False
    (workspace / "security_review_findings.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="llm_review_packet"):
        validate_llm_review_outputs(workspace)


def test_validator_rejects_obvious_unsafe_offensive_wording(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    path = workspace / "launch_risk_report.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nExploit payload: run this attack.\n", encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="unsafe offensive guidance"):
        validate_llm_review_outputs(workspace)


def test_cli_llm_output_validate_accepts_stub_workspace(tmp_path):
    workspace = _workspace_with_stubs(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "vibespec_gate.cli", "llm-output-validate", str(workspace)],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
