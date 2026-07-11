# VibeSpec Gate

[English](README.md) | [简体中文](README.zh-CN.md)

[![CI](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/actions/workflows/ci.yml)
[![状态：RC](https://img.shields.io/badge/status-0.2.0rc1-orange.svg)](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/ROADMAP.md)
[![许可证：Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**面向 vibe coding 产品的 Agent-native、LLM-native 上线安全审查。**

上线前，让 coding Agent 检查项目证据并回答一个实际问题：

> 这个产品是否会泄露密钥、暴露用户数据、带着薄弱的登录或授权逻辑上线，或者给 Agent/工具过大的权限？

VibeSpec Gate 会生成上线决策、最高影响风险、必须经过人工确认的有界修复任务，以及项目专属复测清单。

> **候选发布状态：** Skill 已有确定性回归覆盖和维护者编写的 synthetic walkthrough，但尚未完成真实外部盲测。Synthetic walkthrough 只是契约测试，不是可用性证据。它不是专业安全认证或渗透测试。

<!-- section:see-it-work -->
## 查看结果形态

默认 Lite package 是 prompt-only。首次审查要求宿主 Agent 生成：

```text
lite_review/
  launch_decision.md
  top_security_risks.md
  agent_fix_plan.md
  retest_checklist.md
  evidence/
```

决策示例：

```text
合成示例 - 不是真实安全审查

Decision: BLOCK
风险：私有订单路由没有验证调用者身份或数据所有权。
证据：app/api/orders/route.ts
人工确认：确认预期的数据归属模型。
Agent 任务：增加服务端认证，并把读写限制为已认证数据所有者。
复测：确认用户 A 无法读取或修改用户 B 的订单。
```

这是合成示例。不得把它用作上线决策、审计结果或任何项目安全性的证明。参见[完整合成示例](examples/synthetic_review_example.md)。

<!-- section:install -->
## 安装 Lite Skill

可安装单元是 Lite zip 中唯一的 `vibespec-gate/` 目录，入口文件为 `vibespec-gate/SKILL.md`。

### 从源码构建并安装

需要 Git 和 Python 3.10 或更高版本。Python 只用于构建 zip；安装后的 prompt-only Skill 不依赖 Python CLI。

Windows PowerShell：

```powershell
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
Set-Location VibeSpec_Gate-skill
py -3 -c "import sys; assert sys.version_info >= (3, 10), sys.version"
py -3 scripts/build_lite_package_zip.py
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$SkillRoot = Join-Path $CodexHome "skills"
New-Item -ItemType Directory -Force $SkillRoot | Out-Null
py -3 -m zipfile -e dist/vibespec-gate-lite.zip $SkillRoot
Test-Path (Join-Path $SkillRoot "vibespec-gate\SKILL.md")
```

macOS 或 Linux：

```bash
git clone https://github.com/haoran3160-afk/VibeSpec_Gate-skill.git
cd VibeSpec_Gate-skill
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'
python3 scripts/build_lite_package_zip.py
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
python3 -m zipfile -e dist/vibespec-gate-lite.zip "${CODEX_HOME:-$HOME/.codex}/skills"
test -f "${CODEX_HOME:-$HOME/.codex}/skills/vibespec-gate/SKILL.md"
```

构建命令应输出 `PASS Lite package zip built`。最后一步在 PowerShell 中应返回 `True`，在 macOS/Linux 中应成功退出。

开始审查代码前，在新的宿主任务中运行激活 smoke：

```text
Use $vibespec-gate. Without reading a project, state its four launch decisions and
the required confirmation rule before Agent edits, then stop.
```

预期包含 `BLOCK`、`REVIEW`、`PASS_WITH_WARNINGS`、`PASS` 和 `human confirmation`。它比只检查文件存在更能证明指令已加载，但最终行为仍取决于宿主 Agent。

### 安装已发布版本

GitHub Release 发布后，下载 `vibespec-gate-lite.zip`，按照随附的 `SHA256SUMS` 校验后，再解压到宿主的 Skill 目录。Tag 工作流会从对应提交重新构建、测试、验证并附加这两个文件。

- [Release 页面](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases)
- [最新 Lite zip](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/latest/download/vibespec-gate-lite.zip)，首次 RC Release 后可用
- [最新 SHA256SUMS](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases/latest/download/SHA256SUMS)，首次 RC Release 后可用

当前没有 GA 版本。不要把旧 `v0.1.0` tag 当作更名后的 `vibespec-gate` 包。

### 兼容性

| 宿主 | 当前证据 |
| --- | --- |
| Codex Skill 目录 | 已验证包结构和 `agents/openai.yaml`；安装后需要重启或新建任务。 |
| 其他加载 `SKILL.md` 的宿主 | Prompt 契约可能可移植，但目前不宣称其安装和行为已经验证。 |
| 可选 Python CLI | 已在 Python 3.10 和 3.12 测试；CI 覆盖 Linux、Windows 和 macOS。 |

<!-- section:quick-start -->
## 60 秒开始审查

在 coding Agent 中打开产品仓库并输入：

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Before writing files, ask me for an approved output directory outside the reviewed
project. Do not default to writing lite_review/ inside the project.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, ownership,
and admin-auth risks. Produce bounded coding-Agent fix tasks only after human
confirmation, and produce a project-specific retest checklist.
```

按以下顺序阅读输出：

1. `launch_decision.md`：项目被阻断、需要复核，或没有发现阻断项。
2. `top_security_risks.md`：最高优先级风险的证据和上线影响。
3. `agent_fix_plan.md`：仍然需要人工确认的窄范围修复任务。
4. `retest_checklist.md`：确认修复后要执行的检查。

决策含义：

- `BLOCK`：暂时不要上线；已审查证据表明存在上线阻断项。
- `REVIEW`：证据缺失或含糊，需要人工复核。
- `PASS_WITH_WARNINGS`：没有发现阻断项，但仍有警告。
- `PASS`：在已审查证据中没有发现重大上线阻断项。

`PASS` 不等于产品安全证明。

<!-- section:how-it-works -->
## 工作流程

```text
已授权的项目证据
        -> 宿主 Agent 审查
        -> BLOCK / REVIEW / PASS_WITH_WARNINGS / PASS
        -> 人工确认
        -> 有界 Agent 修复任务
        -> 项目专属复测
```

Skill 优先检查密钥泄露、登录、注册、密码重置、OTP 和会话弱点、缺少服务端认证、数据所有权校验错误、不安全的数据库或存储规则、危险部署配置、prompt 暴露，以及缺少 rate-limit 或过大的 admin、Agent/MCP/IPC/Electron/工具权限。

<!-- section:data-boundary -->
## 数据与隐私边界

- **Prompt-only 模式：** 当前宿主 Agent 在你授权的权限内读取项目文件。内容是否离开本机取决于宿主、模型提供商和配置。处理私有代码前请先检查其策略。
- **带 `--no-adapters` 的本地 CLI：** 仓库代码读取本地文件并把审查结果写到你指定的路径；不会调用 LLM 提供商，也不会启用外部扫描器适配器。
- **可选适配器：** Semgrep、Gitleaks、Trivy 或 ZAP 等已安装工具只在启用时执行；其网络和数据处理行为不属于本 Skill 的保证范围。
- **生成证据：** 报告和 `evidence/` 可能包含路径、代码片段、发现项或敏感项目上下文。分享前必须人工检查并清理。`redacted` 字段不保证所有敏感值都已移除。

VibeSpec Gate 不会静默选择身份提供商、CAPTCHA 提供商、限流阈值、MFA 策略、密钥轮换方案或生产账号变更。

<!-- section:safety -->
## 安全边界

`agent_fix_plan.md` 是修复计划，不是允许 Agent 盲目编辑的许可。

- 修改前由人工确认每个发现、受影响文件和允许范围。
- 不要自动写 suppression，不要扩大权限、移除验证或增加绕过逻辑。
- 不要打印完整 OTP、reset token、JWT、cookie、session ID、authorization header 或 secret。
- 不要运行暴力破解、CAPTCHA 绕过、撞库、钓鱼、破坏性或未授权扫描。
- 所有真实项目审查输出必须写在被审查项目之外。

VibeSpec Gate 不是专业安全认证、渗透测试、法律审查、合规证明或绝对安全保证。

<!-- section:optional-cli -->
## 可选 Core-Powered CLI

CLI 是证据和回归基础设施，不是默认 Skill 体验。

存在更深入审查证据时，`llm_review_packet.json` 是交给宿主 Agent 推理的结构化 packet。它可能包含敏感项目上下文，分享前必须执行与其他证据相同的人工检查。

```bash
python -m pip install -e .
vibespec-gate lite-review ./my-project --output ./lite_review --no-adapters
```

不安装包时可从源码运行：

```bash
PYTHONPATH=src python -m vibespec_gate.cli lite-review ./my-project --output ./lite_review --no-adapters
```

PowerShell：

```powershell
$env:PYTHONPATH = "src"
py -3 -m vibespec_gate.cli lite-review .\my-project --output .\lite_review --no-adapters
```

<!-- section:validation -->
## 验证与成熟度

- CI 执行完整测试、包验证、归档验证和版本检查。
- Release tag 在发布资产前重新执行完整测试和打包门禁。
- 维护者加固使用确定性 fixture、明确标记的 synthetic walkthrough，以及带前后源文件完整性比较的授权项目检查。
- 真实外部盲测证据仍然缺失；synthetic walkthrough 不会被描述为 Agent 或参与者会话。

当前成熟度边界见[路线图](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/ROADMAP.md)。

<!-- section:project -->
## 项目资源

- [Lite 快速开始](docs/usage/lite_quickstart.md)
- [审查提示词](examples/lite_review_prompt.md)
- [Agent 审查手册](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/usage/agent_review_cookbook.md)
- [文档索引](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/README.md)
- [贡献指南](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CONTRIBUTING.md)
- [安全策略](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/SECURITY.md)
- [变更日志](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CHANGELOG.md)

Apache License 2.0，参见 [LICENSE](LICENSE)。
