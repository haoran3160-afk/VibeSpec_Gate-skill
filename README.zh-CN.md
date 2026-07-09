# VibeSpec Gate

[中文主界面](README.md) | [English](README.en.md)

中文 README 已切换为主界面：请阅读 [README.md](README.md)。

本文件保留为兼容入口，方便旧链接、打包脚本或用户收藏继续访问。

VibeSpec Gate 是面向 vibe-coded 产品的 LLM-native 上线安全检查 Skill。它帮助你在上线前判断产品是否存在必须先修的安全或数据风险。

主要输出：

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

决策含义：

- `BLOCK`：暂时不要上线，先修这个问题。
- `REVIEW`：不要直接认为安全，需要人工确认。
- `PASS_WITH_WARNINGS`：没有发现上线阻断项，但仍有警告。
- `PASS`：在已审查证据中没有发现上线阻断风险。

登录安全检查范围包括：登录、注册、密码重置、OTP、session、token、rate-limit、CAPTCHA 和 admin-auth 风险。

安全边界：`agent_fix_plan.md` 是修复计划，不是允许 Agent 未经 human confirmation 就修改代码的许可。不要在报告或修复计划里打印完整 OTP、reset token、JWT、cookie、session id、authorization header 或 secret。

VibeSpec Gate 不是 professional security certification、penetration test、legal review 或 compliance attestation。
