# CEO AI

写作可选择插件内的 **`ceo-ai:writer`**，使用你的风格和普通键盘标点。
不需要 Docker，持久偏好需要单独启用。[安装与使用](docs/WRITER.md#简体中文)。

<a href="https://bearatol.github.io/ceo-ai/zh/"><img src="docs/assets/ceo-ai-banner.png" alt="CEO AI：讨论决策，协调工作" width="1280"></a>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![skills.sh 上的 CEO AI](https://skills.sh/b/bearatol/ceo-ai)](https://skills.sh/bearatol/ceo-ai)

**[网站](https://bearatol.github.io/ceo-ai/zh/) · [各职业使用示例](https://bearatol.github.io/ceo-ai/zh/#cases) · [安全](https://bearatol.github.io/ceo-ai/zh/#security) · [安装](https://bearatol.github.io/ceo-ai/zh/#install) · [帮助](https://bearatol.github.io/ceo-ai/zh/#help)**

网站提供使用场景和可直接发给智能体的安装消息。

**不知道怎样做更合适？先和 AI CEO 商量一下。**

CEO AI 为 Codex、Claude Code 和 Cursor 提供一套工作方法，帮助你讨论想法、选择方案，
再把任务做完。它会提出影响结果的问题，指出依据不足的假设，并说明开始前需要验证什么。

CEO AI 正在积极开发中。我们持续测试这个协调任务的技能，并根据测试结果和反馈改进它。

比如，你想重写一个应用。CEO 会先帮你明确重写要解决的问题，与小范围修改作比较，
再建议如何验证这个选择。决定之后，它会帮你制定计划并推进工作。

CEO 将提出的方案视为实现目标的一项假设。它检查关键前提、比较替代方案，
并在提出重要建议前查阅适用的成熟实践和权威一手资料。
它区分事实与推测，说明证据缺口，尊重用户知情后的偏好。
[如何检验方案](docs/CEO_GUIDE.md#check-the-proposal-against-the-outcome)。

[五个虚构技能示例: CEO, Writer, Security Scan, Debugger 和 User Review](docs/DIALOGUE.zh-CN.md).

## 索引时进行安全检查

CEO AI 在索引时本地检查选定的技能和代理，不执行其中的内容。内置扫描器需要
macOS、Linux 或原生 Windows（本地固定 NTFS 磁盘）上的 Python 3.10+，不需要 Docker，也不调用 LLM 或 API。
报告分别显示风险信号、未检查部分及未验证的信任状态。没有发现问题并不证明安全。

**[第一次扫描：安装 → “检查我的技能” → 理解结果](docs/QUICKSTART.zh-CN.md)。**
Windows 扫描拒绝网络驱动器、重解析点和包别名。参见 [Windows 范围与命令](docs/SECURITY_SCANNING.md#windows)。

同一插件包含 **`ceo-ai:security-scan`**，仅在主动运行额外扫描时
需要 Docker。复制指南中的请求，代理会检查兼容性、准备镜像并运行冒烟测试。
[ARM64 Docker 分步指南](docs/DOCKER_SCAN.zh-CN.md) ·
[技术限制](docs/SECURITY_SCANNING.md)

## 保留有用的经验

提出新方案前，CEO AI 会检查现有组件和适用实践，比较方案并说明选择。
获得同意后，它可以保存项目经验、设计模板，以及单独获批的跨项目偏好。
记忆默认关闭，每次保存都会告知你。可以用自然语言查看、修改、删除或关闭记忆。
[记忆与模板](docs/MEMORY.md#简体中文)。

## 调试代码与检查用户流程

原生插件还包含 **`ceo-ai:debugger`**：复现问题、验证可能的原因并检查小范围修复，
或在明确的范围内重构并保持已测试的行为。[Debugger 指南（英俄文）](docs/DEBUGGER.md)。

**`ceo-ai:user-review`** 从疲惫的新手和指定专业人士的角度检查流程。
它把专业知识与注意力、疲劳和动机分别考虑，指出具体障碍及可能离开的环节，
提出修改建议并说明取舍。这些是模拟产生的假设，不是用户研究或转化率预测。
[User Review 指南（英俄文）](docs/USER_REVIEW.md)。

这两个技能是当前源码中的新增内容，请核对所选发布版本。项目安装和 APM
仍然只提供核心 CEO 技能。

## 开始使用

在 **Codex、Claude Code 或 Cursor** 中打开项目，向助手发送：

```text
请按照以下说明，为我的 AI 应用安装 CEO AI。
先检查已有安装；应用支持插件时，请使用插件方式。
请先说明安装范围，并保留当前项目和本地修改。
https://github.com/bearatol/ceo-ai/blob/main/INSTALL.md
```

除非你指定版本，否则助手会选择最新的稳定发布版本。

Codex 和 Claude Code 可以使用插件管理器。Cursor 继续使用项目安装程序，
该程序也适用于 Windows、macOS 和 Linux 上的 Codex 与 Claude Code。
插件管理器会在项目外保存部分设置。你无需手动创建目录或复制文件。

安装后开启新会话。插件方式：在 Codex 中选择 **`ceo-ai:ceo-ai`**，
在 Claude Code 中调用 **`/ceo-ai:ceo-ai`**。
项目安装方式：Codex 使用 **`$ceo-ai`**，Claude Code 和 Cursor 使用 **`/ceo-ai`**。

[插件安装、更新与迁移](docs/PLUGINS.md#简体中文) ·
[Microsoft APM](docs/APM.md#简体中文)

### 单独安装技能

使用 Node.js 22.20 或更高版本时，可以通过
[Skills CLI](https://github.com/vercel-labs/skills/blob/main/README.md) 选择单个技能：

```sh
npx skills add bearatol/ceo-ai
```

[skills.sh 上的全部五个技能](https://skills.sh/bearatol/ceo-ai) ·
[SkillsMP 搜索](https://skillsmp.com/search?q=bearatol%2Fceo-ai&sortBy=stars)。
已请求 SkillsMP 索引收录，尚未确认已收录。

按照提示选择技能、目标智能体和安装范围。替换已有安装前，请保留本地修改。
此方式安装的是技能，不是原生插件。
[目录收录状态与推广指南（英文）](docs/DISTRIBUTION.md)。

## 可以这样问

> 我想推出一个新产品。帮我判断开发之前应该先验证什么。

> 我打算重写这个服务。请找出这个决定的薄弱之处，并提出其他方案。

> 我们需要增加支付功能。请制定计划，协助实现，并检查结果。

先说明你想得到什么结果。如果有期限、预算或其他限制，也一起告诉它。
不必提前准备一份很长的需求文档。

## 简短示例

以下是说明用的对话，不是实际运行记录，也不是模型评测结果：

> **你：** 服务太慢了，我们从头重写吧。
>
> **CEO：** 具体是哪一部分慢？已经测量过什么？重写可能成本很高，却没有解决原因。
>
> **你：** 生成报表很慢，其他部分都正常。
>
> **CEO：** 先选一份报表，测量耗时，找出最慢的步骤，再验证一个有针对性的修改。
> 根据结果判断是否需要重写整个服务。

讨论的结果是一个明确的下一步，以及判断它是否有效的方法。
如果需要修改代码，CEO 可以继续协助执行计划并检查结果。

## 兼容性与验证情况

| 安装方式 | 已验证 | 尚未验证 |
| --- | --- | --- |
| 旧版仅含核心技能的 Codex / Claude Code 插件 | macOS 上的安装、更新、卸载和技能发现 | 五技能布局的发现与模型调用；Windows/Linux 原生管理器 |
| 项目安装程序，三种应用 | Windows、Linux 和 macOS CI 中的文件生命周期 | 应用内技能调用 |
| APM 0.31.0 | macOS 上 CEO AI 0.2.0 的文件生命周期 | CEO AI 0.8.0 的安装示例 |

旧版仅含核心技能的插件使用 Codex CLI 0.147.0 和 Claude Code 2.1.232 检查。
这些结果不能证明当前源码中五个技能的发现与模型行为。
[验证结果与限制](docs/PLUGINS.md#验证范围) ·
[自动检查](https://github.com/bearatol/ceo-ai/actions/workflows/checks.yml)。

## 它如何协助你

- **讨论选择。** 询问可能改变决策的信息，解释反对理由，并在新证据出现时修正自己的建议。
- **安排工作。** 把大任务拆成清楚的步骤。如果应用支持其他 AI 助手，可以让一个负责实现，另一个检查结果。
- **检查具体问题。** 对代码，运行测试并核对需求；对文字，检查是否清楚、有无矛盾或缺乏依据的说法；
  对计划，检查遗漏步骤、依赖关系，以及选错方案后如何补救。
- **征求第二意见。** 在作出失败代价较高的决定前，请另一个 AI 助手寻找方案中的薄弱之处。
  审查在应用内进行，不会联系任何真人。

简单问题不应变成一次团队会议。如果无法启动其他 AI 助手，CEO 应明确说明，
不能把自己再检查一遍说成独立审查。

## 帮助与项目更新

如果安装停止或找不到技能，请先查看[安装帮助](docs/HELP.zh-CN.md)。
也可以[报告问题](https://github.com/bearatol/ceo-ai/issues/new/choose)。
更多信息：[更新与迁移记录（英文）](CHANGELOG.md)、[发布版本](https://github.com/bearatol/ceo-ai/releases)、
[贡献指南（英文）](CONTRIBUTING.md)和[私密漏洞报告（英文说明）](SECURITY.md)。

## 更新或卸载

请让助手用原来的安装方式更新或卸载 CEO AI，并提供[说明](INSTALL.md)。
删除 Codex 用户级插件会影响所有使用它的项目。删除项目技能也会影响共用该目录的 Cursor。
操作前必须保留本地修改。

CEO AI 使用你现有的模型和工具。AI 的回答需要核实，第二意见也可能出错。
CEO 不会获得额外权限，也不能替代项目要求的安全审查。

[开发与验证](docs/DEVELOPMENT.md) · [推广与目录状态](docs/DISTRIBUTION.md) ·
[CEO 工作流程](docs/CEO_GUIDE.md) · [MIT 许可证](LICENSE)

## 作者

[Telegram @bearatol](https://t.me/bearatol) · [LinkedIn](https://www.linkedin.com/in/mikhail-diesperov/)
