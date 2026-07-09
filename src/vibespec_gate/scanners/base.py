from __future__ import annotations

import re
from pathlib import Path

from vibespec_gate.core.source_classifier import should_ignore_path
from vibespec_gate.core.risk_model import Finding, ProjectProfile


TEXT_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".env",
    ".sql",
    ".rules",
    ".mjs",
    ".cjs",
}


class BaseScanner:
    name = "base"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        raise NotImplementedError


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if should_ignore_path(path):
            continue
        if not path.is_file():
            continue
        if path.suffix in TEXT_EXTENSIONS or path.name.startswith(".env") or path.name in {"Dockerfile", "Procfile"}:
            files.append(path)
    return sorted(files)


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def rel(path: Path, root: Path, line: int | None = None) -> str:
    value = path.relative_to(root).as_posix()
    if line:
        return f"{value}:{line}"
    return value


def mask_secret(value: str) -> str:
    compact = value.strip()
    if len(compact) <= 8:
        return "***"
    return f"{compact[:4]}...{compact[-4:]}"


def looks_like_frontend(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return bool(parts & {"public", "pages", "app", "components", "src"}) and not bool(parts & {"server", "api", "routes"})


def has_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def next_id(prefix: str, index: int) -> str:
    return f"VSG-{prefix}-{index:03d}"


SECRET_VALUE_RE = re.compile(r"([A-Za-z0-9_\-]{16,})")
