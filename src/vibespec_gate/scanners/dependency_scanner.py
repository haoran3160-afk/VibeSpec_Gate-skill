from __future__ import annotations

import json
import re
from pathlib import Path

from vibespec_gate.core.fix_prompt_builder import build_fix_prompt
from vibespec_gate.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, next_id, rel


KNOWN_NODE_RISKS = {
    "lodash": ("4.17.20", "P1", "Known vulnerable lodash version in fixture knowledge base."),
    "minimist": ("1.2.5", "P1", "Known vulnerable minimist version in fixture knowledge base."),
    "next": ("12.", "P2", "Older Next.js major version; review current advisories and upgrade path."),
}

KNOWN_PYTHON_RISKS = {
    "django": ("2.", "P1", "Very old Django major version; likely missing security fixes."),
    "flask": ("0.", "P1", "Very old Flask major version; likely missing security fixes."),
}


class DependencyScanner(BaseScanner):
    name = "dependency_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        findings: list[Finding] = []
        index = 1
        package_json = root / "package.json"
        if package_json.exists():
            package_findings, has_dependencies = self._scan_package_json(root, package_json, index)
            findings.extend(package_findings)
            index += len(findings) + 1
            if has_dependencies and not any((root / name).exists() for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")):
                findings.append(self._missing_lockfile(root, package_json, index))
                index += 1
        reqs = root / "requirements.txt"
        if reqs.exists():
            findings.extend(self._scan_requirements(root, reqs, index))
        return findings

    def _scan_package_json(self, root: Path, path: Path, start: int) -> tuple[list[Finding], bool]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return [], False
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        findings: list[Finding] = []
        index = start
        for name, version in deps.items():
            rule = KNOWN_NODE_RISKS.get(name)
            if not rule:
                continue
            marker, severity, reason = rule
            if marker in str(version):
                findings.append(self._dep_finding(root, path, index, name, version, severity, reason))
                index += 1
        return findings, bool(deps)

    def _scan_requirements(self, root: Path, path: Path, start: int) -> list[Finding]:
        findings: list[Finding] = []
        index = start
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            match = re.match(r"([A-Za-z0-9_.-]+)==([^\\s]+)", line.strip())
            if not match:
                continue
            name = match.group(1).lower()
            version = match.group(2)
            rule = KNOWN_PYTHON_RISKS.get(name)
            if rule and version.startswith(rule[0]):
                findings.append(self._dep_finding(root, path, index, name, version, rule[1], rule[2], line_no))
                index += 1
        return findings

    def _dep_finding(
        self, root: Path, path: Path, index: int, name: str, version: str, severity: str, reason: str, line_no: int | None = None
    ) -> Finding:
        location = rel(path, root, line_no)
        title = f"Review vulnerable or outdated dependency: {name}"
        beginner = f"项目使用了需要复查的依赖 {name}@{version}。旧依赖可能包含公开漏洞。"
        fix = "运行对应生态的 audit 工具，升级到安全版本，并重新执行测试。不要直接删除依赖来掩盖问题。"
        return Finding(
            id=next_id("DEP", index),
            title=title,
            severity=severity,
            category="Dependency",
            affected_files=[location],
            evidence=f"{location} declares {name}@{version}. {reason}",
            why_it_matters_for_beginner=beginner,
            technical_reason=reason,
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["运行 npm/pnpm/pip audit 或项目测试"]),
            verification_steps=["运行依赖审计工具。", "重新扫描并确认该依赖 finding 消失或降级。"],
            false_positive_notes="静态内置表不是完整漏洞数据库；以 npm audit、pnpm audit、pip-audit、Trivy 或 Snyk 结果为准。",
            references=["https://docs.npmjs.com/cli/v9/commands/npm-audit", "https://github.com/pypa/pip-audit"],
        )

    def _missing_lockfile(self, root: Path, path: Path, index: int) -> Finding:
        title = "Node project has no lockfile"
        beginner = "没有 lockfile 时，不同机器可能安装到不同版本，安全审计和复现会更困难。"
        fix = "使用当前包管理器生成并提交 lockfile，然后运行依赖审计。"
        return Finding(
            id=next_id("DEP", index),
            title=title,
            severity="P2",
            category="Dependency",
            affected_files=[rel(path, root)],
            evidence="package.json exists but no package-lock.json, pnpm-lock.yaml, or yarn.lock was found.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Lockfiles improve dependency reproducibility and vulnerability triage.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [rel(path, root)], fix, ["确认 lockfile 被提交"]),
            verification_steps=["重新扫描确认 lockfile 存在。"],
            false_positive_notes="某些库项目故意不提交 lockfile，但上线应用通常应该提交。",
            references=["https://socket.dev/glossary/supply-chain-security"],
        )
