from __future__ import annotations

import shutil
import uuid
import zipfile
from pathlib import Path

from scripts.build_lite_package_zip import ARCHIVE_ROOT, build_lite_package
from scripts.verify_lite_package import REQUIRED_INCLUDE, SKILL_SOURCE, check_package, check_source


def test_lite_package_source_satisfies_skill_unit_contract():
    assert check_source(Path.cwd()) == []


def test_repository_has_one_authoritative_skill_entry():
    skill_files = [
        path.relative_to(Path.cwd()).as_posix()
        for path in Path.cwd().rglob("SKILL.md")
        if not set(path.relative_to(Path.cwd()).parts) & {".git", "dist", "test output"}
    ]

    assert skill_files == ["skills/vibespec-gate/SKILL.md"]
    assert not Path("agents/openai.yaml").exists()


def test_lite_package_verifier_accepts_exact_runtime_package(tmp_path):
    _copy_required_package_files(tmp_path)

    assert check_package(tmp_path) == []


def test_skill_routes_every_reference_and_template():
    skill = (SKILL_SOURCE / "SKILL.md").read_text(encoding="utf-8")

    for relative_name in REQUIRED_INCLUDE:
        if relative_name in {"SKILL.md", "LICENSE", "agents/openai.yaml"}:
            continue
        assert relative_name in skill


def test_skill_requires_canonical_chat_decision_and_coverage_contract():
    skill = (SKILL_SOURCE / "SKILL.md").read_text(encoding="utf-8")

    for decision in ("BLOCK", "REVIEW", "PASS_WITH_WARNINGS", "PASS"):
        assert f"Decision: {decision}" in skill
    assert "Do not replace the token with synonyms" in skill
    assert "list all seven review surfaces" in skill
    for heading in (
        "Highest-Impact Risks",
        "Missing Evidence",
        "Limitations",
        "Human Confirmation Required",
        "Human-Gated Repair Tasks",
        "Project-Specific Retests",
    ):
        assert f"`{heading}`" in skill


def test_agent_metadata_disables_implicit_invocation():
    metadata = (SKILL_SOURCE / "agents/openai.yaml").read_text(encoding="utf-8")

    assert "allow_implicit_invocation: false" in metadata


def test_lite_package_zip_contains_only_runtime_skill_files():
    output_zip = Path.cwd() / "dist" / f"test-vibespec-gate-lite-{uuid.uuid4().hex}.zip"
    staging_dir = output_zip.with_suffix("")

    try:
        result = build_lite_package(staging_dir, output_zip)

        assert result["files"] == list(REQUIRED_INCLUDE)
        with zipfile.ZipFile(output_zip) as archive:
            names = {name for name in archive.namelist() if not name.endswith("/")}
        assert names == {f"{ARCHIVE_ROOT}/{name}" for name in REQUIRED_INCLUDE}
        assert not any("README" in name or "CHANGELOG" in name for name in names)
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if output_zip.exists():
            output_zip.unlink()


def test_lite_package_verifier_rejects_non_runtime_file(tmp_path):
    _copy_required_package_files(tmp_path)
    (tmp_path / "README.md").write_text("Not part of the install unit.\n", encoding="utf-8")

    failures = check_package(tmp_path)

    assert "package contains non-manifest file: README.md" in failures


def test_source_verifier_uses_manifest_include_block_as_authority(tmp_path):
    shutil.copytree(SKILL_SOURCE, tmp_path / SKILL_SOURCE)
    manifest = tmp_path / "docs/design/lite_skill_package_manifest.md"
    manifest.parent.mkdir(parents=True)
    text = Path("docs/design/lite_skill_package_manifest.md").read_text(encoding="utf-8")
    manifest.write_text(text.replace("assets/templates/retest-checklist.md", "README.md", 1), encoding="utf-8")

    failures = check_source(tmp_path)

    assert "missing Skill runtime file: README.md" in failures
    assert "package contains non-manifest file: assets/templates/retest-checklist.md" in failures


def test_lite_package_verifier_rejects_extra_frontmatter_field(tmp_path):
    _copy_required_package_files(tmp_path)
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(
            "description: Review launch security",
            "metadata: unsupported\ndescription: Review launch security",
        ),
        encoding="utf-8",
    )

    failures = check_package(tmp_path)

    assert "SKILL.md frontmatter must contain only the expected name and description fields" in failures


def test_readmes_have_user_facing_structure_and_current_install_contract():
    chinese = Path("README.md").read_text(encoding="utf-8")
    english = Path("README.en.md").read_text(encoding="utf-8")

    assert chinese.index("## 输出示例") < chinese.index("## 安装")
    assert chinese.index("## 能检查什么") < chinese.index("## 安装")
    assert english.index("## Example Output") < english.index("## Install")
    assert english.index("## What It Reviews") < english.index("## Install")
    for text in (chinese, english):
        assert "$HOME/.agents/skills/vibespec-gate" in text
        assert "$CODEX_HOME/skills/vibespec-gate" in text
        assert ".agents/skills/vibespec-gate" in text
        assert "skills/vibespec-gate" in text
        assert "/tree/master/skills/vibespec-gate" in text
        assert "0.2.0rc1" in text
        assert "PASS_WITH_WARNINGS" in text
        assert "/releases/download/v0.2.0-rc.1/vibespec-gate-lite.zip" in text
        assert "/releases/download/v0.2.0-rc.1/SHA256SUMS" in text
    assert not Path("README.zh-CN.md").exists()


def test_readmes_state_skill_cli_and_evidence_boundaries():
    for path in (Path("README.md"), Path("README.en.md")):
        text = path.read_text(encoding="utf-8")
        for term in ("auth", "authorization", "secrets", "data_rules", "deployment", "agent_tools", "desktop_ipc"):
            assert term in text
        assert "--output" in text
        assert "Python 3.10+" in text
        assert "evals/runs/2026-07-20/README.md" in text


def _copy_required_package_files(package_dir: Path) -> None:
    for file_name in REQUIRED_INCLUDE:
        source = SKILL_SOURCE / file_name
        destination = package_dir / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
