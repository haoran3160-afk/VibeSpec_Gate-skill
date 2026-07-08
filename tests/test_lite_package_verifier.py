from __future__ import annotations

import shutil
from pathlib import Path

from scripts.verify_lite_package import REQUIRED_INCLUDE, check_package, check_source


def test_lite_package_source_docs_satisfy_manifest_contract():
    assert check_source(Path.cwd()) == []


def test_lite_package_verifier_accepts_required_prompt_only_package(tmp_path):
    _copy_required_package_files(tmp_path)

    assert check_package(tmp_path) == []


def test_lite_package_verifier_rejects_excluded_package_files(tmp_path):
    _copy_required_package_files(tmp_path)
    excluded = tmp_path / "tests" / "test_internal.py"
    excluded.parent.mkdir(parents=True)
    excluded.write_text("# internal test\n", encoding="utf-8")

    failures = check_package(tmp_path)

    assert any("package contains non-manifest file: tests/test_internal.py" in failure for failure in failures)
    assert any("package contains excluded file: tests/test_internal.py" in failure for failure in failures)


def test_lite_package_verifier_rejects_cli_first_readme(tmp_path):
    _copy_required_package_files(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "Use it like this:",
            "```powershell\npy -3 -m vibesec.cli lite-review .\\my-project\n```\n\nUse it like this:",
        ),
        encoding="utf-8",
    )

    failures = check_package(tmp_path)

    assert any("README.md presents CLI command before the prompt-only default path" in failure for failure in failures)


def _copy_required_package_files(package_dir: Path) -> None:
    root = Path.cwd()
    for file_name in REQUIRED_INCLUDE:
        source = root / file_name
        destination = package_dir / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
