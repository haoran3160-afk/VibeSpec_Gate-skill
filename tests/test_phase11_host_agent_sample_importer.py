from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.import_phase11_host_agent_sample import import_host_agent_sample, validate_sample_dir


def test_import_host_agent_sample_copies_sample_and_refreshes_reports(tmp_path):
    phase_root = tmp_path / "phase11"
    sample = tmp_path / "incoming" / "claude" / "secret_runtime_block"
    _write_sample(sample, "claude")

    result = import_host_agent_sample(sample, phase_root)

    destination = phase_root / "host_agent_samples" / "claude" / "secret_runtime_block"
    matrix = json.loads((phase_root / "reports" / "host_agent_sample_matrix.json").read_text(encoding="utf-8"))
    assert result["imported"] is True
    assert destination.exists()
    assert result["agents"] == ["claude"]
    assert matrix["sample_count"] == 1
    assert matrix["cases"][0]["agent"] == "claude"


def test_import_host_agent_sample_rejects_existing_destination(tmp_path):
    phase_root = tmp_path / "phase11"
    sample = tmp_path / "incoming" / "claude" / "secret_runtime_block"
    _write_sample(sample, "claude")

    import_host_agent_sample(sample, phase_root)

    with pytest.raises(FileExistsError, match="destination already exists"):
        import_host_agent_sample(sample, phase_root)


def test_validate_sample_dir_rejects_provider_invocation_marker(tmp_path):
    sample = tmp_path / "incoming" / "cursor" / "secret_runtime_block"
    _write_sample(sample, "cursor")
    metadata_path = sample / "sample_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["repository_script_invoked_provider"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="repository_script_invoked_provider must be false"):
        validate_sample_dir(sample)


def test_validate_sample_dir_rejects_agent_path_mismatch(tmp_path):
    sample = tmp_path / "incoming" / "cursor" / "secret_runtime_block"
    _write_sample(sample, "claude")

    with pytest.raises(ValueError, match="parent directory"):
        validate_sample_dir(sample)


def _write_sample(sample: Path, agent: str) -> None:
    (sample / "outputs").mkdir(parents=True)
    (sample / "llm_review_packet.json").write_text(
        json.dumps({"case_id": "secret_runtime_block"}, indent=2),
        encoding="utf-8",
    )
    (sample / "expected_quality.json").write_text(
        json.dumps(
            {
                "case_id": "secret_runtime_block",
                "risk_domain": "secrets",
                "expected_launch_decision": "BLOCK",
                "minimum_score": 80,
                "must_include_phrases": [],
                "expected_pass": True,
                "expected_failed_checks": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (sample / "sample_metadata.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "agent": agent,
                "case_id": "secret_runtime_block",
                "source_packet": "tests/evaluation_cases/llm_outputs/secret_runtime_block/llm_review_packet.json",
                "generated_by": "manual_host_agent_session",
                "generated_at": "2026-07-08",
                "prompt_contract": "docs/usage/llm_review_contract.md",
                "human_review_status": "pending",
                "human_quality_decision": None,
                "scorer_human_agreement": None,
                "raw_response_preserved": True,
                "repository_script_invoked_provider": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (sample / "outputs" / "nontechnical_user_summary.md").write_text("Launch decision: BLOCK\n", encoding="utf-8")
    (sample / "outputs" / "launch_risk_report.md").write_text("Launch decision: BLOCK\n", encoding="utf-8")
    (sample / "outputs" / "security_review_findings.json").write_text(
        json.dumps(
            [
                {
                    "id": "finding-1",
                    "severity": "P1",
                    "title": "Runtime secret exposure",
                    "launch_decision": "BLOCK",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    (sample / "outputs" / "agent_fix_plan.md").write_text(
        "Affected files: src/settings.py\nMinimal task boundary: remove runtime secret exposure.\nVerification steps: run tests.\n",
        encoding="utf-8",
    )
    (sample / "outputs" / "retest_checklist.md").write_text("Run secret scan.\n", encoding="utf-8")
