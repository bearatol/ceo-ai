# Install with Microsoft APM

[CEO AI website](https://bearatol.github.io/ceo-ai/) · [Work examples](https://bearatol.github.io/ceo-ai/#cases) · [Install](https://bearatol.github.io/ceo-ai/#install)

[English](#english) · [Русский](#русский) · [简体中文](#简体中文)

## English

Use this option if Microsoft APM is already installed. Otherwise, the
[agent-assisted installation](../README.md#get-started) needs no package manager.
Tell your agent:

> Install CEO AI in this project using my existing Microsoft APM. Follow https://github.com/bearatol/ceo-ai/blob/main/INSTALL.md.

For reference, the Codex command is:

```bash
apm install bearatol/ceo-ai#v0.9.0 --target codex
```

The documented test used APM 0.31.0 with CEO AI 0.2.0 on macOS. It does not
confirm the 0.9.0 example above. See the [test limits](#what-was-tested).

Use `--target claude` or `--target cursor` for those tools. This installs one
self-contained skill, `ceo-ai`, with its supporting files. APM itself manages
`apm.yml`, its lockfile/cache, and user-level state such as `~/.apm`.
Consult the [official APM instructions](https://microsoft.github.io/apm/consumer/install-packages/)
for package-manager setup and permissions.

Before the first install, stop if the target `ceo-ai` folder already exists and
is not managed by this APM project. For update or removal, ask your agent to
follow [INSTALL.md](../INSTALL.md). It must run `apm audit --ci --no-policy`
and the bundle check below before writing. Stop on local changes; `--frozen`
does not protect edits. Do not mix the Python and APM installers for one copy.

## Русский

Этот вариант подходит, если Microsoft APM уже установлен. Иначе воспользуйтесь
[установкой через агента](../README.ru.md#начать-пользоваться), менеджер пакетов
для неё не нужен. Напишите агенту:

> Установи CEO AI в этот проект через уже установленный Microsoft APM. Следуй инструкции https://github.com/bearatol/ceo-ai/blob/main/INSTALL.md.

Для справки, команда для Codex:

```bash
apm install bearatol/ceo-ai#v0.9.0 --target codex
```

APM 0.31.0 проверяли с CEO AI 0.2.0 на macOS. Эта историческая проверка не
подтверждает работу примера с версией 0.9.0 выше. См. [границы проверки](#what-was-tested).

Для Claude Code замените последний аргумент на `claude`, для Cursor на `cursor`.
APM установит один навык `ceo-ai` со всеми нужными файлами. Сам APM ведёт
`apm.yml`, файл версий, кэш и пользовательские настройки, в том числе `~/.apm`.
Установка и разрешения самого менеджера описаны в
[документации APM](https://microsoft.github.io/apm/consumer/install-packages/).

Если папка `ceo-ai` уже существует и не принадлежит этому проекту APM, сначала
разберите конфликт. Обновление и удаление поручите агенту по [инструкции](../INSTALL.md).
Перед изменениями нужны `apm audit --ci --no-policy` и проверка комплекта ниже.
Если файлы изменены, продолжать нельзя: `--frozen` не защищает ваши правки.
Используйте один способ установки для одной копии навыка.

## 简体中文

如果已经安装 Microsoft APM，可以使用此方式。否则请选择
[让智能体安装](../README.zh-CN.md#开始使用)，无需另装包管理器。向智能体发送：

> 请通过已安装的 Microsoft APM，在当前项目中安装 CEO AI。请遵循 https://github.com/bearatol/ceo-ai/blob/main/INSTALL.md 中的说明。

以下是 Codex 的参考命令：

```bash
apm install bearatol/ceo-ai#v0.9.0 --target codex
```

记录中的测试是在 macOS 上使用 APM 0.31.0 和 CEO AI 0.2.0 完成的，不能确认上方
0.9.0 示例是否可用。参见[测试范围](#what-was-tested)。

Claude Code 使用 `--target claude`，Cursor 使用 `--target cursor`。
APM 会安装一个包含所需资源的 `ceo-ai` 技能。APM 本身还管理 `apm.yml`、锁文件、缓存，
以及 `~/.apm` 等用户级状态。包管理器的安装与权限见
[APM 官方说明](https://microsoft.github.io/apm/consumer/install-packages/)。

首次安装时，如果目标 `ceo-ai` 文件夹已存在且不归当前 APM 项目管理，请先处理冲突。
更新或卸载请让智能体遵循[安装说明](../INSTALL.md)，写入前必须执行
`apm audit --ci --no-policy` 和下方的完整性检查。有本地修改时应停止，
`--frozen` 不会保护你的改动。不要对同一份技能混用两种安装方式。

## Agent verification and lifecycle

From a reviewed CEO AI release checkout, before APM update/removal:

```bash
python3 scripts/install.py check-package --project /approved/project --host codex
```

Substitute the actual host/project. Also audit APM's recorded deployment with
`apm audit --ci --no-policy` from the consumer project. The flag only skips
additional organization-policy evaluation for this content audit; it never
waives policies required by the user's organization. Run required policy checks
separately. Preserve conflicts and obtain a reviewed backup before changing the
installed version. APM removal can partially complete; inspect any error before
retrying and never clean up unrelated skills or manifests by hand.

For an approved update use the new explicit version reference in `apm install`.
For removal use `apm uninstall bearatol/ceo-ai`. Inspect APM's planned scope and
preserve dependencies belonging to other packages. Verify the resulting files.

Only a skill is deployed. The package has no lifecycle scripts, native agent
primitives, global rules, or MCP servers. Role prompts remain internal references.

## What was tested

APM 0.31.0 was tested with CEO AI 0.2.0 on macOS. This historical check does not
verify the 0.9.0 example above. APM was exercised through its Python CLI in
disposable Codex, Claude Code, and Cursor project layouts. The fixture relocates only APM's configuration and
lifecycle-lock destinations to temporary storage. The macOS sandbox blocks
network access and writes outside each fixture; `HOME` remains unchanged.
Organization-policy discovery is disabled only in these isolated fixtures,
which contain no organization policy. This does not test policy integration.
This tests local-package deployment and lifecycle, not GitHub downloads, ordinary
user-level APM setup, or model invocation inside the three applications.
