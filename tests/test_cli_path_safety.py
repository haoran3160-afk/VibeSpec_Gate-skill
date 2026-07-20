from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


WRITING_COMMANDS = ("scan", "report", "loop", "review")


@pytest.mark.parametrize("command_name", WRITING_COMMANDS)
@pytest.mark.parametrize("relationship", ("equal", "inside", "contains"))
def test_writing_cli_rejects_project_output_overlap_before_writing(tmp_path, command_name, relationship):
    project, output = _overlapping_paths(tmp_path, relationship)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    findings = inputs / "findings.json"
    findings.write_text("[]\n", encoding="utf-8")
    (project / "keep.txt").write_text("unchanged\n", encoding="utf-8")
    before = _file_snapshot(tmp_path)

    result = _run(command_name, project, output, findings)

    assert result.returncode != 0
    assert "must not overlap" in result.stdout + result.stderr
    assert _file_snapshot(tmp_path) == before


@pytest.mark.parametrize("command_name", WRITING_COMMANDS)
def test_writing_cli_rejects_hard_link_alias_between_project_and_output(tmp_path, command_name):
    project = tmp_path / "project"
    project.mkdir()
    project_file = project / "keep.txt"
    project_file.write_text("unchanged\n", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    _hard_link_or_skip(project_file, output / "findings.json")
    findings = tmp_path / "input-findings.json"
    findings.write_text("[]\n", encoding="utf-8")
    before = _file_snapshot(tmp_path)

    result = _run(command_name, project, output, findings)

    assert result.returncode != 0
    assert "must not overlap" in result.stdout + result.stderr
    assert _file_snapshot(tmp_path) == before


@pytest.mark.parametrize("command_name", ("report", "loop", "review"))
@pytest.mark.parametrize("relationship", ("equal", "inside", "contains"))
def test_writing_cli_rejects_findings_output_overlap_before_writing(tmp_path, command_name, relationship):
    project = tmp_path / "project"
    project.mkdir()
    (project / "keep.txt").write_text("unchanged\n", encoding="utf-8")
    findings, output = _overlapping_input_paths(tmp_path, relationship, "input-findings.json")
    before = _file_snapshot(tmp_path)

    result = _run(command_name, project, output, findings)

    assert result.returncode != 0
    assert "must not overlap" in result.stdout + result.stderr
    assert _file_snapshot(tmp_path) == before


@pytest.mark.parametrize("command_name", ("report", "loop", "review"))
def test_writing_cli_rejects_hard_link_alias_between_findings_and_output(tmp_path, command_name):
    project = tmp_path / "project"
    project.mkdir()
    (project / "keep.txt").write_text("unchanged\n", encoding="utf-8")
    findings = tmp_path / "input-findings.json"
    findings.write_text("[]\n", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    _hard_link_or_skip(findings, output / "findings.json")
    before = _file_snapshot(tmp_path)

    result = _run(command_name, project, output, findings)

    assert result.returncode != 0
    assert "must not overlap" in result.stdout + result.stderr
    assert _file_snapshot(tmp_path) == before


@pytest.mark.parametrize("command_name", ("scan", "loop"))
@pytest.mark.parametrize("relationship", ("equal", "inside", "contains"))
def test_writing_cli_rejects_suppression_output_overlap_before_writing(tmp_path, command_name, relationship):
    project = tmp_path / "project"
    project.mkdir()
    (project / "keep.txt").write_text("unchanged\n", encoding="utf-8")
    findings = tmp_path / "previous-findings.json"
    findings.write_text("[]\n", encoding="utf-8")
    suppression, output = _overlapping_input_paths(tmp_path, relationship, "vibespec_gate.suppressions.json")
    before = _file_snapshot(tmp_path)

    result = _run(command_name, project, output, findings, suppression)

    assert result.returncode != 0
    assert "must not overlap" in result.stdout + result.stderr
    assert _file_snapshot(tmp_path) == before


def _overlapping_paths(tmp_path: Path, relationship: str) -> tuple[Path, Path]:
    if relationship == "contains":
        output = tmp_path / "output"
        project = output / "project"
    else:
        project = tmp_path / "project"
        output = project if relationship == "equal" else project / "output"
    project.mkdir(parents=True)
    return project, output


def _overlapping_input_paths(tmp_path: Path, relationship: str, file_name: str) -> tuple[Path, Path]:
    if relationship == "contains":
        output = tmp_path / "output"
        output.mkdir()
        input_path = output / file_name
        input_path.write_text("[]\n", encoding="utf-8")
    else:
        input_path = tmp_path / "input"
        input_path.mkdir()
        output = input_path if relationship == "equal" else input_path / "output"
    return input_path, output


def _run(
    command_name: str,
    project: Path,
    output: Path,
    findings: Path,
    suppression: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    commands = {
        "scan": ["scan", str(project), "--output", str(output), "--no-adapters"],
        "report": ["report", str(findings), "--project", str(project), "--output", str(output)],
        "loop": [
            "loop",
            str(project),
            "--previous",
            str(findings),
            "--output",
            str(output),
            "--no-adapters",
        ],
        "review": ["review", str(findings), "--project", str(project), "--output", str(output)],
    }
    if suppression is not None:
        commands[command_name].extend(["--suppressions", str(suppression)])
    return subprocess.run(
        [sys.executable, "-m", "vibespec_gate.cli", *commands[command_name]],
        cwd=Path.cwd(),
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )


def _file_snapshot(root: Path) -> dict[str, tuple[str, bytes | None]]:
    return {
        path.relative_to(root).as_posix(): ("file", path.read_bytes()) if path.is_file() else ("dir", None)
        for path in sorted(root.rglob("*"))
        if path.is_file() or path.is_dir()
    }


def _hard_link_or_skip(source: Path, target: Path) -> None:
    try:
        os.link(source, target)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env
