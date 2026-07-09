# VibeSpec_Gate-skill

[English](README.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Package mode](https://img.shields.io/badge/package-prompt--only%20Skill-green)](README.md#default-lite-package)
[![Security boundary](https://img.shields.io/badge/security-not%20a%20certification-orange)](README.md#safety-boundary)

VibeSpec_Gate-skill 是一个 **面向 AI 构建产品的 LLM 原生安全审查 Skill**。

上线前，用它回答一个实际问题：

> 这个应用会不会泄漏密钥、暴露用户数据、带着薄弱的登录/session 流程上线，或者给 Agent/工具过大的权限？

VibeSpec_Gate-skill 会审查项目证据，并输出：

- 上线决策；
- 最高优先级的安全和数据风险；
- 经人工确认后可交给 coding Agent 的有边界修复任务；
- 修复后的复测清单。

## 默认 Lite 包

默认 Lite 包是 **prompt-only** 且 **Agent-native** 的。首次使用者不需要安装 Python 项目、运行仓库测试、理解 scorer 输出、查看 calibration 数据，或使用 release 工具，就能得到上线决策。

使用方式：

1. 将 Lite 包安装或复制到你的 Agent 环境。
2. 用 `examples/lite_review_prompt.md` 让 Agent 审查你的项目。
3. 阅读生成的 Lite 审查文件。

起始提示词：

```text
Review this project for launch-blocking security risks.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, and admin-auth risks,
produce bounded coding-Agent fix tasks after human confirmation, and produce a retest checklist.
```

预期输出：

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

## 如何阅读结果

按这个顺序阅读：

1. `launch_decision.md`：项目是否被阻断、需要人工审查、可带警告上线，或可通过。
2. `top_security_risks.md`：最高影响风险和相关证据。
3. `agent_fix_plan.md`：经人工确认后可交给 coding Agent 的有边界修复任务。
4. `retest_checklist.md`：修复后需要执行的检查。

上线决策含义：

- `BLOCK`：暂时不要上线；一个或多个发现当前阻断上线。
- `REVIEW`：不要视为可上线；仍需要人工确认或补充证据。
- `PASS_WITH_WARNINGS`：没有发现上线阻断项，但仍有警告需要审查。
- `PASS`：在已审查证据中，没有发现实质性上线风险。

## 安全边界

`agent_fix_plan.md` 是修复计划，不是允许 Agent 盲改代码的许可。

- 让 coding Agent 修改项目前，先由人确认证据和范围。
- 不要自动写入 suppressions。
- 修复时不要扩大权限、移除校验、增加绕过逻辑，或修改生产系统。
- 修复后使用 `retest_checklist.md` 复测。
- 不要把 VibeSpec_Gate-skill 当作专业安全认证、渗透测试、法律审查或合规证明。

## 审查范围

VibeSpec_Gate-skill 关注影响上线的风险：

- 暴露的 API key、service-role key、数据库 URL 和凭证；
- 登录、注册、密码重置、OTP、magic-link、session、token、账号枚举和 admin-auth 错误；
- 缺失鉴权、对象归属校验错误、不安全的数据库规则；
- 缺少 rate-limit、CAPTCHA/provider abuse-control 或 reset-token 过期证据；
- 有风险的 CORS、cookie、session、header、上传、日志和部署配置；
- prompt 或 prompt 日志暴露；
- Agent、MCP/IPC、Electron、shell、本地文件、邮件、数据库或支付工具权限过大；
- 上线前需要人工确认的不确定性。

## 可选 Core 路径

完整仓库还提供一个可选的 Core-powered CLI overlay，用于生成更可重复的本地证据：

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibesec.cli lite-review .\my-project --output .\lite_review --no-adapters
```

CLI 是仓库基础设施，不是默认 prompt-only Skill 包的使用前提。
当存在更深入的审查证据时，`llm_review_packet.json` 是用于模型辅助审查流程的 LLM-native handoff packet。

## 文档

从这里开始：

- [Lite quickstart](docs/usage/lite_quickstart.md)
- [Lite review prompt](examples/lite_review_prompt.md)
- [Agent review cookbook](docs/usage/agent_review_cookbook.md)
- [Documentation index](docs/README.md)

维护者文档：

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

运行聚焦测试：

```powershell
py -3 -m pytest tests/test_lite_package_verifier.py tests/test_lite_release_validation.py tests/test_lite_review_bundle.py tests/test_lite_rc_hardening.py
```

仓库结构：

```text
.
|-- SKILL.md
|-- examples/
|-- skill/
|-- src/vibesec/
|-- scripts/
|-- tests/
|-- docs/
`-- .github/
```

`outputs/` 和 `test output/` 这类生成目录会被 Git 忽略，不应放到 GitHub 上。

## 治理

- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## License

目前还没有选择开源许可证。在添加 `LICENSE` 文件前，不要假定可以复用、再分发或重新授权。
