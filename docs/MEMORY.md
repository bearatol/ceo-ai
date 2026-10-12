# Lessons and reusable patterns

[Website](https://bearatol.github.io/ceo-ai/#memory) · [English](#english) · [Русский](#русский) · [简体中文](#简体中文)

## English

CEO AI can retain verified lessons, design patterns and preferences between
sessions. This is optional context for the assistant. It does not train the model
or guarantee better results. Memory is off until you enable a specific scope.

Ask: **“Enable CEO AI memory for this project.”** The agent explains the exact
private location, what it will save and when it will read it. User preferences
across projects require separate permission. Retrieved records may be sent to the
model by your AI app. Nothing is uploaded by the memory helper itself.

Project records can describe a verified fix, an approved color palette, type
sizes, component states, mobile layouts or a working example. A pattern includes
where it fits, where it does not, a source, evidence and a review date. CEO checks
current files and established solutions before creating a new design. When there
is a real choice, it compares suitable options with sources and explains its
recommendation. Browsing requires the host's permitted network tools.

You can say:

- **“Show my CEO AI memory.”** Inspect the selected project or user scope.
- **“Correct this pattern” / “Delete this lesson.”** Change one record.
- **“Disable CEO AI memory.”** Stop automatic reading and saving in both scopes.
- **“Clear this project's CEO AI memory.”** Delete its records and leave it off.

Every save is announced with its title and scope. Disabling preserves records;
clearing removes them. Neither erases previous chats, provider logs, host memory
or backups. The agent must not recreate deleted lessons from the chat. Memory
needs file permissions and Python 3.10+; if unavailable, it remains off.

## Русский

CEO AI может сохранять проверенные уроки, шаблоны и предпочтения между сессиями.
Это дополнительный контекст для помощника. Веса модели не меняются, улучшение
результата не гарантируется. Память выключена до вашего согласия.

Скажите: **«Включи память CEO AI для этого проекта».** Агент покажет точное место
хранения и объяснит, что будет сохранять и читать. Общие предпочтения для разных
проектов требуют отдельного согласия. Прочитанные записи могут попасть в контекст
модели через ваше ИИ-приложение. Сама утилита памяти ничего не отправляет в сеть.

В памяти проекта можно хранить проверенное исправление, утверждённую палитру,
размеры шрифтов, состояния компонентов, мобильные варианты и пример применения.
У шаблона есть условия применения, ограничения, источник, подтверждение и дата
пересмотра. Перед новым решением CEO проверяет существующие компоненты и
подходящие практики. Если есть выбор, показывает варианты с источниками и
объясняет рекомендацию. Для поиска нужен разрешённый доступ к интернету.

Управление обычными сообщениями:

- **«Покажи память CEO AI».** Посмотреть записи проекта или пользователя.
- **«Исправь этот шаблон» / «Удали этот урок».** Изменить отдельную запись.
- **«Отключи память CEO AI».** Прекратить автоматическое чтение и сохранение в обеих областях.
- **«Очисти память CEO AI этого проекта».** Удалить его записи и оставить память выключенной.

После сохранения агент сообщает название записи и её область. Отключение
сохраняет записи, очистка удаляет их. Эти команды не удаляют прежние чаты, логи
провайдера, память приложения или резервные копии. Агент не должен восстанавливать
удалённые уроки из переписки. Нужны разрешение на файлы и Python 3.10+;
без них память остаётся выключенной.

## 简体中文

CEO AI 可以跨会话保留已验证的经验、模板和偏好。这些内容作为助手的补充上下文，
不会训练模型，也不保证结果更好。记忆默认关闭，只有获得明确同意后才会启用。

可以说：**“为这个项目启用 CEO AI 记忆。”** 助手会说明准确的存储位置、保存的内容
以及读取时机。跨项目的用户偏好需要单独授权。读取的记录可能通过 AI 应用进入模型
上下文；记忆工具本身不联网。

项目记忆可以保存已验证的修复、获批的配色、字号、组件状态、移动端布局和使用示例。
每个模板包含适用条件、限制、来源、验证依据和复查日期。提出新方案前，CEO 会检查
项目中已有的组件和适用实践。如果存在有意义的选择，会列出方案、来源和取舍，
并说明建议。网上搜索需要应用允许的网络工具。

用自然语言管理：

- **“显示我的 CEO AI 记忆。”** 查看项目或用户范围的记录。
- **“修改这个模板” / “删除这条经验。”** 更改单条记录。
- **“关闭 CEO AI 记忆。”** 停止两个范围的自动读取和保存。
- **“清空这个项目的 CEO AI 记忆。”** 删除该项目记录，并保持关闭。

每次保存后，助手会告知记录名称和范围。关闭会保留记录，清空会删除记录。
这些命令不会删除以前的聊天、提供商日志、应用记忆或备份。助手不得从聊天历史
重建已删除的记录。需要文件权限和 Python 3.10+；条件不满足时记忆保持关闭。

## Storage and verification

The helper uses Python's standard SQLite library in one `memory.sqlite3` file,
outside repositories and plugin caches. No server, network service, embeddings
or third-party dependency is installed. There is no automatic import of the
host's memory. A canonical project path defines identity; a move, clone or
separate worktree gets a new scope. Sharing or migration requires an explicit
request. The store is not encrypted. Windows privacy follows the selected
folder's ACLs; POSIX stores require user-only file and directory permissions.

SQLite transactions serialize cooperating writers. Opaque revision tokens reject stale
edits, including after an item is deleted and recreated. Each scope holds at most 200 records, the store at most 800 records and
100 scopes, each record at most 16 KiB. Recall returns up to five matching,
unexpired records. It is keyword retrieval, not semantic search. Use targeted
queries and verify current sources. Consent flags cannot authenticate a human:
the agent must ask first, and the host still controls file access.

Deleting one record preserves the scope’s enabled/disabled setting. Clearing a
scope removes all its records using SQLite secure deletion and leaves a disabled
scope marker; it does not silently re-enable collection. This is
not forensic erasure of backups, storage snapshots or previously transmitted data.
Do not place sensitive data, credentials or raw conversations in the store.

The [agent workflow](../.apm/skills/ceo-ai/references/skills/project-memory.md),
[record schema](../.apm/skills/ceo-ai/memory/record.schema.json) and
[synthetic design example](../.apm/skills/ceo-ai/memory/pattern.example.json)
are included in the package. Runtime consent, isolation and lifecycle checks are
automated. Instruction-following quality still depends on the host and model;
these checks do not prove that every agent follows the workflow.

Design values use the [DTCG 2025.10 format](https://www.designtokens.org/tr/2025.10/format/).
The storage choice uses [SQLite transactions](https://www.sqlite.org/atomiccommit.html)
and [secure deletion](https://www.sqlite.org/pragma.html#pragma_secure_delete).
Existing [Claude Code memory](https://code.claude.com/docs/en/memory) is a separate
host feature; CEO AI does not change its settings or promise to clear it.

Recognized hot rollback journals can be recovered after the helper verifies the
owned database schema. Unknown, orphan or active/incomplete sidecars are preserved
and refused. Wait for a known writer or request recovery review; do not delete
sidecars to force a command through.
