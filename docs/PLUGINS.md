# CEO AI plugin

[English](#english) · [Русский](#русский) · [简体中文](#简体中文)

## English

Install one plugin, `ceo-ai`, in Codex or Claude Code. It contains three skills:

| Skill | Use it for | Requirements |
| --- | --- | --- |
| `ceo-ai:ceo-ai` | Discuss decisions, coordinate work, check skills during indexing | Python 3.10+ and POSIX for the local indexing check |
| `ceo-ai:writer` | Draft and edit in your voice | No Docker; Python 3.10+ only for optional persistent memory |
| `ceo-ai:security-scan` | An explicitly requested additional local scan | Python 3.10+, POSIX, Docker and a prepared scanner image |

In Claude Code, prefix the skill name with `/`. Load a skill when its task is
needed. Installation does not run a scan, install Docker or enable memory.
The plugin registers no agents, hooks, MCP servers or extra permissions.
It uses your AI app; no CEO AI account or separate API key is needed.

### Install yourself

In a Claude Code conversation, run separately:

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

Choose project scope when prompted. Terminal equivalent, from your project:

```text
claude plugin marketplace add bearatol/ceo-ai
claude plugin install ceo-ai@ceo-ai-plugins --scope project
```

For Codex CLI versions with the `plugin` command:

```text
codex plugin marketplace add bearatol/ceo-ai --ref main
codex plugin add ceo-ai@ceo-ai-plugins
```

Use a reviewed snapshot following [INSTALL.md](../INSTALL.md). This combined
layout is a new change; older releases may contain only the core skill. Check the
selected snapshot rather than assuming a version label proves its contents.
Restart the conversation and select the relevant skill. Native managers use
user-level catalog/cache state, even when Claude enables a plugin for one project.

Cursor and strictly project-only installs keep using the project installer or
APM. Those routes currently provide the core skill only, not these additional
native skills. CEO AI is distributed through this repository's catalog, not the
official OpenAI or Anthropic directories.

### Optional CEO AI Security

Security Scan is included in the same plugin; running it is optional. Without
Docker, use the builtin indexing check. To prepare the extra scanner, follow the
[Docker walkthrough](DOCKER_SCAN.md). The current image recipe supports native
ARM64 Docker hosts with Buildx/BuildKit. Neither Docker nor the scanner image is
installed by the plugin. There is no cloud service or LLM/API call in the scanner.
See [coverage and costs](SECURITY_SCANNING.md).

### Writer

Select `ceo-ai:writer`. Start with: "Turn these notes into a post in my voice.
Keep the useful details and don't make it sound like an ad."
[Writing preferences](WRITER.md) explains optional memory and its controls.

### Update or remove

Claude Code:

```text
claude plugin marketplace update ceo-ai-plugins
claude plugin update ceo-ai@ceo-ai-plugins --scope project
```

Codex, for a Git-backed catalog:

```text
codex plugin marketplace upgrade ceo-ai-plugins
codex plugin add ceo-ai@ceo-ai-plugins
```

For a local catalog, keep using its reviewed local source and `plugin add`;
Git-only upgrade does not apply. Restart after updating. Use the same manager
and scope to uninstall `ceo-ai@ceo-ai-plugins`.

If you previously installed `ceo-ai-writer` or `ceo-ai-security`, first install
and verify the combined plugin. Then, with permission, remove only those old
registrations through their manager. Preserve local edits and private memory;
never delete cache folders or user preferences manually. See
[migration rules](../INSTALL.md#migration-between-installation-methods).

### What was checked

Package tests verify all three skill directories, exact resource lists, shared
runtime bytes and operation after relocation. Native package installation and
cached-file integrity can be checked separately from model invocation. Historical
macOS checks used Codex CLI 0.147.0 and Claude Code 2.1.232 for the earlier core-only
layout. They do not prove discovery or model behavior for this new layout on every
host. Windows/Linux CI checks packaging and the project installer. See
[development notes](DEVELOPMENT.md).

## Русский

Устанавливается один плагин `ceo-ai`. Внутри три навыка:

| Навык | Для чего | Что нужно |
| --- | --- | --- |
| `ceo-ai:ceo-ai` | Обсуждение задач, координация, проверка при индексации | Для локальной проверки Python 3.10+ и POSIX |
| `ceo-ai:writer` | Тексты и редактура в твоём стиле | Без Docker; Python нужен только для сохранения предпочтений |
| `ceo-ai:security-scan` | Дополнительная проверка по запросу | Python 3.10+, POSIX, Docker и подготовленный образ |

В Claude Code перед именем добавь `/`. Инструкции нужного навыка загружаются по
задаче. Установка не запускает сканирование, не ставит Docker и не включает память.
Плагин не регистрирует агентов, hooks, MCP-серверы или дополнительные права.

### Установка

В диалоге Claude Code выполни по очереди:

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

Выбери область проекта. В терминале из папки проекта можно выполнить:

```text
claude plugin marketplace add bearatol/ceo-ai
claude plugin install ceo-ai@ceo-ai-plugins --scope project
```

В Codex CLI с поддержкой плагинов:

```text
codex plugin marketplace add bearatol/ceo-ai --ref main
codex plugin add ceo-ai@ceo-ai-plugins
```

Сначала проверь выбранную сборку по [INSTALL.md](../INSTALL.md). Объединённый пакет
добавлен недавно: в старом выпуске может быть только основной навык. После
установки начни новый чат и выбери нужный скилл. Менеджер использует пользовательский
каталог и кэш, даже если Claude включает плагин только для проекта.

Для Cursor и установки строго внутри проекта остаются проектный установщик и
APM. Сейчас они ставят только основной навык, без дополнительных нативных скиллов.
Плагин доступен из каталога репозитория, а не официальных каталогов OpenAI и Anthropic.

### Опциональный CEO AI Security

Навык уже внутри плагина. Запуск дополнительного сканера остаётся добровольным.
Без Docker работает базовая проверка при индексации. Для дополнительной есть
[подготовка Docker по шагам](DOCKER_SCAN.ru.md): текущий рецепт рассчитан на
нативный ARM64 Docker-хост и Buildx/BuildKit. Образ готовится отдельно.
[Ограничения проверки и расходы](SECURITY_SCANNING.md).

### Writer

Выбери `ceo-ai:writer` и попроси: "Собери из заметок пост в моём стиле. Сохрани
полезные детали, без пафоса и рекламного нажима".
[Как управлять предпочтениями](WRITER.md#русский).

### Обновление и удаление

Для Claude Code:

```text
claude plugin marketplace update ceo-ai-plugins
claude plugin update ceo-ai@ceo-ai-plugins --scope project
```

Для Codex с Git-каталогом:

```text
codex plugin marketplace upgrade ceo-ai-plugins
codex plugin add ceo-ai@ceo-ai-plugins
```

Локальному каталогу Git-обновление не нужно: используй проверенный локальный
источник и `plugin add`. После обновления начни новый чат. Удаление выполняется
тем же менеджером для `ceo-ai@ceo-ai-plugins` и в прежней области установки.

Если стоят старые отдельные `ceo-ai-writer` или `ceo-ai-security`, сначала установи
и проверь единый пакет. Затем с согласия пользователя удали только старые
регистрации через менеджер. Личные правки и приватную память сохрани.
[Правила перехода](../INSTALL.md#migration-between-installation-methods).

### Что проверено

Тесты проверяют состав трёх скиллов, общие файлы и работу после перемещения.
Установка пакета, обнаружение навыков и ответ модели проверяются отдельно.
Прежние проверки Codex CLI 0.147.0 и Claude Code 2.1.232 на macOS относились к
пакету с одним навыком. Они не подтверждают работу нового состава во всех
приложениях. [Подробности](DEVELOPMENT.md).

## 简体中文

只需安装一个 `ceo-ai` 插件，其中包含三个技能：

| 技能 | 用途 | 要求 |
| --- | --- | --- |
| `ceo-ai:ceo-ai` | 讨论决策、协调任务、索引时检查 | 本地检查需要 Python 3.10+ 和 POSIX |
| `ceo-ai:writer` | 按你的风格写作和编辑 | 无需 Docker；持久偏好需要 Python |
| `ceo-ai:security-scan` | 按请求进行额外扫描 | Python、POSIX、Docker 和已准备的镜像 |

Claude Code 调用时在名称前加 `/`。按任务加载相应技能。安装不会启动扫描、
安装 Docker 或开启记忆，也不会注册代理、hooks、MCP 服务或新增权限。

### 安装

在 Claude Code 对话中依次运行，选择项目范围：

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

支持插件的 Codex CLI：

```text
codex plugin marketplace add bearatol/ceo-ai --ref main
codex plugin add ceo-ai@ceo-ai-plugins
```

先按 [INSTALL.md](../INSTALL.md) 审查所选快照。旧版本可能只有主技能。
安装后开启新对话。原生管理器会使用用户级目录和缓存。Cursor、项目安装器及
APM 目前仍只提供主技能，不包含另外两个原生技能。

### 可选 CEO AI Security

扫描技能已经包含在插件中，只有主动运行额外扫描才需要 Docker 和镜像。
没有 Docker 也可使用基础索引检查。参见 [ARM64 Docker 准备步骤](DOCKER_SCAN.zh-CN.md)
与[覆盖范围及成本](SECURITY_SCANNING.md)。

### Writer

选择 `ceo-ai:writer`，提供笔记并要求按你的风格整理，保留细节、避免营销腔。
[偏好和记忆管理](WRITER.md#简体中文)。

### 更新和卸载

Codex 的 Git 目录先运行 `codex plugin marketplace upgrade ceo-ai-plugins`，
再运行 `codex plugin add ceo-ai@ceo-ai-plugins`。本地目录只需审查本地来源后安装。
Claude Code 使用 `claude plugin marketplace update ceo-ai-plugins` 和
`claude plugin update ceo-ai@ceo-ai-plugins --scope project`。随后开启新对话。
通过原管理器及原范围卸载。若安装过独立的 Writer 或 Security，先验证统一插件，
再经同意移除旧注册，保留私有记忆和用户修改。

### 验证范围

测试覆盖三个技能的打包、文件完整性与迁移后运行。安装、技能发现与模型调用是
不同的检查；旧主技能的宿主测试不能证明新布局在所有平台均可使用。
[开发说明](DEVELOPMENT.md)。

## Platform references

[OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins)
and [Claude Code plugin documentation](https://code.claude.com/docs/en/discover-plugins).
