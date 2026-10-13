# CEO AI plugins

[English](#english) · [Русский](#русский) · [简体中文](#简体中文) · [Website](https://bearatol.github.io/ceo-ai/)

## English

CEO AI is available from this project's GitHub plugin catalog for Codex and
Claude Code. It is not listed in the official OpenAI or Anthropic directories.
The main `ceo-ai` plugin contains one skill and its supporting files. It does not register
agents, hooks, MCP servers or new permissions. Use your existing access to your
AI application; CEO AI has no separate account or API key.

The easiest route is to send your agent the installation message on the
[website](https://bearatol.github.io/ceo-ai/#install). It checks the app version,
existing installations and installation scope. Cursor keeps using the project
installer. If you need a strictly project-only installation in Codex, use that
installer too: Codex's plugin manager writes user-level configuration and cache.
Claude's marketplace also uses user-level state, even with project scope.

### Install yourself

In a Claude Code conversation, run these two commands separately:

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

Choose project scope when prompted. Restart the conversation and invoke
`/ceo-ai:ceo-ai`. The terminal equivalent, run from your project, is:

```text
claude plugin marketplace add bearatol/ceo-ai
claude plugin install ceo-ai@ceo-ai-plugins --scope project
```

For Codex CLI versions with the `plugin` command:

```text
codex plugin marketplace add bearatol/ceo-ai --ref main
codex plugin add ceo-ai@ceo-ai-plugins
```

Restart the app or conversation. Select `ceo-ai:ceo-ai` from the skill picker;
Codex reports that namespaced skill name. If the CLI command is unavailable,
use the project installer instead of changing configuration manually.

### Optional CEO AI Security

From version 0.6.0 the catalog also contains **CEO AI Security**, a separate opt-in
plugin with the skill `ceo-ai-security:security-scan`. Check that the reviewed catalog snapshot contains this module before
using the commands below; do not silently substitute a development build for a
stable release. Installing `ceo-ai` never installs the optional module.

Before installation, explain the requirements: Python 3.10+ on a POSIX host,
a Docker client and working daemon, and a separately prepared, reviewed immutable
NVIDIA SkillSpector image. The plugin supplies the adapter, not Docker or the
scanner image. It has no LLM/API calls or cloud service and works independently
of the main plugin. See [scan limits and costs](SECURITY_SCANNING.md).

With the approved catalog snapshot already registered, explicitly install only
the module requested by the user:

```text
codex plugin add ceo-ai-security@ceo-ai-plugins
```

Or, for Claude Code from the project:

```text
claude plugin install ceo-ai-security@ceo-ai-plugins --scope project
```

Start a new chat and select `ceo-ai-security:security-scan` in Codex or invoke
`/ceo-ai-security:security-scan` in Claude Code. Verify its own payload and discovery
separately. This module currently has only a native-plugin installation route;
the project installer and APM continue to install the core skill only. Without
Docker, keep using CEO AI's local indexing check. No optional scan runs on indexing.

### Update or remove

For Claude Code, from the project where you installed it:

```text
claude plugin marketplace update ceo-ai-plugins
claude plugin update ceo-ai@ceo-ai-plugins --scope project
```

For Codex:

```text
codex plugin marketplace upgrade ceo-ai-plugins
codex plugin add ceo-ai@ceo-ai-plugins
```

These commands refresh the tracked catalog and install its current version.
Restart afterward. To remove the plugin, use `claude plugin uninstall
ceo-ai@ceo-ai-plugins --scope project` or `codex plugin remove
ceo-ai@ceo-ai-plugins`. Removing a plugin does not necessarily remove its catalog.
Remove that separately through the same manager if you no longer use it.
For an explicitly installed optional module, use the same commands with
`ceo-ai-security@ceo-ai-plugins`. Updating or removing the main plugin does not
request installation or removal of the optional plugin.

### Already installed through an agent or APM?

Keep using your existing installation unless you want to switch. Ask your agent
to migrate it using [INSTALL.md](../INSTALL.md#migration-between-installation-methods).
Do not delete folders yourself. The agent must check ownership and local edits.
Codex and Cursor share `.agents/skills/ceo-ai`: removing it for Codex also removes
it for Cursor. If Cursor still needs it, keep the shared copy and use its
`$ceo-ai` entry in Codex, or explicitly choose the plugin's namespaced entry.
Avoid enabling two copies unintentionally. APM installations stay under APM's
control; this plugin does not adopt or remove them.

### What was checked

On macOS: Claude Code 2.1.232 and Codex CLI 0.147.0 installed the local catalog,
updated a test package from 0.4.0 to 0.4.1, and removed it. Both discovered one
skill. Claude reported zero agents, hooks, MCP and LSP servers. Package tests
also verify that the copied skill works from a separate cache path with spaces
and Unicode. These are packaging and discovery checks, not a behavior benchmark.
These historical host checks cover the main plugin. Native installation and
model invocation of the new optional module have not yet been verified.

Model invocation remains unverified: Claude Code had no authenticated session;
the Codex CLI's configured model was rejected by its ChatGPT provider before
the test could run. The Windows/Linux CI checks package integrity and the
project installer; native plugin managers and desktop UI flows on those systems
have not been tested. See [development notes](DEVELOPMENT.md).

## Русский

CEO AI можно установить плагином в Codex и Claude Code из каталога этого
GitHub-репозитория. В официальных каталогах OpenAI и Anthropic его пока нет.
В основном плагине `ceo-ai` один навык и справочные файлы. Плагин не регистрирует агентов, hooks,
MCP-серверы и дополнительные права. Нужен обычный доступ к вашему ИИ-приложению;
отдельного аккаунта или ключа CEO AI нет.

Проще всего отправить агенту сообщение с [сайта](https://bearatol.github.io/ceo-ai/ru/#install).
Он проверит версию приложения и старую установку. Для Cursor остаётся установка
в проект. Она также подходит для Codex, если всё должно храниться только в
проекте: менеджер плагинов Codex меняет пользовательские настройки и кэш.
Каталог Claude тоже хранится на уровне пользователя, даже при установке в проект.

### Установить самостоятельно

В чате Claude Code по очереди введите:

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

Выберите область проекта. Начните новый чат и вызовите `/ceo-ai:ceo-ai`.
В терминале из папки проекта доступны те же действия:

```text
claude plugin marketplace add bearatol/ceo-ai
claude plugin install ceo-ai@ceo-ai-plugins --scope project
```

Для Codex CLI с поддержкой команды `plugin`:

```text
codex plugin marketplace add bearatol/ceo-ai --ref main
codex plugin add ceo-ai@ceo-ai-plugins
```

Перезапустите приложение или чат. Выберите `ceo-ai:ceo-ai` в списке навыков.
Если команда `plugin` недоступна, используйте установщик для проекта.

### Опциональный CEO AI Security

Начиная с версии 0.6.0 в каталоге есть отдельный плагин **CEO AI Security** с навыком
`ceo-ai-security:security-scan`.
Сначала проверьте наличие модуля в одобренной копии каталога; не заменяйте стабильный
релиз сборкой для разработки без запроса пользователя. Установка `ceo-ai` не
устанавливает этот модуль.

До установки нужны Python 3.10+, POSIX-система, клиент и работающий демон Docker,
а для проверки — отдельно подготовленный и проверенный неизменяемый образ NVIDIA
SkillSpector. Плагин содержит адаптер, но не устанавливает Docker и образ.
Основной CEO AI ему не требуется. Облачного сервиса и вызовов LLM/API нет.
[Ограничения и затраты](SECURITY_SCANNING.md).

Когда одобренная копия каталога уже подключена, установите модуль явно:

```text
codex plugin add ceo-ai-security@ceo-ai-plugins
```

Либо для Claude Code, из папки проекта:

```text
claude plugin install ceo-ai-security@ceo-ai-plugins --scope project
```

Начните новый чат: в Codex выберите `ceo-ai-security:security-scan`, в Claude Code
вызовите `/ceo-ai-security:security-scan`. Проверяйте файлы и обнаружение этого
плагина отдельно. Модуль доступен только как нативный плагин; установщик в проект
и APM по-прежнему устанавливают только основной навык. Без Docker можно пользоваться
локальной проверкой CEO AI. Дополнительный сканер при индексации не запускается.

### Обновление и удаление

Claude Code, из проекта с установленным плагином:

```text
claude plugin marketplace update ceo-ai-plugins
claude plugin update ceo-ai@ceo-ai-plugins --scope project
```

Codex:

```text
codex plugin marketplace upgrade ceo-ai-plugins
codex plugin add ceo-ai@ceo-ai-plugins
```

Команды обновляют каталог и устанавливают его текущую версию. После этого
перезапустите чат. Для удаления: `claude plugin uninstall
ceo-ai@ceo-ai-plugins --scope project` или `codex plugin remove
ceo-ai@ceo-ai-plugins`. Сам каталог при этом может остаться. При необходимости
удалите его отдельно через тот же менеджер.
Для отдельно установленного модуля используйте те же команды с именем
`ceo-ai-security@ceo-ai-plugins`. Обновление или удаление основного плагина не
означает запрос на установку или удаление дополнительного.

### Если CEO AI уже установлен

Работающую установку можно оставить. Для перехода попросите агента следовать
[инструкции миграции](../INSTALL.md#migration-between-installation-methods).
Он проверит способ установки и сохранит ваши правки. У Codex и Cursor общая
папка `.agents/skills/ceo-ai`: удаление навыка для Codex затронет и Cursor.
Если навык нужен в Cursor, сохраните эту копию. В Codex используйте её `$ceo-ai`
либо явно выбирайте `ceo-ai:ceo-ai` из плагина. Не подключайте две копии случайно.
Установкой через APM продолжает управлять APM.

### Что проверено

На macOS проверены установка, обновление тестового пакета с 0.4.0 до 0.4.1 и
удаление через Claude Code 2.1.232 и Codex CLI 0.147.0. Оба приложения обнаружили
один навык. Claude показал ноль агентов, hooks, MCP- и LSP-серверов. Проверена
работа файлов навыка из отдельного кэша с пробелами и китайскими символами в пути.
Эти прежние проверки относятся к основному плагину. Установка нового модуля через
менеджеры и вызов модели с ним пока не проверены.

Ответ модели пока не проверен: в Claude Code не было авторизации, а провайдер
Codex CLI отклонил выбранную в настройках модель до запуска теста. CI на Windows
и Linux проверяет пакет и установщик для проекта. Работа менеджеров плагинов и
интерфейса приложений на этих ОС ещё не проверена. Это проверки установки и
обнаружения, а не качества решений CEO. [Подробности](DEVELOPMENT.md).

## 简体中文

CEO AI 可通过本 GitHub 仓库的插件目录安装到 Codex 和 Claude Code。
目前尚未上架 OpenAI 或 Anthropic 的官方目录。主插件 `ceo-ai` 包含一个技能及其参考文件，
不会注册代理、hooks、MCP 服务器或额外权限。使用现有 AI 应用的访问方式即可，
不需要单独的 CEO AI 账号或 API 密钥。

最简单的方法是把[网站上的安装消息](https://bearatol.github.io/ceo-ai/zh/#install)
发给助手。助手会检查应用版本和已有安装。Cursor 继续使用项目安装程序。
如果 Codex 的所有文件都必须留在项目内，也应选择项目安装程序。
Codex 插件管理器会写入用户级配置和缓存；Claude 的目录同样使用用户级状态，
即使插件选择了项目范围。

### 手动安装

在 Claude Code 对话中依次运行：

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

选择项目范围，重新开始对话，然后调用 `/ceo-ai:ceo-ai`。
也可以在项目目录的终端中运行：

```text
claude plugin marketplace add bearatol/ceo-ai
claude plugin install ceo-ai@ceo-ai-plugins --scope project
```

支持 `plugin` 命令的 Codex CLI：

```text
codex plugin marketplace add bearatol/ceo-ai --ref main
codex plugin add ceo-ai@ceo-ai-plugins
```

重启应用或对话，在技能列表中选择 `ceo-ai:ceo-ai`。
如果没有 `plugin` 命令，请使用项目安装程序。

### 可选 CEO AI Security

从 0.6.0 版本起，目录还包含独立的 **CEO AI Security** 插件，技能名为
`ceo-ai-security:security-scan`。请先确认经过审查的
目录快照包含此模块；未经用户要求，不要用开发版本替代稳定版本。
安装 `ceo-ai` 不会同时安装该模块。

安装前应说明要求：POSIX 系统上的 Python 3.10+、Docker 客户端及运行中的守护进程，
以及单独准备并审查的不可变 NVIDIA SkillSpector 镜像。插件提供适配器，
不会安装 Docker 或镜像，也不依赖主插件。没有云服务或 LLM/API 调用。
参见[扫描限制与成本](SECURITY_SCANNING.md)。

注册已批准的目录快照后，单独安装用户请求的模块：

```text
codex plugin add ceo-ai-security@ceo-ai-plugins
```

Claude Code 则在项目目录中运行：

```text
claude plugin install ceo-ai-security@ceo-ai-plugins --scope project
```

开启新会话，在 Codex 中选择 `ceo-ai-security:security-scan`，或在 Claude Code 中
调用 `/ceo-ai-security:security-scan`。单独验证模块文件及技能发现。
目前仅支持原生插件安装；项目安装程序和 APM 仍只安装主技能。没有 Docker 时，
仍可使用 CEO AI 的本地索引检查；索引不会自动启动额外扫描。

### 更新和卸载

Claude Code，在安装插件的项目目录中运行：

```text
claude plugin marketplace update ceo-ai-plugins
claude plugin update ceo-ai@ceo-ai-plugins --scope project
```

Codex：

```text
codex plugin marketplace upgrade ceo-ai-plugins
codex plugin add ceo-ai@ceo-ai-plugins
```

这些命令会刷新目录并安装其当前版本，随后请重启对话。
卸载使用 `claude plugin uninstall ceo-ai@ceo-ai-plugins --scope project`
或 `codex plugin remove ceo-ai@ceo-ai-plugins`。
目录本身可能仍然保留；如不再使用，可通过同一管理器单独移除。
对于单独安装的可选模块，使用相同命令并将名称改为
`ceo-ai-security@ceo-ai-plugins`。更新或移除主插件不表示用户要求安装或移除可选插件。

### 已有安装

可以继续使用现有安装。需要迁移时，让助手按照
[迁移说明](../INSTALL.md#migration-between-installation-methods)检查所有权和本地修改。
不要自行删除目录。Codex 和 Cursor 共用 `.agents/skills/ceo-ai`，
为 Codex 删除它也会影响 Cursor。如果 Cursor 仍需要该技能，请保留这份安装。
在 Codex 中使用原有的 `$ceo-ai`，或明确选择插件的 `ceo-ai:ceo-ai`，避免误用重复副本。
通过 APM 安装的文件仍由 APM 管理。

### 验证范围

已在 macOS 上使用 Claude Code 2.1.232 和 Codex CLI 0.147.0 验证安装、
测试包从 0.4.0 到 0.4.1 的更新以及卸载。两者都发现一个技能。
Claude 报告零个代理、hooks、MCP 和 LSP 服务器。还测试了将技能移动到
含空格和中文字符的独立缓存目录后使用其文件。
上述历史检查仅覆盖主插件。新可选模块的原生安装和模型调用尚未验证。

尚未验证模型调用：Claude Code 未登录，Codex CLI 的提供方在测试开始前
拒绝了当前配置的模型。Windows 和 Linux CI 验证包内容及项目安装程序；
尚未测试这些系统上的原生插件管理器和桌面界面。
这些结果仅证明安装和发现流程，不代表 CEO 决策质量。[详细说明](DEVELOPMENT.md)。

## Platform references

Formats and catalog behavior follow the [OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins)
and [Claude Code plugin documentation](https://code.claude.com/docs/en/discover-plugins).
The tested CLI versions and outcomes above come from this project's local checks.
