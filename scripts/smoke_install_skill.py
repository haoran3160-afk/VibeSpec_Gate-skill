from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_lite_package import REQUIRED_INCLUDE, SKILL_SOURCE, check_package  # noqa: E402


ARCHIVE_ROOT = "vibespec-gate"


def smoke_install(temporary_home: Path, skills_root: str = ".agents/skills") -> Path:
    source = ROOT / SKILL_SOURCE
    target = temporary_home.resolve() / Path(skills_root) / "vibespec-gate"
    if target.exists():
        raise ValueError(f"refusing to overwrite existing smoke target: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    failures = check_package(target)
    if failures:
        raise ValueError("installed Skill failed verification: " + "; ".join(failures))
    installed = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    }
    if installed != set(REQUIRED_INCLUDE):
        raise ValueError(f"installed file set differs from manifest: {sorted(installed)}")
    return target


def smoke_install_archive(archive: Path, temporary_home: Path, skills_root: str = ".codex/skills") -> Path:
    target_root = temporary_home.resolve() / Path(skills_root)
    target = target_root / ARCHIVE_ROOT
    if target.exists():
        raise ValueError(f"refusing to overwrite existing smoke target: {target}")
    expected = {f"{ARCHIVE_ROOT}/{name}" for name in REQUIRED_INCLUDE}
    with zipfile.ZipFile(archive.resolve()) as bundle:
        files = {name for name in bundle.namelist() if not name.endswith("/")}
        if files != expected:
            raise ValueError("release archive file set differs from the Skill manifest")
        target_root.mkdir(parents=True, exist_ok=True)
        bundle.extractall(target_root)
    failures = check_package(target)
    if failures:
        raise ValueError("archive-installed Skill failed verification: " + "; ".join(failures))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-install the VibeSpec Gate Skill.")
    parser.add_argument("--archive", type=Path, help="Install and verify a built release ZIP instead of source files.")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="vibespec-gate-install-") as temporary:
        home = Path(temporary)
        if args.archive:
            targets = [smoke_install_archive(args.archive, home)]
        else:
            targets = [smoke_install(home, root) for root in (".codex/skills", ".agents/skills")]
        print("PASS Skill install smoke: " + ", ".join(str(target) for target in targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
