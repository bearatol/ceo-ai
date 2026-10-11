# CEO AI

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**不知道怎样做更合适？先和 AI CEO 商量一下。**

CEO AI 帮助 AI 助手分析决策、质疑缺乏依据的假设、选择方案并协调执行。
你提供目标和限制，CEO 应说明判断依据，在新证据出现时修正建议，并根据任务复杂度安排工作。

本仓库包含指令和 Python 工具。模型、文件访问权限和子智能体运行能力由你使用的 AI 工具提供。

## CEO 可以做什么

- 讨论可行方案，指出会影响结果的错误，也检查自己的判断。
- 简单问题简短处理；存在步骤依赖时制定计划。
- 检查可用技能和智能体。能力不足时，在你的授权范围内建议安装或创建合适组件。
- 分配边界明确的任务，并核验证据后再接受结果。
- 编写代码时采用测试驱动开发（TDD）；文字与讨论采用编辑或场景检查。
- 在作出影响重大的决定前，请独立决策导师复核。

## 不安装也能试用

先克隆仓库。以下命令适用于 macOS、Linux 和 WSL：

```bash
mkdir -p "$HOME/proj"
git clone https://github.com/bearatol/ceo-ai.git "$HOME/proj/ceo-ai"
cd "$HOME/proj/ceo-ai"
```

在 AI 工具中打开此文件夹，然后发送：

```text
阅读 CONNECT.md，并应用 skills/ceo/SKILL.md。
以当前仓库目录为生态系统根目录。
帮我选择完成以下任务的方案：……
限制条件和成功标准是：……
```

如果在其他项目中使用，请提供 `ceo-ai` 克隆目录的完整路径，并允许工具读取它。
仅打开仓库不会自动注册技能或子智能体。

## 安装到 Codex、Claude Code 或 Cursor

保留克隆目录，组件清单、角色提示词和工具都在其中。从下表选择**一个**目标位置，
将 `skills/` 中的七个文件夹复制进去，保留各自的 `SKILL.md`。
如果已存在同名文件夹，请先手动比较。

| 工具 | 个人技能目录 | 单个项目的技能目录 | 调用方式 |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/` | `.agents/skills/` | `$ceo` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | `/ceo` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` | 在 Agent 聊天中输入 `/ceo` |

目录和调用方式已于 2026 年 10 月 11 日参照官方
[Codex](https://developers.openai.com/codex/skills/)、
[Claude Code](https://code.claude.com/docs/en/skills) 和
[Cursor](https://cursor.com/docs/skills) 文档核对。
这里的 Claude 指 **Claude Code**，不是 claude.ai 聊天界面。

个人安装时，只执行下面三个赋值命令中的一个：

```bash
ceo_skill_dir="$HOME/.agents/skills"   # Codex
```

```bash
ceo_skill_dir="$HOME/.claude/skills"   # Claude Code
```

```bash
ceo_skill_dir="$HOME/.cursor/skills"   # Cursor
```

然后在同一个 Bash 或 Zsh 终端中，进入 `ceo-ai` 仓库并执行以下代码。
它会在复制前检查全部目标；发现任何同名条目便停止。

```bash
(
  set -eu
  : "${ceo_skill_dir:?Choose a skill destination first}"
  test -f CONNECT.md
  test -f skills/ceo/SKILL.md
  for ceo_source in skills/*; do
    ceo_name=$(basename "$ceo_source")
    if [ -e "$ceo_skill_dir/$ceo_name" ] || [ -L "$ceo_skill_dir/$ceo_name" ]; then
      printf 'Already exists; compare manually: %s\n' "$ceo_skill_dir/$ceo_name" >&2
      exit 1
    fi
  done
  mkdir -p "$ceo_skill_dir"
  for ceo_source in skills/*; do
    cp -R "$ceo_source" "$ceo_skill_dir/"
  done
)
```

如需仅用于一个项目，将 `ceo_skill_dir` 改为该项目对应技能目录的完整路径。
原生 Windows 用户可用 Git 克隆仓库，再通过文件管理器复制相同文件夹。
`~` 表示用户主目录，项目相对路径从目标仓库根目录算起。
避免在工具同时扫描的多个目录中安装同名技能。

开启新会话。在 Codex 中调用 `$ceo`，在 Claude Code 或 Cursor 中调用 `/ceo`。
然后发送以下请求，并将路径占位符替换为真实路径：

```text
CEO AI 的生态系统根目录是：<ceo-ai 克隆目录的完整路径>。
阅读其中的 CONNECT.md，处理当前项目。
目标：……；截止时间：……；成功标准：……
请检查可能影响结果的假设。
```

技能副本不包含组件清单。移动仓库后，需要告知助手新路径。

## 日常使用

征求建议：“比较这两个方案。哪些假设目前还没有证据支持？”

执行任务：“修复这个错误。先用失败的测试复现，再做最小改动并验证结果。”

重大决策：“检查这份迁移计划。在确定方案前，请独立导师评估假设、回滚方式和其他选择。”

CEO 应先给出建议或结果，再说明依据和关键限制。它应尊重你经过考虑的选择，
没有新证据时不应反复讨论已定事项。如果预算、期限和权限会影响方案，请明确说明。

## 子智能体与独立导师

安装技能后，主助手便可按 CEO 工作流程处理任务。命名角色仍需单独注册。
`agents/` 中的四个文件是可移植的角色提示词，不是各平台可直接加载的配置。
建议先在**主会话中使用 CEO 技能**，需要时再注册专门角色。

| 工具 | 项目内角色文件 | 导师的只读设置 |
| --- | --- | --- |
| Codex | `.codex/agents/decision-mentor.toml` | `sandbox_mode = "read-only"` |
| Claude Code | `.claude/agents/decision-mentor.md` | `tools: Read, Glob, Grep` |
| Cursor | `.cursor/agents/decision-mentor.md` | `readonly: true` |

按工具的原生格式创建文件，使用名称 `decision-mentor`、简短描述，以及
`agents/decision-mentor.md` 中的角色正文。加入已获准访问的仓库路径，供它读取清单、
选定技能和协议。Codex 将正文放入 `developer_instructions`；Claude Code 和 Cursor
将正文放在 YAML 元数据之后。具体格式见
[Codex](https://developers.openai.com/codex/subagents/)、
[Claude Code](https://code.claude.com/docs/en/sub-agents) 和
[Cursor](https://cursor.com/docs/subagents) 官方说明。

需要时可用同样方式注册 `engineer` 和 `qa-reviewer`，只授予任务所需工具，并保留角色的访问限制。
独立的 **CEO 智能体**只读并委派修改；**CEO 技能**使用主助手已有的权限。
委派前要确认角色确实可调用、工具权限确实受限。文件存在本身不能证明这些条件成立。

上述设置不等于完整的离线安全沙箱。独立安全审查员必须满足项目要求的技术限制，
导师和 QA 不能替代安全审查。如果无法使用子智能体，CEO 可以提供建议并完成获准的工作，
但必须说明缺少独立审查，并推迟必须经过该审查才能作出的决定。

## 检查仓库

在仓库目录中使用 Python 3.10 或更新版本运行，无需第三方 Python 包。

```bash
python3 tools/team/team.py --home . list --type agent
python3 scripts/catalog.py --pack . validate
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check.py
```

Bash 用户也可运行 `bash tests/test.sh` 和 `bash scripts/doctor.sh`。
这些检查验证仓库内容，不验证平台中的角色注册状态或模型实际表现。

POSIX 系统还可以运行可选的能力清单工具：

```bash
python3 scripts/ceo_inventory.py --home .
python3 scripts/ceo_inventory.py --home . --refresh
```

第一条命令读取元数据；第二条在获得授权时写入被 Git 忽略的缓存。
工具会拒绝符号链接和不支持的目录结构。原生 Windows 或其他布局应使用所在工具认可的发现机制。
发现某项能力并不等于安装了它，也不会授予权限。

## 更新、卸载与排查

使用更新前先查看上游改动。在没有本地修改的克隆目录中运行 `git pull --ff-only`，
重新检查，再比较并更新你安装的技能副本和角色配置。复制安装不会自动更新。
卸载时只删除自己安装的副本和角色文件，保留其他文件及本地修改，然后重启工具。

如果找不到 `ceo`，请检查目标目录、`SKILL.md` 文件名、同名技能和工具设置。
如果找不到组件清单，请明确提供克隆目录路径。如果无法调用角色，请检查原生注册和实际权限。

## 内容与限制

本仓库包含七个技能、四个角色提示词、任务与结果契约、任务数据包工具及可选清单工具。
英文技术资料包括[详细指南](docs/CEO_GUIDE.md)、[连接协议](CONNECT.md)
和[文件来源记录](docs/PROVENANCE.json)。

工具权限和项目的强制审查规则始终有效。本仓库不自动安装缺失组件，也不提供已隔离的安全审查员。
指令本身不会授予访问权限。目前尚未在这三个产品中全部完成端到端集成验证。

部分规划和审查实践参考了 Superpowers，但没有包含其提示词。
质量优势或成本节省尚无对照测量结果。原始版权声明保留在 [MIT 许可证](LICENSE) 中。
