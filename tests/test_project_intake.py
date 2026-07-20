from pathlib import Path

from vibespec_gate.core.gate_decision import decide_gate
from vibespec_gate.core.project_intake import detect_profile


def test_detect_ai_agent_profile():
    profile = detect_profile(str(Path("tests/fixtures/vulnerable_ai_agent_app")), "ai-agent")
    assert profile.project_type == "AI Agent"
    assert "OpenAI SDK" in profile.technologies
    assert profile.coverage.coverage_status == "complete"


def test_detect_profile_records_empty_project_as_insufficient(tmp_path):
    profile = detect_profile(str(tmp_path))

    assert profile.coverage.coverage_status == "insufficient"
    assert profile.coverage.files_discovered == 0
    assert profile.coverage.files_inspected == 0


def test_detect_profile_keeps_unknown_project_evidence_insufficient(tmp_path):
    (tmp_path / "notes.txt").write_text("unclassified content\n", encoding="utf-8")

    profile = detect_profile(str(tmp_path))

    assert profile.project_type == "Unknown"
    assert profile.coverage.coverage_status == "insufficient"
    assert not profile.coverage.allows_pass()
    assert all(surface.status == "missing" for surface in profile.coverage.surfaces)


def test_detect_profile_records_file_inventory_truncation(tmp_path):
    for index in range(201):
        (tmp_path / f"file-{index:03d}.txt").write_text("content\n", encoding="utf-8")

    profile = detect_profile(str(tmp_path))

    assert profile.coverage.coverage_status == "truncated"
    assert profile.coverage.files_discovered == 201
    assert profile.coverage.files_inspected == 200
    assert profile.coverage.files_skipped == 1
    assert all(surface.status == "truncated" for surface in profile.coverage.surfaces)


def test_unsupported_security_source_prevents_pass(tmp_path):
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "server.go").write_text('const token = "sk-test-not-scanned"\n', encoding="utf-8")

    profile = detect_profile(str(tmp_path))
    decision = decide_gate([], profile=profile)

    assert profile.coverage.coverage_status == "partial"
    assert profile.coverage.files_skipped == 1
    assert "server.go" in profile.coverage.reason
    assert decision["decision"] == "REVIEW"
