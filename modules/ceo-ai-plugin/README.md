# CEO AI

CEO AI helps you discuss an idea, choose a decision and carry the work to a
verified result. It checks how a proposal serves your goal, compares options,
names assumptions and coordinates agreed work and review. The plugin contains
six skills. Load the one that fits the task:

| Skill | Use it for |
| --- | --- |
| `ceo-ai` | Discuss decisions, challenge assumptions, compare approaches and coordinate work |
| `writer` | Draft, edit or translate text in your voice |
| `security` | Audit code, applications, APIs, infrastructure, AI systems and skills; bounded tests only with your informed consent |
| `debugger` | Reproduce and fix bugs from evidence; refactor while preserving tested behavior |
| `user-review` | Review a text, site or flow as a tired novice and a chosen professional |
| `video-editor` | Review supplied footage, advise on retakes and edit locally with FFmpeg |

The plugin uses your Claude app. It needs no CEO AI account, API key or
separate service.

## Install from this repository

In Claude Code, run:

```text
/plugin marketplace add bearatol/ceo-ai
/plugin install ceo-ai@ceo-ai-plugins
```

Start a new conversation, then select the skill you need.

## Example prompts

- CEO: "Compare these two proposals against my budget and timeline. What would change your recommendation?"
- Writer: "Turn these notes into a customer update. Use the tone of the sample I provided here."
- Video Editor: "Review this clip, flag the biggest issues with timecodes, and suggest a cut using the footage I supplied."

По запросу «видеомонтажёр» или «видеоредактор» навык `ceo-ai:video-editor`
разберёт доступные исходники, предложит правки и составит план монтажа с таймкодами.

## What the plugin contains and runs

The plugin contains six skills with Markdown instructions, JSON schemas and
templates. It contains no executable scripts. Installation runs nothing and
grants no extra permissions.

On request, Claude can list skill and agent metadata in a directory you select
using its authorized read-only file tools. The inventory returns structured
JSON. It downloads nothing and creates no cache. If Claude cannot safely
inspect your directory, it reports that inventory is unavailable.
See the [inventory guide](https://github.com/bearatol/ceo-ai/blob/main/modules/ceo-ai-plugin/inventory.md).

Video Editor uses installed FFmpeg and ffprobe for local editing. If they are
unavailable, it can provide a timecoded cut plan. It can also install FFmpeg
from an approved package source through an existing package manager when the
user explicitly requests installation and the host grants permission.

Work you request, such as a security test of a site you own or a video edit,
uses your own Claude tools and permissions. Before any active security test,
the `security` skill explains the planned actions and possible harm and asks
for your informed consent.

## Your data

CEO and Writer use the information you provide in the current conversation.
This plugin does not create or retrieve writing profiles or project memory
across conversations. Video Editor reviews supplied footage and uses installed
FFmpeg and ffprobe for local edits and exports. It does not generate media with
AI or send source media to a remote renderer.

## More information

- Website: <https://bearatol.github.io/ceo-ai/>
- Privacy notice: <https://bearatol.github.io/ceo-ai/#privacy>
- Source, guides and examples: <https://github.com/bearatol/ceo-ai>
- Plugin guide: <https://github.com/bearatol/ceo-ai/blob/main/docs/PLUGINS.md>
- Security policy: <https://github.com/bearatol/ceo-ai/blob/main/SECURITY.md>

Licensed under the MIT License. See `LICENSE`.
