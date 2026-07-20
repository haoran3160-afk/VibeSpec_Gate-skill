from __future__ import annotations

from pathlib import Path
import re


SCANNABLE_TEXT_EXTENSIONS = {
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
UNSUPPORTED_SECURITY_SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".clj",
    ".cljs",
    ".cmd",
    ".cpp",
    ".cs",
    ".dart",
    ".ex",
    ".exs",
    ".erl",
    ".fs",
    ".fsx",
    ".go",
    ".groovy",
    ".h",
    ".hcl",
    ".hpp",
    ".html",
    ".java",
    ".kt",
    ".kts",
    ".php",
    ".pl",
    ".ps1",
    ".psm1",
    ".rb",
    ".r",
    ".rs",
    ".scala",
    ".sh",
    ".sol",
    ".svelte",
    ".swift",
    ".tf",
    ".vue",
}
SCANNABLE_SPECIAL_NAMES = {"Dockerfile", "Procfile"}


GENERATED_SUFFIXES = (".min.js", ".map")
TEST_SUFFIXES = (
    ".test.js",
    ".test.jsx",
    ".test.ts",
    ".test.tsx",
    ".spec.js",
    ".spec.jsx",
    ".spec.ts",
    ".spec.tsx",
    ".test.py",
    ".spec.py",
)
DOC_SUFFIXES = (".md", ".mdx", ".rst")
EXAMPLE_SUFFIXES = (".example", ".sample")
GENERATED_DIRS = {
    ".next",
    "dist",
    "dist-electron",
    "build",
    "out",
    "target",
    "coverage",
    "release",
    "artifacts",
    "captures",
    "recording-review",
    "reference-capture",
    "reference-capture-long",
    "reference-capture-ui",
    "reference-current-final",
}
VENDOR_DIRS = {
    "node_modules",
    "vendor",
    ".vscode-test",
    ".git",
    ".venv",
    "venv",
}
CACHE_DIRS = {
    ".cache",
    ".pytest_cache",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
}
IGNORED_DIRS = GENERATED_DIRS | VENDOR_DIRS | CACHE_DIRS | {".worktrees", "file_manager_e2e_sandbox"}
IGNORED_FILES = {"vibespec_gate.suppressions.json", ".vibespecignore"}


def source_type_for_path(path: str | Path) -> str:
    text = _strip_line_suffix(str(path)).replace("\\", "/")
    lowered = text.lower()
    parts = [part.lower() for part in lowered.split("/") if part]
    name = parts[-1] if parts else lowered

    if any(part in VENDOR_DIRS for part in parts):
        return "vendor"
    if any(part in CACHE_DIRS for part in parts):
        return "cache"
    if any(part in GENERATED_DIRS for part in parts) or lowered.endswith(GENERATED_SUFFIXES):
        return "generated"
    if ".worktrees" in parts or "file_manager_e2e_sandbox" in parts:
        return "generated"
    if name.endswith(TEST_SUFFIXES):
        return "test"
    if any(part in {"test", "tests", "__tests__", "spec", "specs"} for part in parts):
        return "test"
    if any(part in {"docs", "doc", "examples", "example", "samples", "sample"} for part in parts):
        return "docs" if "docs" in parts or "doc" in parts else "example"
    if name in {".env.example", ".env.sample"} or name.endswith(EXAMPLE_SUFFIXES):
        return "example"
    if lowered.endswith(DOC_SUFFIXES):
        return "docs"
    return "runtime"


def should_ignore_path(path: Path) -> bool:
    name = path.name.lower()
    if name in IGNORED_FILES:
        return True
    if name.endswith(GENERATED_SUFFIXES):
        return True
    return any(part.lower() in IGNORED_DIRS for part in path.parts)


def is_scannable_text_path(path: Path) -> bool:
    return (
        path.suffix.lower() in SCANNABLE_TEXT_EXTENSIONS
        or path.name.startswith(".env")
        or path.name in SCANNABLE_SPECIAL_NAMES
    )


def is_unsupported_security_source(path: Path) -> bool:
    return path.suffix.lower() in UNSUPPORTED_SECURITY_SOURCE_EXTENSIONS


def _strip_line_suffix(path: str) -> str:
    return re.sub(r":\d+(?::\d+)?$", "", path)
