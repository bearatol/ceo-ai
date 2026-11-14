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

### Engagement, pacing and retakes

A review looks for a delayed opening, repetition, missing examples, monotonous
delivery and a promise the video never fulfills. It leads with up to three
prioritized recommendations, each with a timecode, an observation, its likely
viewer effect and a concrete edit or targeted retake. A targeted retake is
recommended when the needed performance or material cannot be recovered
acceptably in editing. A static shot alone is no reason to reshoot. A full reshoot
is recommended only when a problem affects the whole take and localized fixes
are inadequate.

Pacing follows the audience, content and format. A demonstration, reaction or new
idea can develop within one continuous shot. There is no universal rule to cut
every three seconds and no guarantee of better retention. Without viewer data,
engagement assessments remain editorial hypotheses.

### Example prompts

- **Review.** “Review these clips for a 20-second salon promo. Give me timecoded
  notes on what to keep, fix in the edit or reshoot. Separate observations from
  recommendations.”
- **Edit.** “Make a 9:16 preview. Keep the pause after the joke, include editable
  captions in SRT, and keep the booking graphic clear of the subtitles. Let me
  review the cut before final export.”
- **Revise.** “Put the line at source 00:15–00:17 back. Keep the new caption
  placement. Show what changed, and check caption timing in the new version.”
- **Engagement.** "Review where this lesson loses momentum. Give up to three
  priorities with timecodes, observations, likely effects and specific edits or
  targeted retakes. Preserve the time needed to understand each demonstration."

### Evidence and sources

- [Cutting et al. (2011), "Quicker, faster, darker"](https://pmc.ncbi.nlm.nih.gov/articles/PMC3485803/)
  studied 160 films from 1935-2010. Average shot duration fell below four seconds
  after 2000. This describes the sample, not an optimal cut interval, a television
  or physiological rule, or proof of improved retention.
- [Adobe's editing guidance](https://www.adobe.com/creativecloud/video/discover/edit-a-video.html)
  puts emotion and story before rhythm in Walter Murch's rule and recommends
  comparing cuts. Faster or slower pacing can work or fail depending on the scene.
  This is professional craft guidance, not an experiment.
- [TikTok Creative Codes](https://ads.tiktok.com/business/en/blog/creative-best-practices-top-performing-ads)
  recommends a hook, body and close, with motion, transitions and text as attention
  tools. This is advertising guidance, not a universal frequency or a rule for all
  formats.
- [YouTube's audience-retention guide](https://support.google.com/youtube/answer/9314415?hl=en)
  helps locate openings, dips and top moments to inspect. Spikes can indicate
  interest or rewatching because content is unclear. The chart alone does not
  establish the cause.

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

### Интерес, темп и пересъёмка

При разборе навык ищет затянутое начало, повторы, нехватку примеров, монотонную
подачу и обещание, которое ролик не выполняет. Сначала навык даёт до трёх
приоритетных рекомендаций. В каждой есть таймкод, наблюдение, вероятное влияние
на зрителя и конкретная монтажная правка или точечная пересъёмка. Переснять
фрагмент стоит, если нужную подачу или материал нельзя приемлемо восстановить
на монтаже. Неподвижный план сам по себе не повод для пересъёмки. Полная
пересъёмка нужна только тогда, когда проблема затрагивает весь дубль и локальных
правок недостаточно.

Темп зависит от аудитории, содержания и формата. Демонстрация, реакция или новая
мысль могут развиваться внутри одного непрерывного плана. Универсального правила
склейки каждые три секунды и гарантии роста удержания нет. Без данных о зрителях
оценка вовлечённости остаётся редакторской гипотезой.

### Примеры запросов

- **Разбор.** «Посмотри эти клипы для 20-секундной рекламы салона. Отметь по
  таймкодам, что оставить, что поправить на монтаже и что переснять. Отдели
  наблюдения от рекомендаций».
- **Монтаж.** «Сделай превью 9:16. Оставь паузу после шутки, приложи
  редактируемые субтитры SRT и проверь, чтобы графика записи не перекрывала
  текст. Дай мне посмотреть монтаж до финального экспорта».
- **Правка.** «Верни реплику с 00:15–00:17 исходника. Сохрани новое положение
  субтитров. Покажи, что изменилось, и проверь синхронизацию в новой версии».
- **Интерес зрителя.** "Посмотри, где этот урок теряет темп. Дай до трёх
  приоритетов с таймкодами, наблюдениями, вероятным влиянием на зрителя и
  конкретными правками или точечной пересъёмкой. Сохрани время на понимание
  каждой демонстрации."

### Исследования и рекомендации

- [Cutting et al. (2011), "Quicker, faster, darker"](https://pmc.ncbi.nlm.nih.gov/articles/PMC3485803/)
  изучили 160 фильмов за 1935-2010 годы. После 2000 года средняя длительность
  монтажного плана опустилась ниже четырёх секунд. Это описание выборки, а не оптимальный
  интервал склейки, правило для телевидения, физиологическое правило или доказательство
  роста удержания.
- [Рекомендации Adobe по монтажу](https://www.adobe.com/creativecloud/video/discover/edit-a-video.html)
  ставят эмоцию и историю выше ритма в правиле Уолтера Мёрча и предлагают
  сравнивать варианты склеек. Быстрый и медленный темп могут работать или мешать
  в зависимости от сцены. Это профессиональные рекомендации, а не эксперимент.
- [TikTok Creative Codes](https://ads.tiktok.com/business/en/blog/creative-best-practices-top-performing-ads)
  предлагают структуру из зацепки, основной части и завершения, а также движение,
  переходы и текст для привлечения внимания. Это рекомендации для рекламы, а не
  универсальная частота изменений или правило для всех форматов.
- [Руководство YouTube по удержанию аудитории](https://support.google.com/youtube/answer/9314415?hl=en)
  помогает найти начало, провалы и популярные моменты для разбора. Пики могут
  означать интерес или повторный просмотр из-за непонятного содержания.
  Сам график не устанавливает причину.

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

### 吸引力、节奏与补拍

审查会寻找开场迟迟未进入重点、信息重复、缺少例子、表达单调和未兑现的承诺。
结果先列出最多三项优先建议，每项包含时间码、观察、对观众的可能影响，以及具体
剪辑方案或局部补拍方案。只有所需的表演或素材无法通过剪辑得到可接受的结果时，
才建议局部补拍。静止镜头本身不是补拍的理由。只有问题影响整段拍摄且局部修正
不足时，才建议全部重拍。

节奏取决于受众、内容和形式。演示、反应或新观点也可以在一个连续镜头中发展。
没有每三秒必须切换镜头的通用规则，也不能保证提升留存率。没有观众数据时，
吸引力评估仍是编辑判断，有待验证。

### 提示词示例

- **审查。** “看看这些素材能否做成 20 秒的理发店宣传片。按时间码指出哪些可以
  保留、哪些能在后期修正、哪些需要补拍。请区分观察与建议。”
- **剪辑。** “做一版 9:16 预览。保留笑点后的停顿，提供可编辑的 SRT 字幕，
  并确保预约图示不遮挡字幕。最终导出前请让我确认。”
- **修改。** “恢复源素材 00:15–00:17 的台词，保留新的字幕位置。说明改动，
  并核对新版本的字幕同步。”
- **吸引力。** “检查这节课在哪里失去节奏。按优先级提出最多三项建议，包含时间码、
  观察、可能影响和具体剪辑或局部补拍方案。保留理解每个演示所需的时间。”

### 研究与建议

- [Cutting et al. (2011), "Quicker, faster, darker"](https://pmc.ncbi.nlm.nih.gov/articles/PMC3485803/)
  研究了 1935-2010 年间的 160 部电影。2000 年后，平均镜头时长降至四秒以下。
  这是对样本的描述，不能确定最佳切镜间隔，也不是电视或生理规律，更不能证明
  更快的剪辑能提高留存率。
- [Adobe 剪辑指南](https://www.adobe.com/creativecloud/video/discover/edit-a-video.html)
  引用 Walter Murch 的规则，将情感和故事排在节奏之前，并建议比较不同剪辑。
  快节奏和慢节奏都可能有效或失效，取决于场景。这是专业经验指导，不是实验。
- [TikTok Creative Codes](https://ads.tiktok.com/business/en/blog/creative-best-practices-top-performing-ads)
  建议采用开场吸引、主体、结尾的结构，并用动作、转场和文字吸引注意。
  这是广告建议，不是通用的变化频率，也不适用于所有形式。
- [YouTube 观众留存指南](https://support.google.com/youtube/answer/9314415?hl=en)
  帮助定位开场、下降区间和热门片段，以便进一步审查。峰值可能意味着观众感兴趣，
  也可能是内容不清楚而需要重看。单凭图表不能确定原因。

### 工具与交付

技能会检查项目可用的工具。FFmpeg 和 ffprobe 适合简单剪辑和媒体检查。
兼容的 HyperFrames 或 Remotion 环境可以渲染动态图形。可使用已有的带时间码
文字稿，或经授权使用本地 Whisper 等工具获取字幕时间。上述工具与插件分开安装。
安装工具或向云服务传输素材需要你的同意。

审查可以交付带时间码的意见。根据需求和工具，剪辑可以交付方案、预览、字幕和成片。
缺少渲染工具时，可以先要求剪辑方案，并请助手指出所缺工具。源文件保持只读。
按文字稿剪辑时会保留之前的决定，便于在新版本中撤回某一处剪辑。

[虚构剪辑对话](DIALOGUE.zh-CN.md#video-editor)。
