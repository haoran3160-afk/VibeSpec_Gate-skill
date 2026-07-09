from __future__ import annotations

from pathlib import Path

from vibespec_gate.core.risk_model import Finding, ProjectProfile

from .base import ToolAdapter


class TrivyAdapter(ToolAdapter):
    name = "trivy"
    executable = "trivy"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        if self.is_available():
            return [
                Finding(
                    id="VSG-TRIVY-INFO",
                    title="Trivy is installed but not auto-run in MVP",
                    severity="Info",
                    category="Dependency",
                    affected_files=[str(root)],
                    evidence="Adapter detected `trivy`; run it explicitly for full filesystem/container/IaC coverage.",
                    why_it_matters_for_beginner="Trivy 可以补充依赖、容器和配置扫描，但 MVP 不会自动执行可能下载数据库的操作。",
                    technical_reason="Avoids surprising network and cache behavior by default.",
                    recommended_fix="Run `trivy fs <project>` when you want full Trivy output, then review with VibeSpec.",
                    codex_fix_prompt="No code fix required.",
                    verification_steps=["Run `trivy --version`."],
                    false_positive_notes="Informational only.",
                    references=["https://github.com/aquasecurity/trivy"],
                )
            ]
        return [
            Finding(
                id="VSG-TRIVY-000",
                title="Trivy not installed; dependency/container checks are limited",
                severity="Info",
                category="Dependency",
                affected_files=[str(root)],
                evidence="`trivy` executable was not found on PATH.",
                why_it_matters_for_beginner="没有 Trivy 时，MVP 仍会做基础依赖检查，但不会覆盖完整漏洞库和容器配置。",
                technical_reason="External adapter gracefully degraded.",
                recommended_fix="Optionally install Trivy locally for deeper scans.",
                codex_fix_prompt="No code fix required; optional tool installation.",
                verification_steps=["Run `trivy --version` if installed."],
                false_positive_notes="Informational only.",
                references=["https://github.com/aquasecurity/trivy"],
            )
        ]
