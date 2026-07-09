# VibeSpec Gate

[中文](README.md) | [English](README.en.md)

**给 vibe coding 做出来的产品，一个上线前的安全门禁。**

AI 帮你把产品做出来了，但它真的能上线吗？

VibeSpec Gate 让你的 coding Agent 先回答最关键的问题：

> 会不会泄露密钥、暴露用户数据、登录/权限有洞，或者给 Agent/tool 太大权限？

它会输出能不能上线、最该先修的风险、Agent 可执行的修复任务和复测清单。

## 你会得到什么

VibeSpec Gate 会生成四个主要文件：

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

按这个顺序阅读：

1. `launch_decision.md`：产品是否可以上线。
2. `top_security_risks.md`：影响最大的风险和相关证据。
3. `agent_fix_plan.md`：经过 human confirmation 后，可以交给 coding Agent 的有限修复任务。
4. `retest_checklist.md`：修复后的安全复测步骤。

决策含义：

- `BLOCK`：暂时不要上线，先修这个问题。
- `REVIEW`：不要直接认为安全，需要人工确认。
- `PASS_WITH_WARNINGS`：没有发现上线阻断项，但仍有警告。
- `PASS`：在已审查证据中没有发现上线阻断风险。

## 快速开始

优先使用 prompt-only Lite 流程。这是 default Lite package 的默认路径。

1. 把这个 Skill 复制或安装到你的 Agent 环境。
2. 在 Agent 中打开你的产品项目。
3. 粘贴这个提示词：

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

## 它会检查什么

VibeSpec Gate 关注会影响上线的风险：

- 泄露的 secrets、API keys、service-role keys、数据库 URL 和凭据；
- 登录、注册、密码重置、OTP、magic-link、session、token、账号枚举、rate-limit 和 admin-auth 错误；
- 缺少登录检查，或用户数据归属检查错误；
- 过度开放的 Supabase、Firebase、存储或数据库规则；
- CORS、cookie、session、header、上传、日志和部署配置风险；
- prompt 或 prompt 日志暴露；
- 过大的 Agent/tool 权限，包括 MCP/IPC、Electron、shell、本地文件、邮件、数据库和支付工具；
- 上线前必须人工确认的缺失证据。

## 安全边界

`agent_fix_plan.md` 是修复计划，不是允许 Agent 未经确认就修改代码的许可。

让 coding Agent 修改项目之前：

- 确认问题真实存在；
- 确认要修改的文件和范围；
- 不要自动写 suppressions；
- 不要扩大权限、移除校验或增加绕过逻辑；
- 不要让 Agent 在没有 human confirmation 的情况下选择 CAPTCHA provider、rate-limit 阈值、MFA 策略、身份提供商、账号找回策略或生产账号变更；
- 不要在报告或修复计划里打印完整 OTP、reset token、JWT、cookie、session id、authorization header 或 secret。

VibeSpec Gate 不是 professional security certification、penetration test、legal review 或 compliance attestation。

## 默认 Lite 包

默认 Lite 包是 prompt-only。首次使用者只需要 Skill 说明和 coding Agent。

## 可选 Core-Powered 路径

如果你从源码仓库使用，并希望生成可重复的本地证据，可以使用 optional Core-powered 路径：

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

CLI 是可选能力，不是 prompt-only Lite Skill 的使用前提。

当存在更深入的审查证据时，`llm_review_packet.json` 是供模型辅助审查使用的 LLM-native handoff packet。

## 文档

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Lite review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](docs/usage/agent_review_cookbook.md)
- [Changelog](CHANGELOG.md)

## 构建 Lite zip

```powershell
py -3 scripts\build_lite_package_zip.py
```

zip 内包含 prompt-only Lite 包文件和 Apache-2.0 许可证。

## License

Apache License 2.0。见 [LICENSE](LICENSE)。

许可证只处理复用和分发授权，不代表 VibeSpec Gate 是 professional security certification、penetration test、legal review 或 compliance attestation。
