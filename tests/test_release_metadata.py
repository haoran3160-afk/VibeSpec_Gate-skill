from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from scripts.build_lite_package_zip import ARCHIVE_ROOT, build_lite_package
from scripts.verify_lite_package import REQUIRED_INCLUDE
from scripts.verify_release_metadata import release_tag_for, verify_release_metadata


def test_release_metadata_is_consistent():
    assert verify_release_metadata() == []
    assert verify_release_metadata(tag="v0.2.0-rc.1") == []
    assert release_tag_for("0.2.0rc1") == "v0.2.0-rc.1"
    assert release_tag_for("1.0.0") == "v1.0.0"


def test_release_metadata_rejects_mismatched_tag():
    failures = verify_release_metadata(tag="v0.1.0")

    assert any("does not match version tag" in failure for failure in failures)


def test_release_metadata_accepts_single_root_lite_archive():
    output_zip = Path.cwd() / "dist" / "test-release-metadata.zip"
    staging_dir = output_zip.with_suffix("")
    try:
        build_lite_package(staging_dir, output_zip)

        assert verify_release_metadata(archive=output_zip) == []
        with zipfile.ZipFile(output_zip) as bundle:
            names = {name for name in bundle.namelist() if not name.endswith("/")}
        assert names == {f"{ARCHIVE_ROOT}/{name}" for name in REQUIRED_INCLUDE}
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if output_zip.exists():
            output_zip.unlink()


def test_release_metadata_rejects_tampered_archive_content():
    output_zip = Path.cwd() / "dist" / "test-release-metadata-tampered.zip"
    try:
        with zipfile.ZipFile(output_zip, "w") as bundle:
            for name in REQUIRED_INCLUDE:
                bundle.writestr(f"{ARCHIVE_ROOT}/{name}", b"not release content")

        failures = verify_release_metadata(archive=output_zip)

        assert any("archive content differs from source" in failure for failure in failures)
    finally:
        if output_zip.exists():
            output_zip.unlink()


def test_release_workflow_binds_tag_to_master_and_portable_checksum():
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "fetch-depth: 0" in workflow
    assert 'git merge-base --is-ancestor "${GITHUB_SHA}" origin/master' in workflow
    assert 'verify_release_metadata.py --tag "${GITHUB_REF_NAME}"' in workflow
    assert "(cd dist && sha256sum vibespec-gate-lite.zip > SHA256SUMS)" in workflow
    assert "sha256sum dist/vibespec-gate-lite.zip" not in workflow
