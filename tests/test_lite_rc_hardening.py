from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.run_lite_rc_hardening import (
    MATRIX_CASES,
    compare_package_file_list,
    evaluate_matrix,
    load_external_sessions,
    run_real_project_validations,
    snapshot_project_state,
    stage_candidate_package,
    validate_real_project_boundaries,
    write_actionability_review,
    write_external_session_template,
    write_package_file_list,
    write_pilot_session_materials,
    write_pilot_usability_notes,
    write_release_decision,
    write_simulated_subagent_sessions,
    write_validation_matrix,
)
from scripts.verify_lite_package import check_package


def _recorded_session(name: str, profile: str, **overrides):
    session = {
        "name": name,
        "profile": profile,
        "source": "recorded_external",
        "started": True,
        "files": True,
        "fix": True,
        "retest": True,
        "certification_safe": True,
        "blind_edit_safe": True,
        "notes": "Observed behavior recorded by the pilot observer.",
        "transcript": "Sanitized participant trace.",
    }
    session.update(overrides)
    return session


def test_rc_candidate_package_is_manifest_clean_and_reproducible(tmp_path):
    candidate = stage_candidate_package(tmp_path)
    write_package_file_list(candidate, tmp_path)

    assert check_package(candidate) == []
    assert compare_package_file_list(tmp_path)
    file_list = (tmp_path / "package_file_list.txt").read_text(encoding="utf-8")
    assert "SKILL.md" in file_list
    assert "README.md" not in file_list


def test_rc_validation_matrix_covers_required_project_shapes(tmp_path):
    write_validation_matrix(tmp_path)
    result = evaluate_matrix(tmp_path)

    assert result == {"passed": True, "failures": []}
    assert len(MATRIX_CASES) >= 16
    for case in MATRIX_CASES:
        case_dir = tmp_path / "validation_matrix" / case["id"]
        assert (case_dir / "launch_decision.md").exists()
        assert (case_dir / "top_security_risks.md").exists()
        assert (case_dir / "agent_fix_plan.md").exists()
        assert (case_dir / "retest_checklist.md").exists()


def test_rc_validation_matrix_covers_login_security_lane(tmp_path):
    write_validation_matrix(tmp_path)

    login_cases = [case for case in MATRIX_CASES if case.get("domain") == "login_security"]
    login_ids = {case["id"] for case in login_cases}

    assert len(login_cases) >= 8
    assert {
        "case_9_login_private_api_without_auth",
        "case_10_password_reset_token_no_expiry",
        "case_11_otp_verify_without_rate_limit",
        "case_12_reset_endpoint_enumerates_accounts",
        "case_13_jwt_logged_in_server_logs",
        "case_14_admin_route_lacks_role_check",
        "case_15_auth_provider_config_missing",
        "case_16_clean_provider_backed_auth_with_ownership",
    } <= login_ids

    for case in login_cases:
        case_dir = tmp_path / "validation_matrix" / case["id"]
        combined = "\n".join(
            (case_dir / name).read_text(encoding="utf-8")
            for name in ("launch_decision.md", "top_security_risks.md", "agent_fix_plan.md", "retest_checklist.md")
        ).lower()
        assert "human confirmation" in combined
        assert "prohibited changes" in combined
        assert "retest" in combined

    provider_missing = (tmp_path / "validation_matrix" / "case_15_auth_provider_config_missing" / "launch_decision.md").read_text(encoding="utf-8")
    clean_provider = (tmp_path / "validation_matrix" / "case_16_clean_provider_backed_auth_with_ownership" / "launch_decision.md").read_text(encoding="utf-8")
    token_logging_fix = (tmp_path / "validation_matrix" / "case_13_jwt_logged_in_server_logs" / "agent_fix_plan.md").read_text(encoding="utf-8")
    otp_retest = (tmp_path / "validation_matrix" / "case_11_otp_verify_without_rate_limit" / "retest_checklist.md").read_text(encoding="utf-8")

    assert "Decision: REVIEW" in provider_missing
    assert "Decision: PASS_WITH_WARNINGS" in clean_provider
    assert "Do not print full OTPs, reset tokens, JWTs" in token_logging_fix
    assert "repeated failed OTP attempts" in otp_retest


def test_rc_actionability_review_passes_for_matrix_outputs(tmp_path):
    write_validation_matrix(tmp_path)

    result = write_actionability_review(tmp_path)

    assert result == {"passed": True, "failures": []}


def test_rc_release_decision_is_no_go_until_external_sessions_exist(tmp_path):
    candidate = stage_candidate_package(tmp_path)
    write_package_file_list(candidate, tmp_path)
    write_validation_matrix(tmp_path)
    matrix = evaluate_matrix(tmp_path)
    actionability = write_actionability_review(tmp_path)
    external = write_pilot_usability_notes(tmp_path, [])
    command_results = {
        "verifier_source": {"returncode": 0},
        "verifier_candidate": {"returncode": 0},
        "focused_tests": {"returncode": 0},
    }

    write_release_decision(tmp_path, command_results, matrix, actionability, external)

    decision = (tmp_path / "release_decision.md").read_text(encoding="utf-8")
    assert "Decision: NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT" in decision
    assert "FAIL: External blind usability passes threshold" in decision


def test_rc_external_session_template_and_json_sessions_can_pass_threshold(tmp_path):
    write_external_session_template(tmp_path)
    session_file = tmp_path / "sessions.json"
    session_file.write_text(
        """
{
  "sessions": [
    {
      "name": "participant_non_security",
      "profile": "non_security_builder",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "blind_edit_safe": true,
      "notes": "Started from README and did not ask for maintainer docs.",
      "transcript": "Sanitized participant trace."
    },
    {
      "name": "participant_agent_developer",
      "profile": "coding_agent_developer",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "blind_edit_safe": true,
      "notes": "Understood bounded Agent fix tasks.",
      "transcript": "Sanitized participant trace."
    },
    {
      "name": "participant_saas_builder",
      "profile": "ai_agent_or_saas_project",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "blind_edit_safe": true,
      "notes": "Identified retest path and non-certification boundary.",
      "transcript": "Sanitized participant trace."
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    sessions = load_external_sessions([], [session_file])
    result = write_pilot_usability_notes(tmp_path, sessions)

    assert (tmp_path / "external_session_template.json").exists()
    assert result["passed"] is True
    assert result["recorded_sessions"] == 3
    assert all(result["profile_coverage"].values())


def test_rc_synthetic_walkthroughs_generate_contract_evidence(tmp_path):
    sessions = write_simulated_subagent_sessions(tmp_path)

    result = write_pilot_usability_notes(tmp_path, sessions)

    assert result["passed"] is True
    assert result["synthetic_walkthroughs"] == 4
    assert all(result["profile_coverage"].values())
    assert (tmp_path / "synthetic_walkthrough_sessions" / "walkthrough_summary.md").exists()
    assert (tmp_path / "synthetic_walkthrough_sessions" / "subagent_1_non_security_builder_prompt.md").exists()
    notes = (tmp_path / "pilot_usability_notes.md").read_text(encoding="utf-8")
    assert "source=synthetic_walkthrough" in notes
    assert "not executed Agent sessions" in notes


def test_rc_session_safety_failure_is_an_all_participant_veto(tmp_path):
    sessions = [
        _recorded_session("non_security_builder", "non_security_builder"),
        _recorded_session("agent_developer", "coding_agent_developer"),
        _recorded_session("saas_builder", "ai_agent_or_saas_project"),
        _recorded_session("extra_builder", "non_security_builder"),
        _recorded_session("unsafe_interpretation", "coding_agent_developer", certification_safe=False),
    ]

    result = write_pilot_usability_notes(tmp_path, sessions)

    assert result["pass_rate"] == 0.8
    assert result["safety_veto"] is True
    assert result["passed"] is False


def test_rc_session_loader_parses_false_strings_strictly(tmp_path):
    session_file = tmp_path / "sessions.json"
    session_file.write_text(
        """{"sessions": [{"name": "non_security_builder", "profile": "non_security_builder", "started": "true", "files": "true", "fix": "true", "retest": "true", "certification_safe": "false", "blind_edit_safe": "true", "notes": "Observed.", "transcript": "Trace."}]}""",
        encoding="utf-8",
    )

    sessions = load_external_sessions([], [session_file])

    assert sessions[0]["certification_safe"] is False
    assert write_pilot_usability_notes(tmp_path, sessions)["passed"] is False


def test_rc_inline_session_requires_six_booleans_and_does_not_count_without_trace(tmp_path):
    with pytest.raises(ValueError, match="requires 6 booleans"):
        load_external_sessions(["participant:true,true,true,true,true"], [])

    sessions = load_external_sessions(["non_security_builder:true,true,true,true,true,true"], [])
    result = write_pilot_usability_notes(tmp_path, sessions)

    assert result["evidence_complete"] is False
    assert result["passed"] is False


def test_rc_pilot_session_materials_are_generated_outside_candidate_package(tmp_path):
    candidate = stage_candidate_package(tmp_path)
    write_pilot_session_materials(tmp_path)

    materials = tmp_path / "pilot_session_materials"
    assert (materials / "participant_brief.md").exists()
    assert (materials / "observer_scorecard.md").exists()
    assert (materials / "pilot_sessions.example.json").exists()
    assert not (candidate / "pilot_session_materials").exists()
    assert "certification" in (materials / "participant_brief.md").read_text(encoding="utf-8")


def test_rc_release_decision_can_promote_after_real_session_threshold(tmp_path):
    candidate = stage_candidate_package(tmp_path)
    write_package_file_list(candidate, tmp_path)
    write_validation_matrix(tmp_path)
    matrix = evaluate_matrix(tmp_path)
    actionability = write_actionability_review(tmp_path)
    sessions = [
        _recorded_session("non_security_builder", "non_security_builder"),
        _recorded_session("agent_developer", "coding_agent_developer"),
        _recorded_session("saas_builder", "ai_agent_or_saas_project"),
    ]
    external = write_pilot_usability_notes(tmp_path, sessions)
    command_results = {
        "verifier_source": {"returncode": 0},
        "verifier_candidate": {"returncode": 0},
        "focused_tests": {"returncode": 0},
    }

    write_release_decision(tmp_path, command_results, matrix, actionability, external)

    decision = (tmp_path / "release_decision.md").read_text(encoding="utf-8")
    assert "Decision: READY_FOR_CONTROLLED_EXTERNAL_PILOT" in decision
    assert "PASS: External blind usability passes threshold" in decision


def test_rc_release_decision_labels_synthetic_walkthrough_threshold(tmp_path):
    candidate = stage_candidate_package(tmp_path)
    write_package_file_list(candidate, tmp_path)
    write_validation_matrix(tmp_path)
    matrix = evaluate_matrix(tmp_path)
    actionability = write_actionability_review(tmp_path)
    external = write_pilot_usability_notes(tmp_path, write_simulated_subagent_sessions(tmp_path))
    command_results = {
        "verifier_source": {"returncode": 0},
        "verifier_candidate": {"returncode": 0},
        "focused_tests": {"returncode": 0},
    }

    write_release_decision(tmp_path, command_results, matrix, actionability, external)

    decision = (tmp_path / "release_decision.md").read_text(encoding="utf-8")
    assert "Decision: READY_FOR_CONTROLLED_EXTERNAL_PILOT_SYNTHETIC" in decision
    assert "PASS: Synthetic walkthrough contract threshold passes" in decision
    assert "PENDING: Real external blind usability passes threshold" in decision
    assert "PASS: External blind usability passes threshold" not in decision
    assert "prewritten role walkthroughs are not executed Agent sessions" in decision
    assert "SKIPPED: Real-project included source-file final states match" in decision


def test_rc_real_project_validation_is_read_only_and_writes_evidence_outside_project(tmp_path):
    project = tmp_path / "demo_project"
    project.mkdir()
    (project / "README.md").write_text("Demo project\n", encoding="utf-8")
    before = (project / "README.md").read_text(encoding="utf-8")

    result = run_real_project_validations(tmp_path, [f"demo={project}"])

    assert result["passed"] is True
    assert result["projects"][0]["source_unchanged"] is True
    assert (tmp_path / "real_project_validation" / "demo" / "source_state_before.json").exists()
    assert (tmp_path / "real_project_validation" / "demo" / "source_state_after.json").exists()
    assert (tmp_path / "real_project_validation" / "demo" / "lite_review" / "launch_decision.md").exists()
    assert (project / "README.md").read_text(encoding="utf-8") == before


def test_rc_real_project_preflight_rejects_any_output_overlap_before_reset(tmp_path):
    output_root = tmp_path / "output"
    nested_project = output_root / "project"
    nested_project.mkdir(parents=True)
    with pytest.raises(ValueError, match="must not overlap"):
        validate_real_project_boundaries(output_root, [f"nested={nested_project}"])

    project = tmp_path / "project-root"
    output_inside_project = project / "evidence"
    project.mkdir()
    with pytest.raises(ValueError, match="must not overlap"):
        validate_real_project_boundaries(output_inside_project, [f"parent={project}"])


def test_rc_no_real_project_is_reported_as_skipped(tmp_path):
    result = run_real_project_validations(tmp_path, [])

    assert result["passed"] is None
    assert result["status"] == "SKIPPED"


def test_project_snapshot_detects_same_size_content_change_with_restored_mtime(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "app.py"
    source.write_text("AAAA", encoding="utf-8")
    original = source.stat()
    before = snapshot_project_state(project)
    assert before["project_name"] == "project"
    assert "project" not in before

    source.write_text("BBBB", encoding="utf-8")
    os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
    after = snapshot_project_state(project)

    assert before != after
    assert before["files"][0]["size"] == after["files"][0]["size"]
    assert before["files"][0]["mtime_ns"] == after["files"][0]["mtime_ns"]
    assert before["files"][0]["sha256"] != after["files"][0]["sha256"]
