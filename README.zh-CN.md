# VibeSpec Gate

[English](README.md) | [简体中文](README.zh-CN.md)

[![许可证：Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**面向 vibe coding 产品的上线安全审查 Skill。**

上线前，让 coding Agent 检查项目证据并回答一个实际问题：

> 这个产品是否会泄露密钥、暴露用户数据、带着薄弱的登录或授权逻辑上线，或者给 Agent/工具过大的权限？

VibeSpec Gate 会生成上线决策、最高影响风险、必须经过人工确认且范围明确的修复步骤，以及项目专属复测清单。

<!-- section:capabilities -->
## 核心能力

VibeSpec Gate 聚焦会影响上线决策的安全控制点，而不是通用代码质量：

- **身份与访问：** 登录、注册、密码重置、OTP、session、token、数据所有权和 admin 授权。
- **密钥与敏感数据：** 凭据暴露、不安全的客户端数据访问，以及薄弱的数据库或存储规则。
- **Agent 与工具权限：** 过大的 LLM tool、MCP、IPC、Electron、文件系统、shell、数据库、邮件或支付权限。
- **部署暴露面：** 危险的生产配置、公开调试入口、缺少 rate-limit 和不安全默认值。

对于每个问题，Skill 会区分已经确认的风险和仍需回答的问题，在修改前要求人工确认，并生成项目专属复测。

<!-- section:see-it-work -->
## 查看结果形态

VibeSpec Gate 通过你正在使用的 coding Agent 执行审查。Agent 会在被审查项目之外、经批准的输出目录中生成以下文件：

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
示意示例 - 不是真实安全审查

Decision: BLOCK
风险：私有订单路由没有验证调用者身份或数据所有权。
证据：app/api/orders/route.ts
人工确认：确认预期的数据归属模型。
Agent 任务：增加服务端认证，并把读写限制为已认证数据所有者。
复测：确认用户 A 无法读取或修改用户 B 的订单。
```

此示例仅用于说明输出形式。不得把它用作上线决策、审计结果或任何项目安全性的证明。参见[完整示例](examples/synthetic_review_example.md)。

<!-- section:how-it-works -->
## 工作流程

```text
你授权读取的项目文件
        -> coding Agent 审查
        -> BLOCK / REVIEW / PASS_WITH_WARNINGS / PASS
        -> 人工确认
        -> 范围明确的修复任务
        -> 项目专属复测
```

<!-- section:install -->
## 安装 VibeSpec Gate

安装时需要把 zip 中的整个 `vibespec-gate/` 目录放入 coding Agent 的 Skill 目录。调用 Skill 时，Agent 会读取 `vibespec-gate/SKILL.md`。

### 从源码构建并安装

需要 Git 和 Python 3.10 或更高版本。Python 只用于构建 zip；安装后的 Skill 不依赖 Python。

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

构建命令应输出 `PASS`。最后一步在 PowerShell 中应返回 `True`，在 macOS/Linux 中应成功退出。

开始审查代码前，新建一个 coding Agent 任务并检查安装是否成功：

```text
Use $vibespec-gate. Without reading a project, state its four launch decisions and
the required confirmation rule before Agent edits, then stop.
```

预期包含 `BLOCK`、`REVIEW`、`PASS_WITH_WARNINGS`、`PASS` 和 `human confirmation`。出现这些内容表示 coding Agent 已加载 Skill 指令。

### 从 GitHub Releases 安装

打开 [Releases 页面](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/releases)，选择版本，同时下载 `vibespec-gate-lite.zip` 和 `SHA256SUMS`。校验 zip 后，再解压到 coding Agent 的 Skill 目录。

### 兼容性

| 使用环境 | 安装说明 |
| --- | --- |
| Codex | 把 `vibespec-gate/` 安装到 `$CODEX_HOME/skills`，然后新建任务。 |
| 支持 `SKILL.md` 的 coding Agent | 按该 Agent 的文档，把 `vibespec-gate/` 放入其 Skill 目录。 |
| 可选 CLI | 需要 Python 3.10 或更高版本。 |

<!-- section:quick-start -->
## 60 秒开始审查

在 coding Agent 中打开产品仓库并输入：

```text
Use $vibespec-gate to review this project for launch-blocking security risks.

Before writing files, ask me for an approved output directory outside the reviewed
project. Do not default to writing lite_review/ inside the project.

Tell me whether it can safely launch, explain the top security and data-safety risks,
including login, signup, password reset, OTP, session, token, rate-limit, ownership,
and admin-auth risks. Produce scoped coding-Agent fix tasks only after human
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

<!-- section:data-boundary -->
## 数据与隐私边界

- **Coding Agent 审查：** coding Agent 在你授权的权限内读取项目文件。内容是否离开本机取决于该 Agent、模型提供商和配置。处理私有代码前请先检查其策略。
- **带 `--no-adapters` 的本地 CLI：** 仓库代码读取本地文件并把审查结果写到你指定的路径；该选项不会调用 LLM 提供商或运行外部扫描器。
- **外部扫描器：** Semgrep、Gitleaks、Trivy 或 ZAP 等工具只在你启用后执行。使用前请检查各工具的网络和数据处理方式。
- **审查文件：** 报告和 `evidence/` 可能包含路径、代码片段、发现项或敏感项目上下文。即使报告显示敏感值已经脱敏，分享前仍必须人工检查并清理。

VibeSpec Gate 不会静默选择身份提供商、CAPTCHA 提供商、限流阈值、MFA 策略、密钥轮换方案或生产账号变更。

<!-- section:safety -->
## 安全边界

`agent_fix_plan.md` 是修复计划，不是允许 Agent 盲目编辑的许可。

- 修改前由人工确认每个发现、受影响文件和允许范围。
- 不要自动隐藏发现项，不要扩大权限、移除安全检查或增加绕过逻辑。
- 不要打印完整 OTP、reset token、JWT、cookie、session ID、authorization header 或 secret。
- 不要运行暴力破解、CAPTCHA 绕过、撞库、钓鱼、破坏性或未授权扫描。
- 所有真实项目审查输出必须写在被审查项目之外。

VibeSpec Gate 不是专业安全认证、渗透测试、法律审查、合规证明或绝对安全保证。

<!-- section:optional-cli -->
## 可选 CLI

当你需要可重复执行的命令行审查，或者需要归档和比较结果时，可以使用 CLI。对大多数用户，前面的 coding Agent 工作流程更适合作为起点。

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

<!-- section:project -->
## 项目资源

- [快速开始](docs/usage/lite_quickstart.md)
- [审查提示词](examples/lite_review_prompt.md)
- [Agent 审查手册](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/usage/agent_review_cookbook.md)
- [文档索引](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/docs/README.md)
- [贡献指南](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CONTRIBUTING.md)
- [安全策略](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/SECURITY.md)
- [变更日志](https://github.com/haoran3160-afk/VibeSpec_Gate-skill/blob/master/CHANGELOG.md)

Apache License 2.0，参见 [LICENSE](LICENSE)。
