from __future__ import annotations

from pathlib import Path

from vibesec.core.fix_prompt_builder import build_fix_prompt
from vibesec.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


class ConfigScanner(BaseScanner):
    name = "config_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            for line_no, line in enumerate(read_lines(path), start=1):
                lowered = line.lower()
                if "debug" in lowered and ("true" in lowered or "1" == lowered.strip().split("=")[-1]):
                    findings.append(self._debug_finding(root, path, line_no, index))
                    index += 1
                if "productionbrowserSourcemaps".lower() in lowered and "true" in lowered:
                    findings.append(self._sourcemap_finding(root, path, line_no, index))
                    index += 1
                if has_any(line, ["console.log", "logger.debug"]) and has_any(line, ["token", "password", "secret", "authorization"]):
                    findings.append(self._sensitive_log(root, path, line_no, index))
                    index += 1
        return findings

    def _debug_finding(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "Debug mode appears enabled"
        beginner = "调试模式可能把错误细节、路径或内部配置暴露给用户。生产环境应关闭。"
        fix = "确认生产环境关闭 debug/verbose 模式，并把详细错误写入受控日志。"
        return Finding(
            id=next_id("CFG", index),
            title=title,
            severity="P2",
            category="Config",
            affected_files=[location],
            evidence=f"{location} contains debug-like enabled setting.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Verbose debug output can leak implementation details and sensitive context.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加生产配置测试或文档检查"]),
            verification_steps=["确认生产配置中 debug=false。"],
            false_positive_notes="开发环境配置可能合理；生产配置需单独确认。",
            references=["https://owasp.org/Top10/2025/en/"],
        )

    def _sourcemap_finding(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "Production browser source maps appear enabled"
        beginner = "公开 source map 会让别人更容易阅读你的前端源码和内部路径。"
        fix = "公开上线前确认 source map 暴露符合预期；敏感应用应关闭或限制访问。"
        return Finding(
            id=next_id("CFG", index),
            title=title,
            severity="P2",
            category="Deployment",
            affected_files=[location],
            evidence=f"{location} enables production browser source maps.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Source maps can expose source structure and make reverse engineering easier.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["检查构建产物是否仍暴露 .map 文件"]),
            verification_steps=["重新构建并确认生产环境不公开不必要的 source map。"],
            false_positive_notes="有些团队会有意发布 source maps 到受控错误追踪系统。",
            references=["https://nextjs.org/docs/app/api-reference/config/next-config-js/headers"],
        )

    def _sensitive_log(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "Possible sensitive value written to logs"
        beginner = "日志常被很多人和系统读取。如果 token 或密码进入日志，泄露范围会扩大。"
        fix = "删除敏感字段日志，改为记录请求 ID、用户 ID 的脱敏形式和错误类别。"
        return Finding(
            id=next_id("CFG", index),
            title=title,
            severity="P1",
            category="Privacy",
            affected_files=[location],
            evidence=f"{location} logs a line containing sensitive keywords.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Sensitive logs can expose credentials or personal data outside normal access controls.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加日志脱敏测试或静态检查"]),
            verification_steps=["重新扫描确认敏感日志 finding 消失。"],
            false_positive_notes="如果日志值已严格脱敏，可降级为 P3 并保留说明。",
            references=["https://owasp.org/www-project-application-security-verification-standard/"],
        )
