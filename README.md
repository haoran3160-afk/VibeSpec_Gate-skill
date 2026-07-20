# VibeSpec Gate

简体中文 | [English](README.en.md)

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0rc1-orange.svg)](CHANGELOG.md)

**审查 Vibe Coding 产品的上线阻断风险，生成有证据、可确认、可复测的修复任务。**

VibeSpec Gate 会检查你授权范围内的登录授权、用户数据、密钥、数据库规则、部署配置以及 Agent、MCP、IPC、Electron 权限边界，并输出上线决策、最高影响风险、有界修复任务和项目专属复测清单。

证据不足、范围不完整或读取被截断时不能得到 `PASS` 或 `PASS_WITH_WARNINGS`：已有明确阻断证据时仍为 `BLOCK`，否则为 `REVIEW`。`PASS` 只表示在明确声明且完成覆盖的审查范围内没有发现重大风险，不是安全证明。

> 当前为 `0.2.0rc1`，适合辅助审查和受控试用，不能替代专业渗透测试、安全认证、法律意见或合规审计。

## 输出示例

```text
示意示例，不是真实项目审查

Decision: BLOCK
Coverage: partial
Risk: 私有订单接口没有验证调用者或订单所有者。
Evidence: app/api/orders/route.ts:18
Human confirmation: 确认订单归属与管理员访问规则。
Agent task: 仅在确认后增加服务端身份校验和 owner/tenant 约束。
Retest: 用户 A 无法读取或修改用户 B 的订单。
```

真实审查默认先在聊天中返回：

- 七类证据覆盖状态与缺失证据；
- `BLOCK`、`REVIEW`、`PASS_WITH_WARNINGS` 或 `PASS`；
- 最高影响风险及文件证据；
- 需要人工确认的有界修复任务；
- 项目专属复测清单。

只有你明确要求保存并批准项目外目录后，Agent 才会使用四个模板生成 `launch_decision.md`、`top_security_risks.md`、`agent_fix_plan.md`、`retest_checklist.md` 和 `evidence/`。

## 能检查什么

- **身份与访问：** 登录、注册、密码重置、OTP、session、token、owner、tenant 和 admin 授权。
- **密钥与数据：** 源码凭据、日志泄露、客户端数据访问、数据库和存储规则、上传与数据边界。
- **Agent 与工具权限：** LLM tool、MCP、文件、shell、数据库、邮件、支付和人工确认边界。
- **桌面与 IPC：** Electron preload、IPC handler、渲染进程、文件系统和进程调用边界。
- **部署暴露面：** 调试入口、CORS、cookie、header、rate limit、滥用控制和生产配置。

VibeSpec Gate 不会自动选择身份提供商、CAPTCHA、MFA、恢复策略、限流阈值、密钥轮换、数据保留或生产账号变更，也不会在未授权时运行动态或线上测试。

## 安装

推荐让 `$skill-installer` 从仓库中的唯一 Skill 单元安装：

```text
Use $skill-installer to install the Skill from https://github.com/haoran3160-afk/VibeSpec_Gate-skill/tree/master/skills/vibespec-gate.
```

安装完成后新建一个 Agent 任务。`$skill-installer` 默认安装到 `$CODEX_HOME/skills/vibespec-gate`（通常是 `$HOME/.codex/skills/vibespec-gate`）。手动安装也可使用用户级 `$HOME/.agents/skills/vibespec-gate` 或仓库级 `.agents/skills/vibespec-gate`。

手动安装时，完整复制 `skills/vibespec-gate/`，不要只复制 `SKILL.md`。

Windows PowerShell：

```powershell
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
Set-Location VibeSpec_Gate-skill
$Target = Join-Path $HOME ".agents/skills/vibespec-gate"
if (Test-Path -LiteralPath $Target) { throw "Target already exists: $Target" }
New-Item -ItemType Directory -Force (Split-Path -Parent $Target) | Out-Null
Copy-Item -LiteralPath "skills/vibespec-gate" -Destination $Target -Recurse
Test-Path -LiteralPath (Join-Path $Target "SKILL.md")
```

macOS 或 Linux：

```bash
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
cd VibeSpec_Gate-skill
test ! -e "$HOME/.agents/skills/vibespec-gate"
mkdir -p "$HOME/.agents/skills"
cp -R skills/vibespec-gate "$HOME/.agents/skills/vibespec-gate"
test -f "$HOME/.agents/skills/vibespec-gate/SKILL.md"
```

也可以从 [`v0.2.0-rc.1` Release](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/tag/v0.2.0-rc.1) 下载 [`vibespec-gate-lite.zip`](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/download/v0.2.0-rc.1/vibespec-gate-lite.zip) 和 [`SHA256SUMS`](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/download/v0.2.0-rc.1/SHA256SUMS)。校验后解压 ZIP，并安装其中完整的 `vibespec-gate/` 目录。

## 60 秒开始审查

在产品仓库中新建 Agent 任务并输入：

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Keep the project read-only. Start with a chat-only result and do not create files.
Show evidence coverage, the launch decision, the highest-impact risks, repair tasks
that require human confirmation, and a project-specific retest checklist.
```

如果需要保存结果，再单独批准一个不与项目重叠的输出目录。审查和修复是两次授权：收到修复计划不代表 Agent 可以修改项目。

## 证据与决策

每次审查都必须覆盖或说明以下七类表面：`auth`、`authorization`、`secrets`、`data_rules`、`deployment`、`agent_tools`、`desktop_ipc`。

| 决策 | 含义 |
| --- | --- |
| `BLOCK` | 已确认上线阻断证据，暂时不要上线。覆盖不完整也可以阻断。 |
| `REVIEW` | 证据不足、部分缺失、被截断、含糊或需要人工判断。 |
| `PASS_WITH_WARNINGS` | 覆盖完整且没有阻断项，但仍有低优先级或已接受警告。 |
| `PASS` | 覆盖完整、没有缺失审查面，且没有重大风险或剩余警告。 |

仅凭“没有发现问题”不能推导出 `PASS`；完整覆盖且没有重大风险或剩余警告时才可以。证据不完整时不显示安全分数。

## 数据与修改边界

- Coding Agent 在你授权的权限内读取项目。内容是否离开本机取决于所用 Agent、模型提供商和配置。
- 默认只在聊天中返回结果。保存报告前必须批准项目外目录，输入和输出不得相同或互为父子目录。
- 报告与 `evidence/` 可能包含文件路径、代码片段和敏感上下文，分享前必须人工检查。
- 修复前必须再次确认发现、文件范围、允许变更和禁止变更。Skill 不会自动修复、自动忽略发现或扩大权限。
- 不输出完整密钥、OTP、reset token、JWT、cookie、session ID 或 authorization header。

## Skill 与可选 CLI

| | VibeSpec Gate Skill | 可选 CLI |
| --- | --- | --- |
| 用途 | 证据审查、覆盖判断、风险解释、人工确认、修复计划和复测 | 可重复的静态检查与结构化本地证据 |
| 安装 | 复制 `skills/vibespec-gate/` | 从源码安装 Python 项目 |
| 运行依赖 | 支持 Skill 的 Coding Agent | Python 3.10+ |
| 默认输出 | 聊天 | 明确指定的项目外目录 |
| 能力边界 | 不自动拥有 CLI 扫描能力 | 不能代替 Agent 对上下文和缺失证据的判断 |

源码模式的 CLI 示例：

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review D:\path\to\project --output D:\reviews\project-review --no-adapters
```

`--output` 必须明确提供、不得与项目目录重叠，且目标目录必须尚不存在。

## 验证与成熟度

- CI 在 Ubuntu Python 3.10/3.12、Windows Python 3.12 和 macOS Python 3.12 上运行完整测试、包校验和归档校验。
- Skill 已验证显式调用、无关任务不自动启用，以及 8 类上线判断和只读边界；[验证记录可复核](evals/runs/2026-07-20/README.md)。
- 这些 Agent 场景不是实际用户试用。受控真实用户试用尚未完成，因此项目保持 RC，不宣称 GA。
- 自动化和场景覆盖不能证明没有漏洞，也不能替代专业安全评估。

## 项目资源

- [英文 README](README.en.md)
- [文档索引](docs/README.md)
- [快速开始](docs/usage/lite_quickstart.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [变更日志](CHANGELOG.md)

Apache License 2.0，参见 [LICENSE](LICENSE)。
