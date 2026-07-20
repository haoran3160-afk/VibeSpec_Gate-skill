from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/design/lite_skill_package_manifest.md")
SKILL_SOURCE = Path("skills/vibespec-gate")


def manifest_required_include(root: Path) -> tuple[str, ...]:
    manifest_path = root.resolve() / MANIFEST
    text = manifest_path.read_text(encoding="utf-8")
    match = re.search(r"^## Include\s+.*?^```text\s*\n(?P<files>.*?)^```", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"{MANIFEST.as_posix()} has no machine-readable Include block")
    files = tuple(line.strip() for line in match.group("files").splitlines() if line.strip())
    if not files or len(set(files)) != len(files):
        raise ValueError(f"{MANIFEST.as_posix()} Include block is empty or contains duplicates")
    return files


REQUIRED_INCLUDE = manifest_required_include(ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the VibeSpec Gate Skill install unit.")
    parser.add_argument("package_dir", nargs="?", type=Path, help="Optional staged package directory.")
    args = parser.parse_args(argv)

    failures = check_source(ROOT)
    if args.package_dir is not None:
        failures.extend(check_package(args.package_dir))
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("PASS VibeSpec Gate Skill source and package boundary")
    return 0


def check_source(root: Path) -> list[str]:
    root = root.resolve()
    failures: list[str] = []
    try:
        required_include = manifest_required_include(root)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    skill_dir = root / SKILL_SOURCE
    failures.extend(check_package(skill_dir, required_include))

    skill_entries = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("SKILL.md")
        if not set(path.relative_to(root).parts) & {".git", ".agents", "dist", "test output", ".pytest_cache"}
    )
    expected = [f"{SKILL_SOURCE.as_posix()}/SKILL.md"]
    if skill_entries != expected:
        failures.append(f"repository must contain exactly one authoritative SKILL.md: {skill_entries}")
    if (root / "agents/openai.yaml").exists():
        failures.append("root agents/openai.yaml must be removed after Skill migration")
    return failures


def check_package(package_dir: Path, required_include: tuple[str, ...] = REQUIRED_INCLUDE) -> list[str]:
    package_dir = package_dir.resolve()
    if not package_dir.exists():
        return [f"package directory does not exist: {package_dir}"]
    if not package_dir.is_dir():
        return [f"package path is not a directory: {package_dir}"]

    failures = _check_skill_unit(package_dir, required_include)
    files = {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    required = set(required_include)
    for missing in sorted(required - files):
        failures.append(f"package missing required file: {missing}")
    for extra in sorted(files - required):
        failures.append(f"package contains non-manifest file: {extra}")
    return failures


def _check_skill_unit(skill_dir: Path, required_include: tuple[str, ...]) -> list[str]:
    failures: list[str] = []
    for relative_name in required_include:
        if not (skill_dir / relative_name).is_file():
            failures.append(f"missing Skill runtime file: {relative_name}")
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        return failures

    skill = skill_path.read_text(encoding="utf-8")
    frontmatter_parts = skill.split("---\n", 2)
    frontmatter = frontmatter_parts[1].splitlines() if len(frontmatter_parts) == 3 else []
    if (
        len(frontmatter) != 2
        or frontmatter[0] != "name: vibespec-gate"
        or not frontmatter[1].startswith("description: ")
        or not frontmatter[1].removeprefix("description: ").strip()
    ):
        failures.append("SKILL.md frontmatter must contain only the expected name and description fields")
    for relative_name in required_include:
        if relative_name in {"SKILL.md", "LICENSE", "agents/openai.yaml"}:
            continue
        if relative_name not in skill:
            failures.append(f"SKILL.md does not route runtime resource: {relative_name}")
    for phrase in (
        "Decision: BLOCK",
        "Decision: REVIEW",
        "Decision: PASS_WITH_WARNINGS",
        "Decision: PASS",
        "Do not replace the token with synonyms",
        "list all seven review surfaces",
    ):
        if phrase not in skill:
            failures.append(f"SKILL.md missing chat output contract: {phrase}")
    template_destinations = {
        "assets/templates/launch-decision.md": "launch_decision.md",
        "assets/templates/top-security-risks.md": "top_security_risks.md",
        "assets/templates/agent-fix-plan.md": "agent_fix_plan.md",
        "assets/templates/retest-checklist.md": "retest_checklist.md",
    }
    for source, destination in template_destinations.items():
        if f"`{source}` -> `{destination}`" not in skill:
            failures.append(f"SKILL.md does not map {source} to {destination}")

    metadata = _read(skill_dir / "agents/openai.yaml")
    for phrase in (
        'display_name: "VibeSpec Gate"',
        'default_prompt: "Use $vibespec-gate',
        "allow_implicit_invocation: false",
    ):
        if phrase not in metadata:
            failures.append(f"agents/openai.yaml missing policy or interface field: {phrase}")

    protocol = _read(skill_dir / "references/review-protocol.md")
    for phrase in ("BLOCK", "REVIEW", "PASS_WITH_WARNINGS", "PASS", "human confirmation", "read-only"):
        if phrase.lower() not in protocol.lower():
            failures.append(f"review-protocol.md missing contract term: {phrase}")

    coverage = _read(skill_dir / "references/evidence-coverage.md")
    for phrase in (
        "complete",
        "partial",
        "insufficient",
        "truncated",
        "auth",
        "authorization",
        "secrets",
        "data_rules",
        "deployment",
        "agent_tools",
        "desktop_ipc",
    ):
        if phrase not in coverage:
            failures.append(f"evidence-coverage.md missing coverage term: {phrase}")

    template_terms = {
        "assets/templates/launch-decision.md": ("Decision", "Coverage status", "Missing evidence", "Safety Boundary"),
        "assets/templates/top-security-risks.md": ("Severity", "Evidence", "Launch impact", "Human confirmation"),
        "assets/templates/agent-fix-plan.md": ("Human Confirmation Gate", "Allowed change scope", "Prohibited changes", "Verification"),
        "assets/templates/retest-checklist.md": ("Coverage", "Commands Or Checks", "Expected Result"),
    }
    for relative_name, phrases in template_terms.items():
        text = _read(skill_dir / relative_name)
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"{relative_name} missing template field: {phrase}")
    return failures


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if __name__ == "__main__":
    raise SystemExit(main())
