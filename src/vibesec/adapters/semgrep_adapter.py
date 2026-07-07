from __future__ import annotations

from pathlib import Path

from vibesec.core.risk_model import Finding, ProjectProfile

from .base import ToolAdapter


class SemgrepAdapter(ToolAdapter):
    name = "semgrep"
    executable = "semgrep"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        if self.is_available():
            status = "Semgrep is installed but not auto-run in MVP"
            evidence = "Adapter detected `semgrep`; configure rules before running deeper SAST."
        else:
            status = "Semgrep not installed; SAST checks use built-in heuristics only"
            evidence = "`semgrep` executable was not found on PATH."
        return [
            Finding(
                id="VSG-SEMGREP-000",
                title=status,
                severity="Info",
                category="Config",
                affected_files=[str(root)],
                evidence=evidence,
                why_it_matters_for_beginner="Semgrep 可以发现更多代码级问题，但需要合适规则集来控制噪音。",
                technical_reason="Adapter status only; no external scan was required for MVP.",
                recommended_fix="Optionally run Semgrep with vetted rules and feed results into a future VibeSec import.",
                codex_fix_prompt="No code fix required.",
                verification_steps=["Run `semgrep --version` if installed."],
                false_positive_notes="Informational only.",
                references=["https://github.com/semgrep/semgrep"],
            )
        ]
