from pathlib import Path
import shutil
import uuid

from scripts.build_lite_package_zip import build_lite_package
from scripts.smoke_install_skill import smoke_install, smoke_install_archive
from scripts.verify_lite_package import REQUIRED_INCLUDE


def test_skill_installs_to_supported_skill_directories(tmp_path):
    agents_target = smoke_install(tmp_path)
    codex_target = smoke_install(tmp_path, ".codex/skills")

    assert agents_target == tmp_path.resolve() / ".agents" / "skills" / "vibespec-gate"
    assert codex_target == tmp_path.resolve() / ".codex" / "skills" / "vibespec-gate"
    for target in (agents_target, codex_target):
        assert {
            path.relative_to(target).as_posix()
            for path in target.rglob("*")
            if path.is_file()
        } == set(REQUIRED_INCLUDE)


def test_release_archive_installs_to_default_codex_directory(tmp_path):
    output_zip = Path.cwd() / "dist" / f"test-install-{uuid.uuid4().hex}.zip"
    staging_dir = output_zip.with_suffix("")
    try:
        build_lite_package(staging_dir, output_zip)

        target = smoke_install_archive(output_zip, tmp_path)

        assert target == tmp_path.resolve() / ".codex" / "skills" / "vibespec-gate"
        assert (target / "SKILL.md").is_file()
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if output_zip.exists():
            output_zip.unlink()
