from __future__ import annotations

import shutil
import uuid
import zipfile
from pathlib import Path

from scripts.build_lite_package_zip import ARCHIVE_ROOT, build_lite_package
from scripts.verify_lite_package import REQUIRED_INCLUDE, check_package, check_source


def test_lite_package_source_docs_satisfy_manifest_contract():
    assert check_source(Path.cwd()) == []


def test_lite_package_verifier_accepts_required_prompt_only_package(tmp_path):
    _copy_required_package_files(tmp_path)

    assert check_package(tmp_path) == []


def test_lite_package_user_docs_include_login_security_evidence_lane():
    required_terms_by_file = {
        "README.zh-CN.md": ("登录", "注册", "密码重置", "OTP", "session", "rate-limit", "admin"),
        "examples/synthetic_review_example.md": ("ownership", "human confirmation", "retest"),
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
    output_zip = Path.cwd() / "dist" / f"test-vibespec-gate-lite-{uuid.uuid4().hex}.zip"
    staging_dir = output_zip.with_suffix("")

    try:
        result = build_lite_package(staging_dir, output_zip)

        assert result["files"] == list(REQUIRED_INCLUDE)
        assert output_zip.exists()
        with zipfile.ZipFile(output_zip) as archive:
            names = set(archive.namelist())
        expected = {f"{ARCHIVE_ROOT}/{name}" for name in REQUIRED_INCLUDE}
        assert names == expected
        assert f"{ARCHIVE_ROOT}/LICENSE" in names
        assert f"{ARCHIVE_ROOT}/README.md" in names
        assert f"{ARCHIVE_ROOT}/README.zh-CN.md" in names
        assert f"{ARCHIVE_ROOT}/agents/openai.yaml" in names
        assert not any(name.startswith(("tests/", "scripts/", "test output/")) for name in names)
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if output_zip.exists():
            output_zip.unlink()


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
            "The default Lite package is prompt-only.",
            "```powershell\npy -3 -m vibespec_gate.cli lite-review .\\my-project\n```\n\nThe default Lite package is prompt-only.",
        ),
        encoding="utf-8",
    )

    failures = check_package(tmp_path)

    assert any("README.md presents CLI command before the prompt-only default path" in failure for failure in failures)


def test_lite_package_has_install_data_and_translation_contracts():
    readme = Path("README.md").read_text(encoding="utf-8")
    chinese = Path("README.zh-CN.md").read_text(encoding="utf-8")

    assert "vibespec-gate\\SKILL.md" in readme
    assert "SYNTHETIC EXAMPLE" in readme
    assert "a `redacted` field is not a guarantee" in readme.lower()
    assert "redacted` 字段不保证" in chinese
    assert "README.en.md" not in REQUIRED_INCLUDE
    assert "agents/openai.yaml" in REQUIRED_INCLUDE


def _copy_required_package_files(package_dir: Path) -> None:
    root = Path.cwd()
    for file_name in REQUIRED_INCLUDE:
        source = root / file_name
        destination = package_dir / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
