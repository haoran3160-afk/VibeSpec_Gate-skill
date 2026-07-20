from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

import scripts.run_lite_release_validation as release_validation
from scripts.run_lite_release_validation import (
    PRIMARY_OUTPUTS,
    _skill_eval_passed,
    _skill_tree_sha256,
    review_validation_outputs,
    stage_candidate_package,
    write_prompt_only_outputs,
    write_release_readiness_decision,
    write_release_notes,
    write_usability_notes,
)
from scripts.verify_lite_package import REQUIRED_INCLUDE, check_package
from scripts.verify_skill_evals import main as verify_skill_evals_main


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


def test_release_readiness_decision_requires_cli_when_not_skipped(tmp_path, monkeypatch):
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

    monkeypatch.setattr(release_validation, "_skill_eval_passed", lambda _path: True)
    ready = write_release_readiness_decision(tmp_path, command_results, review, skipped_cli=False)

    decision = (tmp_path / "release_readiness_decision.md").read_text(encoding="utf-8")
    assert ready is True
    assert "Decision: READY_FOR_CONTROLLED_RC" in decision
    assert "prewritten examples are not counted" in decision
    assert "Real-user controlled trial: PENDING" in decision
    assert "professional security certification" in decision


def test_release_readiness_decision_fails_when_skill_eval_is_not_observable(tmp_path, monkeypatch):
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
    monkeypatch.setattr(release_validation, "_skill_eval_passed", lambda _path: False)

    ready = write_release_readiness_decision(tmp_path, command_results, review, skipped_cli=False)

    assert ready is False
    decision = (tmp_path / "release_readiness_decision.md").read_text(encoding="utf-8")
    assert "Decision: NOT_RELEASE_READY" in decision
    assert "FAIL: Fresh-task Skill trigger and behavior evaluations pass" in decision


def test_skill_eval_readiness_reconstructs_cases_traces_hashes_and_skill_tree(tmp_path):
    host = "test-host"
    executed_at = "2026-07-20T00:00:00+00:00"
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("candidate\n", encoding="utf-8")
    run_root = tmp_path / "run"
    (run_root / "trigger").mkdir(parents=True)
    (run_root / "behavior").mkdir()
    (run_root / "evidence").mkdir()
    triggers = []
    trigger_cases = []
    for index in range(10):
        output = f"trigger/{index}.md"
        expected = index < 5
        prompt = f"trigger prompt {index}"
        trace = f"# trigger-{index}\n\n## Raw Request\n\n{prompt}\n\n## Unedited Final Output\n\ntrace\n"
        (run_root / output).write_text(trace, encoding="utf-8")
        output_sha256 = hashlib.sha256((run_root / output).read_bytes()).hexdigest()
        activation_evidence = f"evidence/trigger-{index}.json"
        task_id = f"task-trigger-{index}"
        (run_root / activation_evidence).write_text(
            json.dumps(
                {
                    "case_id": f"trigger-{index}",
                    "event_type": "skill_routing",
                    "task_id": task_id,
                    "host": host,
                    "selected_skills": ["vibespec-gate"] if expected else [],
                }
            ),
            encoding="utf-8",
        )
        trigger_cases.append({"id": f"trigger-{index}", "prompt": prompt, "expected_trigger": expected})
        triggers.append(
            {
                "id": f"trigger-{index}",
                "status": "PASS",
                "expected_trigger": expected,
                "activated": expected,
                "activation_source": "host_event",
                "activation_evidence": activation_evidence,
                "activation_evidence_sha256": hashlib.sha256(
                    (run_root / activation_evidence).read_bytes()
                ).hexdigest(),
                "output": output,
                "output_sha256": output_sha256,
                "task_id": task_id,
                "executed_at_utc": executed_at,
            }
        )
    behaviors = []
    behavior_cases = []
    for index in range(8):
        output = f"behavior/{index}.md"
        prompt = f"behavior prompt {index}"
        fixture = tmp_path / f"fixture-{index}.txt"
        fixture.write_text(f"fixture {index}\n", encoding="utf-8")
        fixture_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
        trace = (
            f"# behavior-{index}\n\n## Raw Request\n\n{prompt}\n\n"
            "## Unedited Final Output\n\nDecision: REVIEW\nCoverage is partial.\n"
        )
        (run_root / output).write_text(trace, encoding="utf-8")
        output_sha256 = hashlib.sha256((run_root / output).read_bytes()).hexdigest()
        write_evidence = f"evidence/behavior-{index}.json"
        task_id = f"task-behavior-{index}"
        (run_root / write_evidence).write_text(
            json.dumps(
                {
                    "case_id": f"behavior-{index}",
                    "event_type": "host_filesystem_write_trace",
                    "scope": "isolated_case_root",
                    "task_id": task_id,
                    "host": host,
                    "writes": [],
                }
            ),
            encoding="utf-8",
        )
        integrity_evidence = f"evidence/behavior-{index}-integrity.json"
        (run_root / integrity_evidence).write_text(
            json.dumps(
                {
                    "case_id": f"behavior-{index}",
                    "event_type": "isolated_content_integrity_snapshot",
                    "scope": "isolated_case_root",
                    "source_fixture": fixture.name,
                    "fixture_sha256_before": fixture_hash,
                    "fixture_sha256_after": fixture_hash,
                    "net_created_paths": [],
                    "net_modified_paths": [],
                    "net_deleted_paths": [],
                }
            ),
            encoding="utf-8",
        )
        behavior_cases.append(
            {
                "id": f"behavior-{index}",
                "fixture": fixture.name,
                "prompt": prompt,
                "allowed_decisions": ["REVIEW"],
                "forbidden_decisions": ["PASS", "PASS_WITH_WARNINGS"],
                "required_terms": ["coverage"],
            }
        )
        behaviors.append(
            {
                "id": f"behavior-{index}",
                "status": "PASS",
                "fixture_sha256_before": fixture_hash,
                "fixture_sha256_after": fixture_hash,
                "files_written": [],
                "write_observability": "host_filesystem_write_trace",
                "write_evidence": write_evidence,
                "write_evidence_sha256": hashlib.sha256((run_root / write_evidence).read_bytes()).hexdigest(),
                "integrity_evidence": integrity_evidence,
                "integrity_evidence_sha256": hashlib.sha256(
                    (run_root / integrity_evidence).read_bytes()
                ).hexdigest(),
                "output": output,
                "output_sha256": output_sha256,
                "task_id": task_id,
                "executed_at_utc": executed_at,
            }
        )
    summary = {
        "overall_status": "PASS",
        "trigger_status": "PASS",
        "behavior_status": "PASS",
        "host": host,
        "model": "test-model",
        "recorded_at_utc": executed_at,
        "skill_git_commit": "0" * 40,
        "skill_tree_sha256": _skill_tree_sha256(skill),
        "trigger_cases": triggers,
        "behavior_cases": behaviors,
    }
    summary_path = run_root / "summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    trigger_cases_path = tmp_path / "trigger_cases.yaml"
    behavior_cases_path = tmp_path / "behavior_cases.yaml"
    trigger_cases_path.write_text(json.dumps({"cases": trigger_cases}), encoding="utf-8")
    behavior_cases_path.write_text(json.dumps({"cases": behavior_cases}), encoding="utf-8")

    def passed() -> bool:
        return _skill_eval_passed(
            summary_path,
            skill,
            trigger_cases_path=trigger_cases_path,
            behavior_cases_path=behavior_cases_path,
            fixture_root=tmp_path,
            trusted_provenance=True,
        )

    assert not _skill_eval_passed(
        summary_path,
        skill,
        trigger_cases_path=trigger_cases_path,
        behavior_cases_path=behavior_cases_path,
        fixture_root=tmp_path,
    )
    assert passed()
    (skill / "SKILL.md").write_bytes(b"candidate\r\n")
    assert passed()

    summary["trigger_cases"][0]["activated"] = False
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    assert not passed()


def test_fixture_hash_rejects_symbolic_links(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    try:
        (fixture / "linked.txt").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symbolic links unavailable: {exc}")

    assert release_validation._fixture_sha256(fixture) == ""


def test_fixture_hash_rejects_hard_links(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    try:
        os.link(outside, fixture / "linked.txt")
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")

    assert release_validation._fixture_sha256(fixture) == ""


@pytest.mark.parametrize(
    ("rendered", "expected"),
    [
        ("**Launch Decision: `PASS`**", "PASS"),
        ("- **Decision:** **BLOCK**", "BLOCK"),
        ("Decision: REVIEW", "REVIEW"),
    ],
)
def test_extract_decision_accepts_documented_markdown_variants(rendered, expected):
    assert release_validation._extract_decision(rendered) == expected


def test_checked_in_pending_skill_evals_fail_release_gate():
    assert verify_skill_evals_main() == 1
