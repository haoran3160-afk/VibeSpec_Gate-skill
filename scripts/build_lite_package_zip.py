from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_lite_package import REQUIRED_INCLUDE, check_package, check_source  # noqa: E402


DEFAULT_OUTPUT = ROOT / "dist" / "vibespec-gate-lite.zip"
ARCHIVE_ROOT = "vibespec-gate"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the prompt-only VibeSpec Gate Lite zip package.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Zip file to write.")
    args = parser.parse_args(argv)

    output_zip = args.output.resolve()
    staging_dir = output_zip.with_suffix("")
    build_lite_package(staging_dir, output_zip)
    print(f"PASS Lite package zip built: {output_zip}")
    return 0


def build_lite_package(staging_dir: Path, output_zip: Path) -> dict[str, object]:
    staging_dir = staging_dir.resolve()
    output_zip = output_zip.resolve()
    dist_root = (ROOT / "dist").resolve()
    if dist_root not in output_zip.parents:
        raise ValueError(f"output zip must be under {dist_root}")
    if dist_root not in staging_dir.parents and staging_dir != dist_root:
        raise ValueError(f"staging directory must be under {dist_root}")

    source_failures = check_source(ROOT)
    if source_failures:
        raise ValueError("source Lite package docs failed verification: " + "; ".join(source_failures))

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    for relative_name in REQUIRED_INCLUDE:
        source = ROOT / relative_name
        destination = staging_dir / relative_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    package_failures = check_package(staging_dir)
    if package_failures:
        raise ValueError("staged Lite package failed verification: " + "; ".join(package_failures))

    if output_zip.exists():
        output_zip.unlink()
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging_dir.rglob("*")):
            if path.is_file():
                relative_name = path.relative_to(staging_dir).as_posix()
                archive.write(path, f"{ARCHIVE_ROOT}/{relative_name}")

    return {
        "zip": str(output_zip),
        "staging_dir": str(staging_dir),
        "files": list(REQUIRED_INCLUDE),
        "archive_root": ARCHIVE_ROOT,
    }


if __name__ == "__main__":
    raise SystemExit(main())
