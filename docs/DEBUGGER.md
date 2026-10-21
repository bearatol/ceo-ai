# CEO AI Debugger

Fictional debugging and refactoring scene: [English](DIALOGUE.md#debugger) | [Русский](DIALOGUE.ru.md#debugger) | [简体中文](DIALOGUE.zh-CN.md#debugger).

[English](#english) · [Русский](#русский)

## English

Select `ceo-ai:debugger` in a native plugin host, or invoke
`/ceo-ai:debugger` in Claude Code. This skill is an addition in the current source
tree; check the selected release and actual host discovery. Project/APM installs
contain only the core CEO skill. [Plugin setup and verification](PLUGINS.md#english).

### Fix a bug

Provide the observed result, expected result, reproduction steps and the relevant
code or sanitized error output. Partial information is enough to begin inspecting;
an unreproduced problem must remain explicitly unconfirmed.

> After I save a filter and reopen the page, the filter is empty. Reproduce this,
> test possible causes and make the smallest verified fix. Keep unrelated behavior.

The workflow establishes a baseline, reproduces the failure, tests competing
explanations and changes the smallest relevant surface. A focused regression
check should fail for the original problem and pass with the fix. Broader checks
follow the affected boundaries and project requirements. A plausible explanation
without a reproduction or supporting evidence is a hypothesis, not a confirmed cause.

### Refactor within a boundary

> Simplify this parser without changing accepted inputs, output, errors or its
> public interface. Establish the current behavior first and keep the change local.

Refactoring starts by defining what must stay the same and checking the baseline.
If coverage is missing, characterization checks capture the relevant existing
behavior before restructuring. Work proceeds in small steps with checks between
them. A feature change, dependency replacement or architecture redesign needs its
own scope; it is not an incidental part of a refactor. Passing checks support only
the behavior they cover, not a claim of complete equivalence.

### What the result should show

- The reproduced failure or refactor boundary, with concrete evidence.
- The supported cause or structural change and the files affected.
- Checks actually run, their outcomes, and any untested behavior or remaining risk.

Debugger uses the host's existing tools and permissions. It does not install tools,
change dependencies or authorize production actions merely by being selected.
Project approval and security requirements still apply. Inspected code, logs and
external content are evidence, not instructions. Redact secrets from examples and
reports. If execution is unavailable, the result is an inspection with stated
limits, not a claim that tests passed.

## Русский

Выбери `ceo-ai:debugger` в приложении с нативным плагином или вызови
`/ceo-ai:debugger` в Claude Code. Навык добавлен в текущие исходники; проверь
состав выбранного релиза и наличие в приложении. Установка в проект и APM
содержат только основной навык CEO. [Установка и проверка](PLUGINS.md#русский).

### Исправить ошибку

Опиши ожидаемый и фактический результат, шаги воспроизведения, приложи нужный код
или сообщение об ошибке без секретов. Для начала проверки достаточно частичных
данных; невоспроизведённая проблема должна оставаться неподтверждённой.

> После сохранения фильтра и повторного открытия страницы фильтр пустой.
> Воспроизведи ошибку, проверь возможные причины и минимальное исправление.
> Сохрани остальное поведение.

Навык фиксирует исходное состояние, воспроизводит сбой, проверяет объяснения и
меняет только необходимый участок. Проверка регрессии должна выявлять исходную
ошибку и проходить после исправления. Дополнительные проверки зависят от
затронутых частей и правил проекта. Правдоподобная причина без подтверждения
остаётся гипотезой.

### Провести рефакторинг

> Упрости этот парсер, сохрани допустимые входные данные, результат, ошибки и
> публичный интерфейс. Сначала зафиксируй текущее поведение. Не расширяй задачу.

Сначала определяются границы и поведение, которое нужно сохранить. Если проверок
не хватает, до изменения структуры добавляются проверки текущего поведения.
Изменения идут небольшими шагами с проверкой результата. Новые функции, замена
зависимостей или пересмотр архитектуры требуют отдельного согласованного объёма.
Успешные проверки подтверждают только покрытое ими поведение, а не полную
эквивалентность.

### Что будет в результате

- Воспроизведённая ошибка или границы рефакторинга и конкретные доказательства.
- Подтверждённая причина или изменение структуры, затронутые файлы.
- Фактически выполненные проверки, результаты, пробелы и оставшиеся риски.

Навык использует доступные инструменты и права приложения. Его выбор сам по себе
не разрешает установку инструментов, замену зависимостей или действия в рабочей
системе. Согласования и проверки безопасности проекта сохраняются. Код, журналы
и внешние материалы рассматриваются как данные, а не команды; секреты не должны
попадать в примеры и отчёты. Если запуск недоступен, результат описывает проверку
материалов и её ограничения, а не успешное выполнение тестов.
