from __future__ import annotations

from pathlib import Path

from scripts.run_lite_rc_hardening import (
    MATRIX_CASES,
    compare_package_file_list,
    evaluate_matrix,
    load_external_sessions,
    run_real_project_validations,
    stage_candidate_package,
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


def test_rc_candidate_package_is_manifest_clean_and_reproducible(tmp_path):
    candidate = stage_candidate_package(tmp_path)
    write_package_file_list(candidate, tmp_path)

    assert check_package(candidate) == []
    assert compare_package_file_list(tmp_path)
    assert "README.md" in (tmp_path / "package_file_list.txt").read_text(encoding="utf-8")


def test_rc_validation_matrix_covers_required_project_shapes(tmp_path):
    write_validation_matrix(tmp_path)
    result = evaluate_matrix(tmp_path)

    assert result == {"passed": True, "failures": []}
    assert len(MATRIX_CASES) == 8
    for case in MATRIX_CASES:
        case_dir = tmp_path / "validation_matrix" / case["id"]
        assert (case_dir / "launch_decision.md").exists()
        assert (case_dir / "top_security_risks.md").exists()
        assert (case_dir / "agent_fix_plan.md").exists()
        assert (case_dir / "retest_checklist.md").exists()


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
      "notes": "Started from README and did not ask for maintainer docs."
    },
    {
      "name": "participant_agent_developer",
      "profile": "coding_agent_developer",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "notes": "Understood bounded Agent fix tasks."
    },
    {
      "name": "participant_saas_builder",
      "profile": "ai_agent_or_saas_project",
      "started": true,
      "files": true,
      "fix": true,
      "retest": true,
      "certification_safe": true,
      "notes": "Identified retest path and non-certification boundary."
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


def test_rc_simulated_subagent_sessions_generate_evidence_and_pass_threshold(tmp_path):
    sessions = write_simulated_subagent_sessions(tmp_path)

    result = write_pilot_usability_notes(tmp_path, sessions)

    assert result["passed"] is True
    assert result["simulated_sessions"] == 4
    assert all(result["profile_coverage"].values())
    assert (tmp_path / "simulated_subagent_sessions" / "simulation_summary.md").exists()
    assert (tmp_path / "simulated_subagent_sessions" / "subagent_1_non_security_builder_prompt.md").exists()
    notes = (tmp_path / "pilot_usability_notes.md").read_text(encoding="utf-8")
    assert "source=simulated_subagent" in notes
    assert "not real blind user evidence" in notes


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
    sessions = load_external_sessions(
        [
            "non_security_builder:true,true,true,true,true",
            "agent_developer:true,true,true,true,true",
            "saas_builder:true,true,true,true,true",
        ],
        [],
    )
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


def test_rc_release_decision_labels_simulated_subagent_threshold(tmp_path):
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
    assert "Decision: READY_FOR_CONTROLLED_EXTERNAL_PILOT_SIMULATED" in decision
    assert "structured sub-agent sessions are not real external blind user evidence" in decision


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
