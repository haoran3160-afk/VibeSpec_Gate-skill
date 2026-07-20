from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.build_lite_package_zip import ARCHIVE_ROOT  # noqa: E402
from scripts.verify_lite_package import REQUIRED_INCLUDE, SKILL_SOURCE  # noqa: E402
from vibespec_gate import __version__  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify VibeSpec Gate release metadata and Lite archive.")
    parser.add_argument("--tag", help="Git tag to compare with the package version.")
    parser.add_argument("--archive", type=Path, help="Lite zip archive to validate.")
    args = parser.parse_args(argv)

    failures = verify_release_metadata(args.tag, args.archive)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"PASS release metadata: version={__version__}, tag={release_tag_for(__version__)}")
    return 0


def verify_release_metadata(tag: str | None = None, archive: Path | None = None) -> list[str]:
    failures: list[str] = []
    pyproject_version = _pyproject_version()
    if pyproject_version != __version__:
        failures.append(f"pyproject version {pyproject_version!r} does not match __version__ {__version__!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## {__version__} " not in changelog:
        failures.append(f"CHANGELOG.md has no heading for {__version__}")
    if tag is not None and re.search(rf"^## {re.escape(__version__)}\s+-\s+Unreleased\s*$", changelog, re.MULTILINE):
        failures.append(f"CHANGELOG.md still marks {__version__} as Unreleased")
    unreleased = re.search(r"^## Unreleased\s*(?P<body>.*?)(?=^## |\Z)", changelog, re.MULTILINE | re.DOTALL)
    if tag is not None and unreleased and re.search(r"^- ", unreleased.group("body"), re.MULTILINE):
        failures.append("CHANGELOG.md still contains unreleased changes")

    expected_tag = release_tag_for(__version__)
    if tag is not None and tag != expected_tag:
        failures.append(f"tag {tag!r} does not match version tag {expected_tag!r}")

    if archive is not None:
        failures.extend(_verify_archive(archive))
    return failures


def release_tag_for(version: str) -> str:
    match = re.fullmatch(r"(\d+\.\d+\.\d+)rc(\d+)", version)
    if match:
        return f"v{match.group(1)}-rc.{match.group(2)}"
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"unsupported release version: {version}")
    return f"v{version}"


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', text, re.MULTILINE)
    if not match:
        raise ValueError("pyproject.toml does not define project.version")
    return match.group(1)


def _verify_archive(archive: Path) -> list[str]:
    archive = archive.resolve()
    if not archive.exists():
        return [f"archive does not exist: {archive}"]
    with zipfile.ZipFile(archive) as bundle:
        files = {name for name in bundle.namelist() if not name.endswith("/")}
        content = {name: bundle.read(name) for name in files}
    expected = {f"{ARCHIVE_ROOT}/{name}" for name in REQUIRED_INCLUDE}
    failures: list[str] = []
    if files != expected:
        missing = sorted(expected - files)
        extra = sorted(files - expected)
        if missing:
            failures.append(f"archive missing files: {missing}")
        if extra:
            failures.append(f"archive contains unexpected files: {extra}")
    if any(not name.startswith(f"{ARCHIVE_ROOT}/") for name in files):
        failures.append(f"archive must contain one {ARCHIVE_ROOT}/ root directory")
    for relative_name in REQUIRED_INCLUDE:
        archive_name = f"{ARCHIVE_ROOT}/{relative_name}"
        source = ROOT / SKILL_SOURCE / relative_name
        if archive_name in content and content[archive_name] != source.read_bytes():
            failures.append(f"archive content differs from source: {archive_name}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
