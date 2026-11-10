# Video Editor

[English](#english) · [Русский](#русский) · [简体中文](#简体中文)

## English

Use `ceo-ai:video-editor` to review footage, plan a cut, or revise and export an
edit. In Codex, select the skill after opening a new chat with the native
plugin. In Claude Code, invoke `/ceo-ai:video-editor`. Project and APM installs
provide the core CEO skill only. [Native plugin setup](PLUGINS.md#english).

### What to send

Share the source clips or existing project, the audience, platform, target
duration, aspect ratio and caption language. Tell the editor which phrases or
moments to keep. For critique, a transcript or stills can support a partial
review. Sound and motion need the corresponding media.

### Example prompts

- **Review.** “Review these clips for a 20-second salon promo. Give me timecoded
  notes on what to keep, fix in the edit or reshoot. Separate observations from
  recommendations.”
- **Edit.** “Make a 9:16 preview. Keep the pause after the joke, include editable
  captions in SRT, and keep the booking graphic clear of the subtitles. Let me
  review the cut before final export.”
- **Revise.** “Put the line at source 00:15–00:17 back. Keep the new caption
  placement. Show what changed, and check caption timing in the new version.”

### Tools and output

The skill checks the tools it can use in your project. FFmpeg and ffprobe can
handle straightforward cuts and media checks. A compatible HyperFrames or
Remotion setup can render motion graphics. An existing timed transcript or an
authorized transcription tool such as local Whisper can supply subtitle timing.
These tools are separate from the plugin. Installation and hosted media transfers
require your approval.

Review requests can return findings by timecode. Edit requests can return a cut
plan, preview, captions, and an export as the requested workflow and available
tools allow. If a required tool is unavailable, ask for the cut plan and the
specific missing prerequisite. Originals stay read-only. Transcript-based
revisions retain previous decisions so you can restore one cut in a new version.

[Read a fictional editing dialogue](DIALOGUE.md#video-editor).

## Русский

`ceo-ai:video-editor` помогает оценить исходники, спланировать монтаж,
внести правки и подготовить экспорт. В Codex откройте новый чат с нативным
плагином и выберите навык. В Claude Code вызовите `/ceo-ai:video-editor`.
Установка в проект и APM дают только основной навык CEO.
[Установка плагина](PLUGINS.md#русский).

### Что передать

Приложите исходные клипы или укажите существующий проект, аудиторию, площадку,
длительность, соотношение сторон и язык субтитров. Отметьте фразы и моменты,
которые нужно сохранить. Расшифровки или кадров хватит для частичного разбора.
Для оценки звука и движения нужны соответствующие материалы.

### Примеры запросов

- **Разбор.** «Посмотри эти клипы для 20-секундной рекламы салона. Отметь по
  таймкодам, что оставить, что поправить на монтаже и что переснять. Отдели
  наблюдения от рекомендаций».
- **Монтаж.** «Сделай превью 9:16. Оставь паузу после шутки, приложи
  редактируемые субтитры SRT и проверь, чтобы графика записи не перекрывала
  текст. Дай мне посмотреть монтаж до финального экспорта».
- **Правка.** «Верни реплику с 00:15–00:17 исходника. Сохрани новое положение
  субтитров. Покажи, что изменилось, и проверь синхронизацию в новой версии».

### Инструменты и результат

Навык проверяет, какие инструменты доступны в проекте. FFmpeg и ffprobe
подходят для простой нарезки и проверки файлов. Для анимации подойдёт
совместимый проект на HyperFrames или Remotion. Таймкоды для субтитров можно
взять из готовой расшифровки или получить разрешённым инструментом, например
локальным Whisper. Эти инструменты устанавливаются отдельно. Для установки
или передачи материалов в облачный сервис нужно ваше разрешение.

По запросу на разбор вы получите замечания с таймкодами. При монтаже результат
может включать план, превью, субтитры и экспорт в зависимости от задачи и
доступных инструментов. Если для рендера чего-то не хватает, попросите план
монтажа и название нужного инструмента. Исходники остаются доступными только
для чтения. Предыдущие решения в монтаже по расшифровке сохраняются, чтобы
можно было вернуть конкретную правку в новой версии.

[Вымышленный диалог о монтаже](DIALOGUE.ru.md#video-editor).

## 简体中文

使用 `ceo-ai:video-editor` 审查素材、规划剪辑、修改版本或导出成片。
在 Codex 中，用原生插件开启新会话并选择此技能。在 Claude Code 中，
调用 `/ceo-ai:video-editor`。项目安装和 APM 只提供核心 CEO 技能。
[原生插件安装](PLUGINS.md#简体中文)。

### 提供哪些信息

提供源视频或现有项目，说明受众、发布平台、目标时长、画面比例及字幕语言。
标出想保留的台词或画面。只有文字稿或静帧时，也可以做部分审查。
评估声音或动态画面需要相应素材。

### 提示词示例

- **审查。** “看看这些素材能否做成 20 秒的理发店宣传片。按时间码指出哪些可以
  保留、哪些能在后期修正、哪些需要补拍。请区分观察与建议。”
- **剪辑。** “做一版 9:16 预览。保留笑点后的停顿，提供可编辑的 SRT 字幕，
  并确保预约图示不遮挡字幕。最终导出前请让我确认。”
- **修改。** “恢复源素材 00:15–00:17 的台词，保留新的字幕位置。说明改动，
  并核对新版本的字幕同步。”

### 工具与交付

技能会检查项目可用的工具。FFmpeg 和 ffprobe 适合简单剪辑和媒体检查。
兼容的 HyperFrames 或 Remotion 环境可以渲染动态图形。可使用已有的带时间码
文字稿，或经授权使用本地 Whisper 等工具获取字幕时间。上述工具与插件分开安装。
安装工具或向云服务传输素材需要你的同意。

审查可以交付带时间码的意见。根据需求和工具，剪辑可以交付方案、预览、字幕和成片。
缺少渲染工具时，可以先要求剪辑方案，并请助手指出所缺工具。源文件保持只读。
按文字稿剪辑时会保留之前的决定，便于在新版本中撤回某一处剪辑。

[虚构剪辑对话](DIALOGUE.zh-CN.md#video-editor)。
