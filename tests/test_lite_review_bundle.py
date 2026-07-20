from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from vibespec_gate.core.coverage import REVIEW_SURFACES, EvidenceCoverage, SurfaceCoverage
from vibespec_gate.core.lite_review_bundle import _launch_decision, build_lite_review_bundle
from vibespec_gate.core.review_runner import run_review
from vibespec_gate.core.scan_runner import run_scan


def test_build_lite_review_bundle_creates_four_primary_outputs_and_evidence(tmp_path):
    review_output = tmp_path / "review"
    review_output.mkdir()
    _write_review_output(review_output)

    result = build_lite_review_bundle(review_output)

    bundle = review_output.with_name("review-lite-review")
    assert result["launch_decision"] == "BLOCK"
    assert (bundle / "launch_decision.md").exists()
    assert (bundle / "top_security_risks.md").exists()
    assert (bundle / "agent_fix_plan.md").exists()
    assert (bundle / "retest_checklist.md").exists()
    assert (bundle / "evidence" / "agent_review_decisions.json").exists()
    assert (bundle / "evidence" / "raw_findings.json").exists()
    launch = (bundle / "launch_decision.md").read_text(encoding="utf-8")
    fix_plan = (bundle / "agent_fix_plan.md").read_text(encoding="utf-8")
    assert "Decision: BLOCK" in launch
    assert "not a professional security certification" in launch
    assert "Human Confirmation Gate" in fix_plan
    assert "Do not auto-suppress findings" in fix_plan


def test_build_lite_review_bundle_uses_pass_with_warnings_for_nonblocking_candidates(tmp_path):
    coverage = EvidenceCoverage(
        coverage_status="complete",
        surfaces=[
            SurfaceCoverage(surface=surface, status="reviewed", source_refs=["package.json"])
            for surface in REVIEW_SURFACES
        ],
        files_discovered=1,
        files_inspected=1,
    )

    assert _launch_decision([{"recommended_action": "downgrade"}], coverage) == "PASS_WITH_WARNINGS"


def test_build_lite_review_bundle_requires_coverage_before_pass(tmp_path):
    review_output = tmp_path / "review"
    review_output.mkdir()
    _write_review_output(review_output, coverage_status=None, safe=True)

    result = build_lite_review_bundle(review_output)

    assert result["launch_decision"] == "REVIEW"
    launch = (review_output.with_name("review-lite-review") / "launch_decision.md").read_text(encoding="utf-8")
    assert "## Evidence Coverage" in launch
    assert "Coverage status: insufficient" in launch
    assert "Missing evidence" in launch


def test_lite_review_cli_builds_bundle(tmp_path):
    review_output = tmp_path / "review"
    bundle = tmp_path / "lite"
    review_output.mkdir()
    _write_review_output(review_output)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibespec_gate.cli",
            "lite-review",
            str(review_output),
            "--output",
            str(bundle),
        ],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["launch_decision"] == "BLOCK"
    assert (bundle / "launch_decision.md").exists()
    assert (bundle / "evidence" / "raw_findings.json").exists()


def test_bundle_helper_script_uses_safe_sibling_default(tmp_path):
    review_output = tmp_path / "review"
    review_output.mkdir()
    _write_review_output(review_output)

    result = subprocess.run(
        [sys.executable, "scripts/build_lite_review_bundle.py", str(review_output)],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (tmp_path / "review-lite-review" / "launch_decision.md").is_file()


def test_build_lite_review_bundle_rejects_incomplete_review_input_before_writing(tmp_path):
    review_output = tmp_path / "review"
    bundle = tmp_path / "bundle"
    review_output.mkdir()
    (review_output / "agent_review_decisions.json").write_text(
        json.dumps({"schema_version": "1.0", "summary": {}, "decisions": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        build_lite_review_bundle(review_output, bundle)

    assert not bundle.exists()


def test_build_lite_review_bundle_refuses_to_overwrite_existing_bundle(tmp_path):
    review_output = tmp_path / "review"
    bundle = tmp_path / "bundle"
    review_output.mkdir()
    _write_review_output(review_output)
    build_lite_review_bundle(review_output, bundle)
    original = (bundle / "launch_decision.md").read_bytes()

    with pytest.raises(ValueError, match="already exists"):
        build_lite_review_bundle(review_output, bundle)

    assert (bundle / "launch_decision.md").read_bytes() == original


def test_lite_review_cli_can_run_project_facade(tmp_path):
    project = tmp_path / "project"
    bundle = tmp_path / "lite-project"
    project.mkdir()
    (project / "README.md").write_text("Demo project\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vibespec_gate.cli",
            "lite-review",
            str(project),
            "--output",
            str(bundle),
            "--no-adapters",
        ],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert "scan" in payload
    assert "review" in payload
    assert payload["lite"]["bundle_dir"] == str(bundle.resolve())
    assert (bundle / "launch_decision.md").exists()
    assert (bundle / "evidence" / "scan" / "findings.json").exists()
    assert (bundle / "evidence" / "review_output" / "agent_review_decisions.json").exists()


def test_lite_review_cli_refuses_to_reuse_project_output_without_partial_overwrite(tmp_path):
    project = tmp_path / "project"
    bundle = tmp_path / "lite-project"
    project.mkdir()
    (project / "package.json").write_text("{}\n", encoding="utf-8")
    first = _run_lite_review(project, bundle)
    assert first.returncode == 0, first.stderr + first.stdout
    launch_before = (bundle / "launch_decision.md").read_bytes()
    findings_before = (bundle / "evidence" / "scan" / "findings.json").read_bytes()

    second = _run_lite_review(project, bundle)

    assert second.returncode == 1
    assert "already exists" in second.stdout
    assert (bundle / "launch_decision.md").read_bytes() == launch_before
    assert (bundle / "evidence" / "scan" / "findings.json").read_bytes() == findings_before


def test_lite_review_cli_requires_explicit_output_for_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    marker = project / "keep.txt"
    marker.write_text("unchanged\n", encoding="utf-8")

    result = _run_lite_review(project)

    assert result.returncode == 1
    assert "--output is required" in result.stdout
    assert marker.read_text(encoding="utf-8") == "unchanged\n"
    assert sorted(path.name for path in project.iterdir()) == ["keep.txt"]


def test_lite_review_cli_rejects_missing_target_before_writing(tmp_path):
    target = tmp_path / "missing"
    output = tmp_path / "output"

    result = _run_lite_review(target, output)

    assert result.returncode == 1
    assert "must be an existing directory" in result.stdout
    assert not output.exists()


@pytest.mark.parametrize("relationship", ["equal", "inside", "contains"])
def test_lite_review_cli_rejects_project_output_overlap_before_writing(tmp_path, relationship):
    if relationship == "contains":
        output = tmp_path / "output"
        project = output / "project"
    else:
        project = tmp_path / "project"
        output = project if relationship == "equal" else project / "output"
    project.mkdir(parents=True)
    marker = project / "keep.txt"
    marker.write_text("unchanged\n", encoding="utf-8")

    result = _run_lite_review(project, output)

    assert result.returncode == 1
    assert "must not overlap" in result.stdout
    assert marker.read_text(encoding="utf-8") == "unchanged\n"
    assert not (output / "launch_decision.md").exists()


@pytest.mark.parametrize("relationship", ["equal", "inside", "contains"])
def test_bundle_rejects_review_output_overlap_before_writing(tmp_path, relationship):
    if relationship == "contains":
        bundle = tmp_path / "bundle"
        review_output = bundle / "review"
    else:
        review_output = tmp_path / "review"
        bundle = review_output if relationship == "equal" else review_output / "bundle"
    review_output.mkdir(parents=True)
    _write_review_output(review_output)

    with pytest.raises(ValueError, match="must not overlap"):
        build_lite_review_bundle(review_output, bundle)

    assert not (bundle / "launch_decision.md").exists()


def _write_review_output(
    review_output: Path,
    *,
    coverage_status: str | None = "complete",
    safe: bool = False,
) -> None:
    if safe:
        project = review_output.parent / f"{review_output.name}-project"
        project.mkdir()
        (project / "package.json").write_text("{}\n", encoding="utf-8")
    else:
        project = Path("tests/fixtures/vulnerable_next_supabase_app").resolve()
    scan_output = review_output.parent / f"{review_output.name}-scan"
    run_scan(str(project), str(scan_output), include_adapters=False)
    run_review(
        str(scan_output / "findings.json"),
        str(project),
        str(review_output),
        include_p2=True,
    )
    if coverage_status is None:
        decisions_path = review_output / "agent_review_decisions.json"
        decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
        decisions["summary"].pop("coverage", None)
        decisions_path.write_text(json.dumps(decisions, indent=2), encoding="utf-8")
        llm_path = review_output / "llm_review_packet.json"
        llm_packet = json.loads(llm_path.read_text(encoding="utf-8"))
        llm_packet["project_profile"].pop("coverage", None)
        llm_path.write_text(json.dumps(llm_packet, indent=2), encoding="utf-8")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run_lite_review(project: Path, output: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "vibespec_gate.cli", "lite-review", str(project), "--no-adapters"]
    if output is not None:
        command.extend(["--output", str(output)])
    return subprocess.run(
        command,
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )
