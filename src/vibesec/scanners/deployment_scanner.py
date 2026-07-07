from __future__ import annotations

from pathlib import Path

from vibesec.core.fix_prompt_builder import build_fix_prompt
from vibesec.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


SECURITY_HEADERS = ["content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy"]


class DeploymentScanner(BaseScanner):
    name = "deployment_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            for line_no, line in enumerate(read_lines(path), start=1):
                lowered = line.lower().replace(" ", "")
                rel_path = rel(path, root)
                if rel_path.startswith("public/") and "api" not in rel_path.lower():
                    continue
                if "access-control-allow-origin" in lowered and ("*" in lowered or "'*'" in lowered or '"*"' in lowered):
                    findings.append(self._wildcard_cors(root, path, line_no, index))
                    index += 1
                if "cors(" in lowered and ("origin:'*'" in lowered or "origin:\"*\"" in lowered):
                    findings.append(self._wildcard_cors(root, path, line_no, index))
                    index += 1
                if "setcookie" in lowered or "cookies.set" in lowered:
                    if not has_any(lowered, ["httponly", "secure", "samesite"]):
                        findings.append(self._weak_cookie(root, path, line_no, index))
                        index += 1
        if "Next.js" in profile.technologies:
            next_config = next((root / name for name in ("next.config.js", "next.config.mjs") if (root / name).exists()), None)
            if next_config and not has_any(next_config.read_text(encoding="utf-8", errors="replace").lower(), SECURITY_HEADERS):
                findings.append(self._missing_headers(root, next_config, index))
        return findings

    def _wildcard_cors(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "CORS appears overly broad"
        beginner = "CORS 过宽可能让不该访问你 API 的网页也能从浏览器调用接口。"
        fix = "只允许可信域名；对带 cookie 或用户数据的 API 禁止 `*`。"
        return Finding(
            id=next_id("DEPLOY", index),
            title=title,
            severity="P1",
            category="Deployment",
            affected_files=[location],
            evidence=f"{location} configures wildcard CORS.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Wildcard CORS on authenticated APIs can weaken browser origin boundaries.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加允许域名列表配置测试"]),
            verification_steps=["确认 CORS origin 是明确白名单。"],
            false_positive_notes="纯公开静态资源可允许广泛读取；用户数据 API 不应这样配置。",
            references=["https://owasp.org/Top10/2025/en/"],
        )

    def _weak_cookie(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "Cookie security flags may be missing"
        beginner = "登录 cookie 如果缺少安全属性，更容易被脚本读取或在不安全连接中暴露。"
        fix = "为会话 cookie 设置 httpOnly、secure 和 sameSite，并确认 HTTPS。"
        return Finding(
            id=next_id("DEPLOY", index),
            title=title,
            severity="P2",
            category="Deployment",
            affected_files=[location],
            evidence=f"{location} sets cookie without obvious security flags.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Session cookies should use defensive browser flags.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加 cookie 配置单元测试"]),
            verification_steps=["确认响应 Set-Cookie 包含 httpOnly、secure、sameSite。"],
            false_positive_notes="非会话 cookie 可能不需要全部属性，但应解释用途。",
            references=["https://owasp.org/www-project-application-security-verification-standard/"],
            confidence="suspected",
        )

    def _missing_headers(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Next.js app has no obvious security headers"
        beginner = "安全响应头不是万能的，但能减少 XSS、点击劫持、内容嗅探等常见风险。"
        fix = "在 next.config.js 或中间件中配置基础安全 headers，并根据业务设置 CSP。"
        return Finding(
            id=next_id("DEPLOY", index),
            title=title,
            severity="P3",
            category="Deployment",
            affected_files=[location],
            evidence=f"{location} does not appear to define common security headers.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Security headers provide browser-enforced defense-in-depth.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["增加 header 配置测试"]),
            verification_steps=["运行本地构建或请求检查，确认 headers 存在。"],
            false_positive_notes="Headers 可能由托管平台或反向代理设置；请人工确认。",
            references=["https://nextjs.org/docs/app/api-reference/config/next-config-js/headers"],
            confidence="suspected",
        )
