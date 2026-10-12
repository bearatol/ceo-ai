# CEO AI plugins

[English](#english) · [Русский](#русский) · [简体中文](#简体中文) · [Website](https://bearatol.github.io/ceo-ai/)

## English

CEO AI is available from this project's GitHub plugin catalog for Codex and
Claude Code. It is not listed in the official OpenAI or Anthropic directories.
The plugin contains one skill and its supporting files. It does not register
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

Model invocation remains unverified: Claude Code had no authenticated session;
the Codex CLI's configured model was rejected by its ChatGPT provider before
the test could run. The Windows/Linux CI checks package integrity and the
project installer; native plugin managers and desktop UI flows on those systems
have not been tested. See [development notes](DEVELOPMENT.md).

## Русский

CEO AI можно установить плагином в Codex и Claude Code из каталога этого
GitHub-репозитория. В официальных каталогах OpenAI и Anthropic его пока нет.
Внутри один навык и справочные файлы. Плагин не регистрирует агентов, hooks,
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

Ответ модели пока не проверен: в Claude Code не было авторизации, а провайдер
Codex CLI отклонил выбранную в настройках модель до запуска теста. CI на Windows
и Linux проверяет пакет и установщик для проекта. Работа менеджеров плагинов и
интерфейса приложений на этих ОС ещё не проверена. Это проверки установки и
обнаружения, а не качества решений CEO. [Подробности](DEVELOPMENT.md).

## 简体中文

CEO AI 可通过本 GitHub 仓库的插件目录安装到 Codex 和 Claude Code。
目前尚未上架 OpenAI 或 Anthropic 的官方目录。插件包含一个技能及其参考文件，
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

尚未验证模型调用：Claude Code 未登录，Codex CLI 的提供方在测试开始前
拒绝了当前配置的模型。Windows 和 Linux CI 验证包内容及项目安装程序；
尚未测试这些系统上的原生插件管理器和桌面界面。
这些结果仅证明安装和发现流程，不代表 CEO 决策质量。[详细说明](DEVELOPMENT.md)。

## Platform references

Formats and catalog behavior follow the [OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins)
and [Claude Code plugin documentation](https://code.claude.com/docs/en/discover-plugins).
The tested CLI versions and outcomes above come from this project's local checks.
