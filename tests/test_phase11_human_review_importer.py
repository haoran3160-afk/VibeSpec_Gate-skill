from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.import_phase11_human_review import import_human_review, validate_human_record


def test_import_human_review_appends_record_and_updates_markdown(tmp_path):
    phase_root = _write_empty_phase_root(tmp_path)
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(_record("review-1"), indent=2), encoding="utf-8")

    result = import_human_review(record_path, phase_root)

    ledger = json.loads((phase_root / "human_calibration_ledger.json").read_text(encoding="utf-8"))
    markdown = (phase_root / "human_calibration_ledger.md").read_text(encoding="utf-8")
    disagreement = (phase_root / "scorer_disagreement_log.md").read_text(encoding="utf-8")
    assert result["imported"] is True
    assert result["completed_human_review_count"] == 1
    assert ledger["records"][0]["review_id"] == "review-1"
    assert ledger["human_review_performed"] is True
    assert "| review-1 | host_agent_sample | codex | secret_runtime_block | BLOCK | fail | False | defer |" in markdown
    assert "## review-1" in disagreement


def test_import_human_review_rejects_duplicate_review_id(tmp_path):
    phase_root = _write_empty_phase_root(tmp_path)
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(_record("review-1"), indent=2), encoding="utf-8")

    import_human_review(record_path, phase_root)

    with pytest.raises(ValueError, match="duplicate review_id"):
        import_human_review(record_path, phase_root)


def test_validate_human_record_requires_rule_change_for_add_check():
    record = _record("review-1")
    record["rubric_action"] = "add_check"
    record["proposed_rule_change"] = None

    with pytest.raises(ValueError, match="proposed_rule_change"):
        validate_human_record(record)


def _write_empty_phase_root(tmp_path: Path) -> Path:
    phase_root = tmp_path / "phase11"
    phase_root.mkdir()
    ledger = {
        "schema_version": "1.0",
        "phase": "phase11_real_host_agent_calibration",
        "status": "blocked_on_external_human_review",
        "human_review_performed": False,
        "minimum_required_review_count": 5,
        "completed_human_review_count": 0,
        "records": [],
        "agent_structured_observations": [],
        "required_review_queue": [],
        "blocking_gaps": ["No independent human reviewer decisions were supplied."],
    }
    (phase_root / "human_calibration_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    (phase_root / "human_calibration_ledger.md").write_text("# Ledger\n", encoding="utf-8")
    (phase_root / "scorer_disagreement_log.md").write_text("# Disagreements\n", encoding="utf-8")
    return phase_root


def _record(review_id: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "review_id": review_id,
        "reviewed_at": "2026-07-07",
        "reviewer": "human",
        "case_id": "secret_runtime_block",
        "sample_type": "host_agent_sample",
        "agent": "codex",
        "sample_path": "test output/phase11_real_host_agent_calibration/host_agent_samples/codex/secret_runtime_block",
        "scorer_passed": True,
        "scorer_soft_score": 100,
        "scorer_hard_failures": [],
        "human_launch_decision": "BLOCK",
        "human_quality_decision": "fail",
        "agreement": False,
        "disagreement_type": "human_stricter",
        "human_notes": "Human reviewer found the sample incomplete.",
        "rubric_action": "defer",
        "proposed_rule_change": None,
    }
