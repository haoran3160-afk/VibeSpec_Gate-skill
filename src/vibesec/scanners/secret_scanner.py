from __future__ import annotations

import re
from pathlib import Path

from vibesec.core.fix_prompt_builder import build_fix_prompt
from vibesec.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, iter_text_files, looks_like_frontend, mask_secret, next_id, read_lines, rel


SECRET_PATTERNS = [
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("Stripe secret key", re.compile(r"sk_(?:test|live)_[A-Za-z0-9]{16,}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")),
    ("Database URL", re.compile(r"(postgres(?:ql)?|mysql|mongodb)://[^\\s'\"<>]+", re.I)),
    ("Supabase service role key", re.compile(r"service[_-]?role[^\\n]{0,40}(eyJ[A-Za-z0-9_\-]{20,})", re.I)),
]

KEY_ASSIGNMENT_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|private[_-]?key|database[_-]?url)\s*[:=]\s*['\"]?([^'\"\s]{12,})"
)


class SecretScanner(BaseScanner):
    name = "secret_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            lines = read_lines(path)
            if path.name in {".env", ".env.local", ".env.production"}:
                findings.append(self._env_file_finding(root, path, index))
                index += 1
            for line_no, line in enumerate(lines, start=1):
                if self._is_placeholder(line):
                    continue
                for label, pattern in SECRET_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        findings.append(self._secret_finding(root, path, line_no, label, match.group(0), index))
                        index += 1
                assignment = KEY_ASSIGNMENT_RE.search(line)
                if (
                    assignment
                    and not self._is_public_client_value(assignment.group(1), assignment.group(2))
                    and not self._is_env_reference(assignment.group(2))
                ):
                    findings.append(
                        self._secret_finding(
                            root,
                            path,
                            line_no,
                            assignment.group(1),
                            assignment.group(2),
                            index,
                            severity="P2",
                            confidence="suspected",
                        )
                    )
                    index += 1
                if looks_like_frontend(path) and "service_role" in line.lower():
                    findings.append(self._frontend_service_role(root, path, line_no, index))
                    index += 1
        return findings

    def _env_file_finding(self, root: Path, path: Path, index: int) -> Finding:
        title = "Environment file appears to be present in the project"
        beginner = "环境变量文件通常保存密钥。如果它被提交到仓库或打包进前端，别人可能拿到你的数据库或第三方服务权限。"
        fix = "确认该文件没有被提交；把真实值放到部署平台的环境变量；仓库只保留 `.env.example`。"
        return Finding(
            id=next_id("SEC", index),
            title=title,
            severity="P1" if path.name != ".env.example" else "P3",
            category="Secrets",
            affected_files=[rel(path, root)],
            evidence=f"Found {path.name}; values are intentionally not printed.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Checked-in environment files frequently contain credentials, tokens, and service connection strings.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [rel(path, root)], fix, ["确认真实 .env 文件被 .gitignore 排除"]),
            verification_steps=["重新扫描项目，确认报告中没有真实 `.env` 文件 finding。", "检查 GitHub secret scanning 或 Gitleaks 历史扫描结果。"],
            false_positive_notes="如果文件只包含占位符，应改名为 `.env.example` 并确认没有真实值。",
            references=["https://docs.github.com/code-security/secret-scanning/about-secret-scanning"],
        )

    def _secret_finding(
        self,
        root: Path,
        path: Path,
        line_no: int,
        label: str,
        value: str,
        index: int,
        severity: str | None = None,
        confidence: str = "confirmed",
    ) -> Finding:
        title = f"Possible hardcoded secret: {label}"
        location = rel(path, root, line_no)
        beginner = "代码里疑似写入了密钥。上线后任何能看到代码、bundle、日志或仓库的人都可能复用它。"
        fix = "立即确认该值是否真实；如果真实，轮换密钥；从代码中移除；改用服务端环境变量；检查历史提交。"
        evidence = f"{location} contains secret-like value {mask_secret(value)}"
        return Finding(
            id=next_id("SEC", index),
            title=title,
            severity=severity or ("P0" if "service" in label.lower() or "private" in label.lower() else "P1"),
            category="Secrets",
            affected_files=[location],
            evidence=evidence,
            why_it_matters_for_beginner=beginner,
            technical_reason="Static pattern matching found a token/credential-shaped value in a project file.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加测试或扫描步骤，防止密钥再次被提交"]),
            verification_steps=["重新运行 VibeSec Gate 或 Gitleaks。", "确认报告只显示脱敏片段且不再发现该值。"],
            false_positive_notes="测试假值可能误报；真实密钥仍应轮换，因为仓库历史可能已经暴露。",
            references=["https://github.com/gitleaks/gitleaks", "https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/quick_start"],
            confidence=confidence,
        )

    def _frontend_service_role(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        title = "Supabase service role referenced from frontend-like code"
        location = rel(path, root, line_no)
        beginner = "Supabase service role key 相当于数据库万能钥匙，不能放到浏览器代码里。"
        fix = "前端只使用 publishable/anon key；需要高权限操作时通过服务端 API 代理并做鉴权。"
        return Finding(
            id=next_id("SEC", index),
            title=title,
            severity="P0",
            category="Secrets",
            affected_files=[location],
            evidence=f"{location} references service_role in frontend-like path.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Service role keys bypass RLS and must only live in trusted server environments.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["确认前端 bundle 不包含 service role 字符串"]),
            verification_steps=["重新扫描前端目录。", "确认服务端代理有 session/user 校验。"],
            false_positive_notes="如果只是文档说明，请移动到安全文档并避免包含真实值。",
            references=["https://supabase.com/docs/guides/database/postgres/row-level-security"],
        )

    def _is_placeholder(self, line: str) -> bool:
        lowered = line.lower()
        return any(word in lowered for word in ("example", "placeholder", "your_", "replace_me", "changeme"))

    def _is_public_client_value(self, key: str, value: str) -> bool:
        lowered = f"{key} {value}".lower()
        return "anon" in lowered or "publishable" in lowered or "public" in lowered

    def _is_env_reference(self, value: str) -> bool:
        stripped = value.strip().strip("'\"")
        lowered = stripped.lower()
        if lowered.startswith(("process.env.", "os.environ", "settings.", "config.")):
            return True
        return bool(re.fullmatch(r"[A-Z][A-Z0-9_]{6,}", stripped))
