# VibeSpec_Gate-skill

[English](README.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Package mode](https://img.shields.io/badge/package-prompt--only%20Skill-green)](README.md#default-lite-package)
[![Security boundary](https://img.shields.io/badge/security-not%20a%20certification-orange)](README.md#safety-boundary)

**给 vibe coding 产品用的上线前安全闸门。**

如果你用 Cursor、Claude Code、Codex、Lovable、Bolt、v0、Replit 或其他 vibe coding 工作流做了网站、SaaS、内部工具、Agent 或桌面应用，VibeSpec_Gate-skill 帮你回答上线前最难判断的问题：

> 这个产品现在能不能上线？还是有安全或用户数据风险必须先修？

它面向的不是安全专家，而是正在做产品的 vibe coding 用户。你不需要先学一堆安全术语，也能看懂它给出的结论。

它是一个 LLM-native Skill：你的 coding Agent 会读取说明、审查项目，并替你写出四个审查文件。

## 它会给你什么

VibeSpec_Gate-skill 会让你的 coding Agent 看一遍项目，并生成四个简单文件：

```text
lite_review/
  launch_decision.md       # 我能上线吗？
  top_security_risks.md    # 哪些问题可能伤害用户或产品？
  agent_fix_plan.md        # 哪些修复可以人工确认后交给 Agent 做？
  retest_checklist.md      # 修完后怎么确认真的修好了？
  evidence/                # 更深入审查用的证据
```

最重要的是 `launch_decision.md`。

它只用四种结论：

- `BLOCK`：先别上线，必须先修。
- `REVIEW`：不要直接当成安全，需要人确认。
- `PASS_WITH_WARNINGS`：没有发现上线阻断项，但还有警告。
- `PASS`：在已审查证据里，没有发现阻断上线的风险。

## 为什么需要它

vibe coding 可以很快做出一个真实产品，但你可能还没完全看懂生成的代码。

常见上线风险包括：

- 密钥、数据库地址或 API key 不小心进了项目；
- 私密页面或 API 不登录也能打开；
- 用户 A 能看到用户 B 的数据；
- 注册、登录、密码重置、OTP、magic-link、session、token、rate-limit、admin 登录有问题；
- 日志里打印了 token、cookie、重置链接或一次性验证码；
- 数据库或存储规则开得太大；
- Agent、MCP 工具、Electron 应用、shell 命令、本地文件工具、邮件工具、数据库工具或支付工具权限太大。

VibeSpec_Gate-skill 会把这些问题翻译成：能不能上线、风险是什么、Agent 可以安全修什么、修完怎么复测。

## 快速开始

先用默认的 prompt-only Lite 流程。

1. 把这个 Skill 复制或安装到你的 Agent 环境。
2. 在 Agent 里打开你的 vibe-coded 产品。
3. 粘贴这个提示词：

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, and admin-auth risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

然后阅读：

```text
lite_review/launch_decision.md
lite_review/top_security_risks.md
lite_review/agent_fix_plan.md
lite_review/retest_checklist.md
```

## 示例结果

```text
Decision: BLOCK

Why:
密码重置接口看起来接受没有过期时间、也不能保证一次性使用的 reset token。
如果重置链接泄漏，别人可能之后重复使用它接管账号。

First safe fix:
在你确认账号找回策略后，让 coding Agent 增加 reset token 过期和一次性使用校验。

Retest:
确认过期的 token 和已经使用过的 token 都会被拒绝。
```

这就是这个 Skill 追求的输出：短、直接、能指导你判断能不能上线。

## 默认 Lite 包

默认 Lite 包是 **prompt-only** 的。首次使用者不需要安装这个 Python 项目、运行仓库测试、理解内部评分、阅读校准笔记，或使用 release 工具。

完整仓库里有更深的引擎给维护者和高级用户使用，但普通用户第一路径保持轻量：

```text
复制 Skill -> 让 Agent 审查项目 -> 阅读四个文件 -> 修复和复测
```

## 它会检查什么

VibeSpec_Gate-skill 关注 vibe coding 用户最容易漏掉、但会影响上线的问题：

- secrets、API keys、service-role keys、数据库 URL 和凭证；
- 登录、注册、密码重置、OTP、magic-link、session、token、账号枚举、rate-limit 和 admin-auth 错误；
- 缺少登录校验，或用户数据归属检查错误；
- Supabase、Firebase、存储或数据库规则过宽；
- CORS、cookie、session、header、上传、日志和部署配置风险；
- prompt 或 prompt 日志暴露；
- Agent/tool 权限过大，包括 MCP/IPC、Electron、shell、本地文件、邮件、数据库和支付工具；
- 上线前需要人确认的缺失证据。

## 安全边界

`agent_fix_plan.md` 是修复计划，不是允许 Agent 盲改代码的许可。

让 coding Agent 改项目之前：

- 先确认这个问题真的存在；
- 先确认要改哪些文件、改到什么范围；
- 不要自动写 suppressions；
- 不要扩大权限、移除校验或增加绕过逻辑；
- 不要让 Agent 在没有人确认的情况下选择 CAPTCHA provider、rate-limit 阈值、MFA 策略、身份提供商、账号找回策略或生产账号变更；
- 不要在报告或修复计划里打印完整 OTP、reset token、JWT、cookie、session id、authorization header 或 secret。

VibeSpec_Gate-skill 不是专业安全认证、渗透测试、法律审查或合规证明。

## 可选 Core-Powered 路径

如果你 clone 了完整仓库，并希望得到更可重复的本地证据，可以运行可选 Core-powered Python CLI：

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

这个 CLI 是可选证据引擎，不是 prompt-only Lite Skill 的使用前提。
当存在更深入的审查证据时，`llm_review_packet.json` 是用于模型辅助审查流程的 LLM-native handoff packet。

## 我该用哪条路径？

| 你是... | 从这里开始 |
| --- | --- |
| 想知道产品能不能上线的 vibe coding 用户 | `examples/lite_review_prompt.md` |
| 想按步骤使用的用户 | `docs/usage/lite_quickstart.md` |
| 已经 clone 完整仓库的开发者 | 上面的可选 CLI 路径 |
| 维护者，需要验证包质量 | `scripts/verify_lite_package.py` 和 `scripts/verify_release.py` |

## 文档

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Lite review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](docs/usage/agent_review_cookbook.md)
- [Documentation index](docs/README.md)

维护者参考：

- [Lite package manifest](docs/design/lite_skill_package_manifest.md)
- [Lite package verification](docs/maintainers/lite_package_verification.md)
- [Release verification](docs/maintainers/release_verification.md)

## 本地开发

从源码安装：

```bash
python -m pip install -e .
```

验证 Lite 包边界：

```powershell
py -3 scripts\verify_lite_package.py
```

构建 prompt-only Lite zip：

```powershell
py -3 scripts\build_lite_package_zip.py
```

运行聚焦测试：

```powershell
py -3 -m pytest tests/test_lite_package_verifier.py tests/test_lite_release_validation.py tests/test_lite_review_bundle.py tests/test_lite_rc_hardening.py
```

`outputs/` 和 `test output/` 这类生成目录会被 Git 忽略。

## 治理

- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## License

Apache License 2.0。见 [LICENSE](LICENSE)。

许可证只处理复用和分发授权，不代表 VibeSpec_Gate-skill 是专业安全认证、渗透测试、法律审查或合规证明。
