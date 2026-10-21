# CEO AI Writer

Fictional writing scene: [English](DIALOGUE.md#writer) | [Русский](DIALOGUE.ru.md#writer) | [简体中文](DIALOGUE.zh-CN.md#writer).

## English

`writer` drafts, edits and translates in your voice. It uses plain language
and normal keyboard punctuation without stripping useful detail or inventing
personal experience. It avoids sales pressure and decorative formatting by
default. Your instructions and approved examples take precedence.

Writer is included in the single `ceo-ai` plugin. Follow [plugin installation](PLUGINS.md#english),
start a new chat and select `ceo-ai:writer` in Codex or `/ceo-ai:writer` in Claude Code.
No second plugin or Docker setup is needed. Python 3.10+ is needed only for persistent
preferences. The project installer and APM currently provide only the core skill.

It is not a separate subscription or a background service. Host model usage
still consumes tokens.

Try: "Use writer to turn these notes into a post in my voice. Keep the
technical details, use normal quotes, and don't make it sound like an ad."

Corrections take effect in the current chat. Learning between chats uses
[CEO AI memory](MEMORY.md), initially off. Enable a specific private location and
scope before saving preferences. Saves are announced. The skill keeps short rules
with context and evidence, not whole conversations or drafts, and does not train
model weights. Local records can enter your AI app's model context.

Ask to show, correct or forget your writing preferences. Writer-only stop/reset
needs a scoped review of the relevant records; the helper has no independent
writer-only switch. Disabling all CEO memory is available immediately through the
existing command. Neither operation deletes past chats or provider logs. Without
persistent storage, corrections are available only in the current conversation.

No personal profile ships in the plugin. The included examples are synthetic.
The skill does not publish for you or promise to bypass AI detectors; follow the
destination's disclosure requirements.

## Русский

`writer` пишет, редактирует и переводит с учётом вашего стиля. Обычные слова,
кавычки `"..."`, дефис `-` и многоточие `...`. Без рекламного нажима, выдуманных
историй и потери полезных деталей. Это предпочтения по умолчанию, их можно менять.

Writer уже внутри единственного плагина `ceo-ai`. После [установки плагина](PLUGINS.md#русский)
начни новый чат и выбери `ceo-ai:writer` в Codex или `/ceo-ai:writer` в Claude Code.
Второй плагин и Docker не нужны. Python 3.10+ нужен только для сохранения предпочтений.
Проектный установщик и APM сейчас предоставляют только основной навык.

Пример: "Собери из этих заметок пост в моём стиле. Без пафоса и призывов купить.
Технические подробности сохрани. Используй writer."

Правки учитываются сразу в чате. Для обучения между чатами нужно включить
[память CEO AI](MEMORY.md#русский) для конкретного приватного места и области.
Агент сообщает о сохранении коротких правил. Полные тексты и переписки не
сохраняет в профиль, веса модели не меняет. Локальные записи могут попасть в
контекст модели вашего приложения.

Можно посмотреть, исправить или удалить предпочтения. Для остановки или сброса
только профиля письма агент сначала уточняет набор записей: отдельного постоянного
выключателя для writer в общей памяти пока нет. Команда отключения всей памяти
CEO AI уже есть. Личные примеры в публичный пакет не попадают; встроенные примеры
вымышленные. Скилл сам ничего не публикует.

## 简体中文

`writer` 根据你的写作风格起草、编辑和翻译。默认使用普通键盘标点，
避免夸张营销和多余装饰，同时保留技术细节，不编造个人经历。

Writer 包含在唯一的 `ceo-ai` 插件中。[安装插件](PLUGINS.md#简体中文)后开启新对话，
在 Codex 中选择 `ceo-ai:writer`，或在 Claude Code 中调用 `/ceo-ai:writer`。
无需第二个插件或 Docker。持久偏好需要 Python 3.10+。
项目安装器和 APM 目前只提供主技能。

当前对话会立即采用你的修改。跨对话学习使用默认关闭的
[CEO AI 记忆](MEMORY.md#简体中文)，需要先批准私有存储位置和范围。
只保存简短偏好及其适用场景，不保存完整草稿或聊天，不训练模型权重。
读取的记录可能进入应用的模型上下文。每次保存都会告知你。

可以查看、修改或删除偏好。仅停止或重置写作偏好需要先确定相关记录；
共享记忆尚无独立的 writer 开关。可以使用已有命令关闭全部 CEO AI 记忆。
插件不包含个人资料；示例为虚构内容。此技能不会自行发布文章。
