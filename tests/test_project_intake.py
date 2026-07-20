from pathlib import Path

import pytest

from vibespec_gate.core.gate_decision import decide_gate
from vibespec_gate.core.project_intake import detect_profile


def test_detect_ai_agent_profile():
    profile = detect_profile(str(Path("tests/fixtures/vulnerable_ai_agent_app")), "ai-agent")
    assert profile.project_type == "AI Agent"
    assert "OpenAI SDK" in profile.technologies
    assert profile.coverage.coverage_status == "partial"
    assert not profile.coverage.allows_pass()


def test_api_route_project_is_not_misclassified_as_static_site():
    profile = detect_profile(str(Path("tests/fixtures/safe_demo_app")))

    assert profile.project_type == "Web App"
    assert profile.coverage.coverage_status == "complete"


def test_nested_route_directory_is_not_misclassified_as_static_site(tmp_path):
    route = tmp_path / "src" / "routes" / "health.ts"
    route.parent.mkdir(parents=True)
    route.write_text("export function health() { return { ok: true } }\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")

    profile = detect_profile(str(tmp_path))

    assert profile.project_type == "Web App"
    assert profile.coverage.coverage_status == "partial"
    assert decide_gate([], profile=profile)["decision"] == "REVIEW"


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


def test_unknown_source_extension_prevents_pass(tmp_path):
    source = tmp_path / "src" / "app.ts"
    source.parent.mkdir()
    source.write_text("export const version = 1\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "credentials.coffee").write_text(
        "api_key = 'REAL_LOOKING_SECRET_VALUE_123456789'\n",
        encoding="utf-8",
    )

    profile = detect_profile(str(tmp_path))
    decision = decide_gate([], profile=profile)

    assert profile.coverage.coverage_status == "partial"
    assert profile.coverage.files_skipped == 1
    assert "credentials.coffee" in profile.coverage.reason
    assert decision["decision"] == "REVIEW"


def test_common_style_and_lock_assets_do_not_create_false_unsupported_source(tmp_path):
    source = tmp_path / "src" / "app.ts"
    source.parent.mkdir()
    source.write_text("export const version = 1\n", encoding="utf-8")
    (tmp_path / "src" / "styles.css").write_text("body { color: black; }\n", encoding="utf-8")
    (tmp_path / "yarn.lock").write_text("# generated lockfile\n", encoding="utf-8")
    (tmp_path / ".DS_Store").write_bytes(b"metadata")
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")

    profile = detect_profile(str(tmp_path))

    assert profile.coverage.coverage_status == "complete"
    assert profile.coverage.files_skipped == 0
    assert decide_gate([], profile=profile)["decision"] == "PASS"


@pytest.mark.parametrize("mode", [None, "web-app", "ai-agent", "desktop", "cli"])
def test_manifest_only_project_never_has_complete_coverage(tmp_path, mode):
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")

    profile = detect_profile(str(tmp_path), mode)
    decision = decide_gate([], profile=profile)

    assert profile.coverage.coverage_status == "partial"
    assert not profile.coverage.allows_pass()
    assert decision["decision"] == "REVIEW"


def test_web_profile_requires_surface_specific_evidence(tmp_path):
    source = tmp_path / "src" / "page.tsx"
    source.parent.mkdir()
    source.write_text("export default function Page() { return null }\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")

    profile = detect_profile(str(tmp_path), "web-app")
    by_surface = {item.surface: item for item in profile.coverage.surfaces}

    assert profile.coverage.coverage_status == "partial"
    assert by_surface["auth"].status == "missing"
    assert by_surface["authorization"].status == "missing"
    assert by_surface["data_rules"].status == "not_applicable"
    assert decide_gate([], profile=profile)["decision"] == "REVIEW"
