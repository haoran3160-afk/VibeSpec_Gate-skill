from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/design/lite_skill_package_manifest.md")
REQUIRED_INCLUDE = (
    "LICENSE",
    "SKILL.md",
    "README.md",
    "README.zh-CN.md",
    "agents/openai.yaml",
    "docs/usage/lite_quickstart.md",
    "examples/lite_review_prompt.md",
    "examples/synthetic_review_example.md",
)
OPTIONAL_INCLUDE = (
    "docs/usage/agent_review_cookbook.md",
    "docs/usage/examples.md",
    "docs/usage/quickstart.md",
)
EXCLUDE_PATTERNS = (
    "test output/**",
    "tests/**",
    "scripts/*phase*",
    "scripts/*matrix*",
    "scripts/*score*",
    "scripts/*calibration*",
    "scripts/verify_release.py",
    "docs/design/*phase*",
    "docs/usage/*quality*",
    "docs/usage/*contract*",
    "docs/maintainers/**",
    "tests/evaluation_cases/**",
)
OUTPUT_NAMES = (
    "launch_decision.md",
    "top_security_risks.md",
    "agent_fix_plan.md",
    "retest_checklist.md",
)
DECISION_NAMES = ("BLOCK", "REVIEW", "PASS_WITH_WARNINGS", "PASS")
USER_DOC_INCLUDE = tuple(path for path in REQUIRED_INCLUDE if path.endswith(".md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Lite Skill package manifest boundaries.")
    parser.add_argument(
        "package_dir",
        nargs="?",
        type=Path,
        help="Optional candidate Lite package directory to check against the manifest.",
    )
    args = parser.parse_args(argv)

    failures = check_source(ROOT)
    if args.package_dir is not None:
        failures.extend(check_package(args.package_dir))

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    if args.package_dir is not None:
        print(f"PASS source docs and package boundary: {args.package_dir}")
    else:
        print("PASS source Lite package docs")
    return 0


def check_source(root: Path) -> list[str]:
    failures: list[str] = []
    if not (root / MANIFEST).exists():
        failures.append(f"missing {MANIFEST.as_posix()}")
    failures.extend(_check_user_docs(root, USER_DOC_INCLUDE))
    failures.extend(_check_prompt_only_default(root))
    failures.extend(_check_safety_boundary(root))
    failures.extend(_check_install_contract(root))
    failures.extend(_check_translation_parity(root))
    failures.extend(_check_sensitive_evidence_boundary(root))
    failures.extend(_check_agent_metadata(root))
    failures.extend(_check_local_links(root, USER_DOC_INCLUDE))
    return failures


def check_package(package_dir: Path) -> list[str]:
    package_dir = package_dir.resolve()
    failures: list[str] = []
    if not package_dir.exists():
        return [f"package directory does not exist: {package_dir}"]
    if not package_dir.is_dir():
        return [f"package path is not a directory: {package_dir}"]

    files = _package_files(package_dir)
    for required in REQUIRED_INCLUDE:
        if required not in files:
            failures.append(f"package missing required file: {required}")

    allowed = set(REQUIRED_INCLUDE) | set(OPTIONAL_INCLUDE)
    for file_path in files:
        if file_path not in allowed:
            failures.append(f"package contains non-manifest file: {file_path}")
        for pattern in EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern):
                failures.append(f"package contains excluded file: {file_path} matches {pattern}")

    present_docs = [path for path in USER_DOC_INCLUDE + OPTIONAL_INCLUDE if path in files]
    failures.extend(_check_user_docs(package_dir, present_docs))
    failures.extend(_check_prompt_only_default(package_dir))
    failures.extend(_check_safety_boundary(package_dir))
    failures.extend(_check_install_contract(package_dir))
    failures.extend(_check_translation_parity(package_dir))
    failures.extend(_check_sensitive_evidence_boundary(package_dir))
    failures.extend(_check_agent_metadata(package_dir))
    failures.extend(_check_local_links(package_dir, present_docs))
    return failures


def _check_user_docs(root: Path, docs: tuple[str, ...] | list[str]) -> list[str]:
    failures: list[str] = []
    for doc in docs:
        path = root / doc
        if not path.exists():
            failures.append(f"missing user-facing file: {doc}")
            continue
        text = path.read_text(encoding="utf-8")
        for output_name in OUTPUT_NAMES:
            if output_name not in text:
                failures.append(f"{doc} missing output name {output_name}")
        for decision in DECISION_NAMES:
            if decision not in text:
                failures.append(f"{doc} missing decision name {decision}")
    return failures


def _check_prompt_only_default(root: Path) -> list[str]:
    failures: list[str] = []
    readme = _read_lower(root / "README.md")
    quickstart = _read_lower(root / "docs/usage/lite_quickstart.md")
    skill = _read_lower(root / "SKILL.md")
    prompt = _read_lower(root / "examples/lite_review_prompt.md")

    required_phrases = {
        "README.md": (readme, ("default lite package", "prompt-only", "optional core-powered")),
        "docs/usage/lite_quickstart.md": (quickstart, ("agent-native flow", "prompt-only", "optional repository cli flow")),
        "SKILL.md": (skill, ("default package mode", "prompt-only", "optional core-powered")),
        "examples/lite_review_prompt.md": (prompt, ("prompt-only", "optional repository overlay")),
    }
    for doc, (text, phrases) in required_phrases.items():
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"{doc} missing prompt-only package phrase: {phrase}")

    first_readme = _before_any(
        readme,
        ("## optional core-powered path", "## optional core-powered cli", "## 可选 core-powered 路径", "## source checkout commands"),
    )
    first_quickstart = _before_any(quickstart, ("## optional repository cli flow", "## optional existing review output input"))
    for doc, text in (("README.md", first_readme), ("docs/usage/lite_quickstart.md", first_quickstart)):
        if "py -3 -m vibespec_gate.cli" in text or "$env:pythonpath" in text:
            failures.append(f"{doc} presents CLI command before the prompt-only default path")
    return failures


def _check_safety_boundary(root: Path) -> list[str]:
    failures: list[str] = []
    checks = {
        "README.md": _read_lower(root / "README.md"),
        "docs/usage/lite_quickstart.md": _read_lower(root / "docs/usage/lite_quickstart.md"),
    }
    for doc, text in checks.items():
        if "professional security certification" not in text:
            failures.append(f"{doc} missing professional certification disclaimer")
        if "human confirmation" not in text:
            failures.append(f"{doc} missing human confirmation boundary")
    return failures


def _check_install_contract(root: Path) -> list[str]:
    failures: list[str] = []
    checks = {
        "README.md": _read_lower(root / "README.md"),
        "docs/usage/lite_quickstart.md": _read_lower(root / "docs/usage/lite_quickstart.md"),
    }
    for doc, text in checks.items():
        normalized_text = " ".join(text.split())
        required = (
            "vibespec-gate\\skill.md",
            "macos or linux",
            "windows powershell",
            "build_lite_package_zip.py",
            "codex_home",
            "without reading a project",
            "outside the reviewed project",
            "py -3 -c",
            "python3 -c",
        )
        for phrase in required:
            if phrase not in normalized_text:
                failures.append(f"{doc} missing install contract phrase: {phrase}")
    return failures


def _check_translation_parity(root: Path) -> list[str]:
    english = _section_markers(root / "README.md")
    chinese = _section_markers(root / "README.zh-CN.md")
    if not english:
        return ["README.md has no translation section markers"]
    if english != chinese:
        return [f"README section markers differ: English={english}, Chinese={chinese}"]
    return []


def _check_sensitive_evidence_boundary(root: Path) -> list[str]:
    failures: list[str] = []
    checks = {
        "README.md": (_read_lower(root / "README.md"), ("synthetic", "manual", "sharing")),
        "docs/usage/lite_quickstart.md": (
            _read_lower(root / "docs/usage/lite_quickstart.md"),
            ("manual", "sharing", "redacted"),
        ),
        "examples/synthetic_review_example.md": (
            _read_lower(root / "examples/synthetic_review_example.md"),
            ("synthetic", "manually", "sharing"),
        ),
    }
    for doc, (text, required) in checks.items():
        for phrase in required:
            if phrase not in text:
                failures.append(f"{doc} missing sensitive-evidence phrase: {phrase}")
    return failures


def _check_agent_metadata(root: Path) -> list[str]:
    path = root / "agents/openai.yaml"
    if not path.exists():
        return ["missing agents/openai.yaml"]
    text = path.read_text(encoding="utf-8")
    failures = []
    for phrase in ('display_name: "VibeSpec Gate"', 'short_description:', 'default_prompt: "Use $vibespec-gate'):
        if phrase not in text:
            failures.append(f"agents/openai.yaml missing metadata: {phrase}")
    return failures


def _check_local_links(root: Path, docs: tuple[str, ...] | list[str]) -> list[str]:
    failures: list[str] = []
    for doc in docs:
        path = root / doc
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            relative_target = target.split("#", 1)[0]
            if relative_target and not (path.parent / relative_target).exists():
                failures.append(f"{doc} has broken local link: {target}")
    return failures


def _package_files(package_dir: Path) -> set[str]:
    return {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file()
    }


def _read_lower(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lower()


def _section_markers(path: Path) -> list[str]:
    if not path.exists():
        return []
    return re.findall(r"<!-- section:([a-z0-9-]+) -->", path.read_text(encoding="utf-8"))


def _before_any(text: str, markers: tuple[str, ...]) -> str:
    positions = [text.find(marker) for marker in markers if marker in text]
    if not positions:
        return text
    return text[: min(positions)]


if __name__ == "__main__":
    raise SystemExit(main())
