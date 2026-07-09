from __future__ import annotations

from pathlib import Path

from vibespec_gate.core.risk_model import Finding, ProjectProfile
from vibespec_gate.scanners.base import next_id

from .base import ToolAdapter


class GitleaksAdapter(ToolAdapter):
    name = "gitleaks"
    executable = "gitleaks"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        if not self.is_available():
            return [self._missing(root)]
        try:
            data = self.run_json(["gitleaks", "detect", "--source", str(root), "--no-git", "--report-format", "json", "--redact"])
        except Exception as exc:
            return [self._error(root, exc)]
        findings: list[Finding] = []
        for idx, item in enumerate(data or [], start=1):
            file = item.get("File", "unknown")
            line = item.get("StartLine", "")
            location = f"{file}:{line}" if line else file
            findings.append(
                Finding(
                    id=next_id("GL", idx),
                    title="Gitleaks detected a possible secret",
                    severity="P1",
                    category="Secrets",
                    affected_files=[location],
                    evidence=f"Gitleaks rule {item.get('RuleID', 'unknown')} at {location}; secret redacted.",
                    why_it_matters_for_beginner="专业密钥扫描器发现了疑似凭证，真实值可能已经暴露。",
                    technical_reason="Gitleaks matched a known secret detector pattern.",
                    recommended_fix="确认并轮换真实密钥，从代码和历史中移除，并改用环境变量。",
                    codex_fix_prompt="Use VibeSpec report context to remove the secret and add a prevention check.",
                    verification_steps=["重新运行 Gitleaks 和 VibeSpec Gate。"],
                    false_positive_notes="Gitleaks 也可能命中测试假值；真实密钥必须轮换。",
                    references=["https://github.com/gitleaks/gitleaks"],
                )
            )
        return findings

    def _missing(self, root: Path) -> Finding:
        return Finding(
            id="VSG-GL-000",
            title="Gitleaks not installed; using built-in secret fallback only",
            severity="Info",
            category="Secrets",
            affected_files=[str(root)],
            evidence="`gitleaks` executable was not found on PATH.",
            why_it_matters_for_beginner="内置规则能兜底，但专业密钥扫描器覆盖更全，尤其是 Git 历史。",
            technical_reason="External adapter gracefully degraded.",
            recommended_fix="Install Gitleaks locally if you need deeper secret scanning.",
            codex_fix_prompt="No code fix required; optional tool installation.",
            verification_steps=["Run `gitleaks version` if installed."],
            false_positive_notes="This is an informational adapter status, not a vulnerability.",
            references=["https://gitleaks.io/"],
        )

    def _error(self, root: Path, exc: Exception) -> Finding:
        finding = self._missing(root)
        finding.title = "Gitleaks adapter failed and was skipped"
        finding.evidence = str(exc)
        return finding
