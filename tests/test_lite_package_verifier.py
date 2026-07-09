from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from scripts.build_lite_package_zip import build_lite_package
from scripts.verify_lite_package import REQUIRED_INCLUDE, check_package, check_source


def test_lite_package_source_docs_satisfy_manifest_contract():
    assert check_source(Path.cwd()) == []


def test_lite_package_verifier_accepts_required_prompt_only_package(tmp_path):
    _copy_required_package_files(tmp_path)

    assert check_package(tmp_path) == []


def test_lite_package_user_docs_include_login_security_evidence_lane():
    required_terms_by_file = {
        "README.md": ("登录", "注册", "密码重置", "OTP", "session", "rate-limit", "admin"),
        "README.zh-CN.md": ("登录", "注册", "密码重置", "OTP", "session", "rate-limit", "admin"),
        "default": ("login", "signup", "password reset", "OTP", "session", "rate-limit", "admin"),
    }
    for file_name in REQUIRED_INCLUDE:
        if not file_name.endswith(".md"):
            continue
        terms = required_terms_by_file.get(file_name, required_terms_by_file["default"])
        text = (Path.cwd() / file_name).read_text(encoding="utf-8")
        for term in terms:
            assert term.lower() in text.lower(), f"{file_name} missing {term}"


def test_lite_package_zip_contains_only_prompt_only_files(tmp_path):
    output_zip = Path.cwd() / "dist" / "test-vibespec-gate-lite.zip"

    result = build_lite_package(output_zip.with_suffix(""), output_zip)

    assert result["files"] == list(REQUIRED_INCLUDE)
    assert output_zip.exists()
    with zipfile.ZipFile(output_zip) as archive:
        names = set(archive.namelist())
    assert set(REQUIRED_INCLUDE) <= names
    assert "LICENSE" in names
    assert "README.md" in names
    assert "README.en.md" in names
    assert "README.zh-CN.md" in names
    assert not any(name.startswith(("tests/", "scripts/", "test output/")) for name in names)


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
            "优先使用 prompt-only Lite 流程。",
            "```powershell\npy -3 -m vibespec_gate.cli lite-review .\\my-project\n```\n\n优先使用 prompt-only Lite 流程。",
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
