from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_skill_blackbox_evals import (
    _disabled_user_skills_override,
    _extract_decision,
    _parse_jsonl,
    _require_disjoint_directories,
    _require_new_directory,
    _semantic_failures,
    _skill_resources_read,
    _snapshot_diff,
    _snapshot_tree,
    _user_skill_names_read,
    _write_activity,
)


def _command_event(
    command: str,
    *,
    status: str = "completed",
    exit_code: int = 0,
    aggregated_output: str = "",
) -> dict:
    return {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": command,
            "status": status,
            "exit_code": exit_code,
            "aggregated_output": aggregated_output,
        },
    }


def test_jsonl_parser_ignores_non_json_host_warnings():
    events = _parse_jsonl(
        "warning text\n"
        '{"type":"thread.started","thread_id":"task-1"}\n'
        '{"type":"turn.started"}\n'
    )

    assert events == [
        {"type": "thread.started", "thread_id": "task-1"},
        {"type": "turn.started"},
    ]


def test_activation_requires_successful_reads_of_both_skill_resources(tmp_path: Path):
    skill_source = tmp_path / "source"
    skill_root = tmp_path / "installed"
    for resource in ("review-protocol.md", "evidence-coverage.md"):
        source = skill_source / "references" / resource
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"# {resource}\n", encoding="utf-8")
    skill = str(skill_root).replace("\\", "\\\\")
    events = [
        _command_event(
            f"Get-Content '{skill}\\references\\review-protocol.md'",
            aggregated_output="# review-protocol.md\n",
        ),
        _command_event(
            f"Get-Content '{skill}\\references\\evidence-coverage.md'",
            aggregated_output="# evidence-coverage.md\n",
        ),
    ]

    assert _skill_resources_read(
        events,
        skill_root=skill_root,
        skill_source=skill_source,
    ) == {
        "references/review-protocol.md",
        "references/evidence-coverage.md",
    }
    assert not _skill_resources_read(
        events[:1],
        skill_root=skill_root,
        skill_source=skill_source,
    ) == {
        "references/review-protocol.md",
        "references/evidence-coverage.md",
    }


@pytest.mark.parametrize(
    ("status", "exit_code", "command", "output"),
    [
        ("declined", -1, "Get-Content '{path}'", "{content}"),
        ("failed", 1, "Get-Content '{path}'", "{content}"),
        ("completed", 0, "Write-Output '{path}'", "{content}"),
        ("completed", 0, "Get-Content '{path}'", "wrong content\n"),
    ],
)
def test_activation_rejects_unsuccessful_or_unproven_reads(
    tmp_path: Path,
    status: str,
    exit_code: int,
    command: str,
    output: str,
):
    skill_source = tmp_path / "source"
    skill_root = tmp_path / "installed"
    resource = skill_source / "references/review-protocol.md"
    resource.parent.mkdir(parents=True)
    resource.write_text("protocol content\n", encoding="utf-8")
    installed_resource = skill_root / "references/review-protocol.md"
    event = _command_event(
        command.format(path=installed_resource, content="protocol content"),
        status=status,
        exit_code=exit_code,
        aggregated_output=output.format(content="protocol content", path=installed_resource),
    )

    assert _skill_resources_read(
        [event],
        skill_root=skill_root,
        skill_source=skill_source,
    ) == set()


def test_write_activity_separates_completed_writes_from_blocked_attempts():
    writes, attempts = _write_activity(
        [
            _command_event("Get-Content file.txt"),
            _command_event("Set-Content -LiteralPath file.txt -Value changed"),
            _command_event(
                "Remove-Item -LiteralPath file.txt",
                status="declined",
                exit_code=-1,
            ),
        ]
    )

    assert len(writes) == 1
    assert "Set-Content" in writes[0]["command"]
    assert len(attempts) == 1
    assert "Remove-Item" in attempts[0]["command"]


@pytest.mark.parametrize(
    "command",
    [
        "py -3 -c \"from pathlib import Path; Path('x').write_text('x')\"",
        "node -e \"require('fs').writeFileSync('x','x')\"",
        "[System.IO.File]::WriteAllText('x', 'x')",
        "Get-Content source.txt | tee target.txt",
        "dd if=source of=target",
        "Write-Output x 1> target.txt",
        "git restore file.txt",
    ],
)
def test_write_activity_flags_indirect_write_commands(command: str):
    writes, attempts = _write_activity([_command_event(command)])

    assert len(writes) == 1
    assert attempts == []


def test_user_skill_override_disables_known_conflicting_skill(tmp_path: Path):
    user_skills = tmp_path / ".agents/skills"
    candidate = user_skills / "vibespec-gate"
    other = user_skills / "architecture-patterns"
    for skill in (candidate, other):
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text("skill\n", encoding="utf-8")

    override = _disabled_user_skills_override(user_skills, candidate)

    assert str(other / "SKILL.md").replace("\\", "\\\\") in override
    assert str(candidate / "SKILL.md").replace("\\", "\\\\") not in override
    assert "enabled=false" in override


def test_user_skill_trace_inventory_detects_target_and_unexpected_skills(tmp_path: Path):
    user_skills = tmp_path / ".agents/skills"
    events = [
        _command_event(
            f"Get-Content '{user_skills / 'vibespec-gate/SKILL.md'}'"
        ),
        _command_event(
            f"Get-Content '{user_skills / 'other-skill/SKILL.md'}'"
        ),
    ]

    assert _user_skill_names_read(events, user_skills_root=user_skills) == {
        "vibespec-gate",
        "other-skill",
    }


def test_semantic_gate_requires_canonical_contract():
    case = {
        "id": "behavior-empty-project",
        "allowed_decisions": ["REVIEW"],
        "forbidden_decisions": ["PASS", "PASS_WITH_WARNINGS"],
        "required_terms": ["coverage", "missing"],
    }
    output = """Coverage: insufficient
Decision: REVIEW

Highest-Impact Risks
none identified

Missing Evidence
project files are missing

Limitations
coverage is limited to an empty project

Human Confirmation Required
provide the intended project

Human-Gated Repair Tasks
none identified

Project-Specific Retests
repeat after evidence is available
"""

    assert _extract_decision(output) == "REVIEW"
    assert _semantic_failures(case, output, "REVIEW") == []
    assert "missing canonical Decision line" in _semantic_failures(
        case,
        output.replace("Decision: REVIEW", "**Decision**\nREVIEW"),
        "",
    )


def test_snapshot_includes_directories_and_reports_all_change_types(tmp_path: Path):
    root = tmp_path / "fixture"
    root.mkdir()
    nested = root / "nested"
    nested.mkdir()
    original = nested / "original.txt"
    original.write_text("before\n", encoding="utf-8")
    deleted = root / "deleted.txt"
    deleted.write_text("delete\n", encoding="utf-8")
    before = _snapshot_tree(root)

    original.write_text("after\n", encoding="utf-8")
    deleted.unlink()
    created_dir = root / "created"
    created_dir.mkdir()
    (created_dir / "new.txt").write_text("new\n", encoding="utf-8")
    after = _snapshot_tree(root)

    created, modified, removed = _snapshot_diff(before, after)
    assert created == ["created/", "created/new.txt"]
    assert modified == ["nested/original.txt"]
    assert removed == ["deleted.txt"]


def test_new_directory_must_be_below_an_approved_root(tmp_path: Path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()

    _require_new_directory(
        allowed / "candidate",
        "candidate",
        allowed_roots=(allowed,),
    )
    with pytest.raises(SystemExit, match="unsafe candidate"):
        _require_new_directory(
            tmp_path / "outside",
            "candidate",
            allowed_roots=(allowed,),
        )


def test_new_directory_refuses_existing_or_overlapping_roots(tmp_path: Path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    existing = allowed / "existing"
    existing.mkdir()

    with pytest.raises(SystemExit, match="refusing to overwrite"):
        _require_new_directory(existing, "candidate", allowed_roots=(allowed,))
    with pytest.raises(SystemExit, match="must not overlap"):
        _require_disjoint_directories(allowed / "run", allowed / "run/workspace")

    _require_disjoint_directories(allowed / "run", allowed / "workspace")
