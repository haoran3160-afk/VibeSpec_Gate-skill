from __future__ import annotations

import os
import re
from pathlib import Path


def require_disjoint_paths(
    first: str | Path,
    second: str | Path,
    *,
    first_label: str = "input",
    second_label: str = "output",
) -> tuple[Path, Path]:
    first_path = _canonical_path(first)
    second_path = _canonical_path(second)
    names_overlap = first_path == second_path or first_path in second_path.parents or second_path in first_path.parents
    identities_overlap = bool(_file_identities(first_path) & _file_identities(second_path))
    if names_overlap or identities_overlap:
        raise ValueError(
            f"{first_label} and {second_label} paths must not overlap: "
            f"{first_path} and {second_path}"
        )
    return first_path, second_path


def _canonical_path(value: str | Path) -> Path:
    raw = str(value)
    lowered = raw.lower()
    if lowered.startswith("\\\\?\\unc\\"):
        raw = "\\\\" + raw[8:]
    elif lowered.startswith(("\\\\?\\", "\\\\.\\")):
        candidate = raw[4:]
        if not re.match(r"^[a-zA-Z]:[\\/]", candidate):
            raise ValueError(f"unsupported Windows device path: {value}")
        raw = candidate
    return Path(raw).resolve()


def _file_identities(path: Path) -> set[tuple[int, int]]:
    try:
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = [Path(root) / name for root, _, names in os.walk(path, onerror=_raise_walk_error) for name in names]
        else:
            return set()
        identities = set()
        for candidate in candidates:
            stat_result = candidate.stat()
            if stat_result.st_ino:
                identities.add((stat_result.st_dev, stat_result.st_ino))
        return identities
    except OSError as exc:
        raise ValueError(f"cannot verify path identity for {path}: {exc}") from exc


def _raise_walk_error(exc: OSError) -> None:
    raise exc
