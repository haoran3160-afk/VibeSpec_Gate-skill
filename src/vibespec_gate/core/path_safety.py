from __future__ import annotations

from pathlib import Path


def require_disjoint_paths(
    first: str | Path,
    second: str | Path,
    *,
    first_label: str = "input",
    second_label: str = "output",
) -> tuple[Path, Path]:
    first_path = Path(first).resolve()
    second_path = Path(second).resolve()
    if first_path == second_path or first_path in second_path.parents or second_path in first_path.parents:
        raise ValueError(
            f"{first_label} and {second_label} paths must not overlap: "
            f"{first_path} and {second_path}"
        )
    return first_path, second_path
