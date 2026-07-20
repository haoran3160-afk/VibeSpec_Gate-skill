from __future__ import annotations

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
    if first_path == second_path or first_path in second_path.parents or second_path in first_path.parents:
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
