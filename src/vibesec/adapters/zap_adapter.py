from __future__ import annotations

from pathlib import Path

from vibesec.core.risk_model import Finding, ProjectProfile

from .base import ToolAdapter


class ZapAdapter(ToolAdapter):
    name = "zap"
    executable = "zap.sh"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        return [
            Finding(
                id="VSG-ZAP-000",
                title="OWASP ZAP dynamic scanning is disabled by default",
                severity="Info",
                category="Deployment",
                affected_files=[str(root)],
                evidence="No URL target was scanned. Dynamic scanning requires explicit authorization and scope.",
                why_it_matters_for_beginner="动态扫描会访问运行中的网站，必须确认这是你拥有或被授权的环境。",
                technical_reason="Prevents unauthorized or destructive active scanning.",
                recommended_fix="If needed, run a separate authorized ZAP baseline/passive scan against local or staging only.",
                codex_fix_prompt="No code fix required.",
                verification_steps=["Document authorization before any dynamic scan."],
                false_positive_notes="Informational safety boundary.",
                references=["https://github.com/zaproxy/zaproxy"],
            )
        ]
