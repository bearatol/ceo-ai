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

## What the plugin contains and runs

The plugin contains only skills: Markdown instructions, JSON schemas and
templates, readable Python 3.10+ scripts that use the standard library, and
one small Bash wrapper.
It registers no hooks, MCP servers, agents, commands or extra permissions, and
installation runs nothing.

Skills may ask Claude to run these bundled scripts with your host's normal
permissions:

- `ceo-ai/scripts/ceo_inventory.py` and `ceo_inventory_windows.py` read
  metadata of skills and agents in folders you approve, without executing the
  code they find. A refresh writes only its own cache, when you authorize it.
- `ceo-ai/scripts/catalog.py` validates the bundled component catalog without
  executing component code.
- `ceo-ai/scripts/ceo_security.py` and the copies in `security/scripts/`
  make static, text-only observations of an already captured snapshot.
- `ceo-ai/tools/team/team.py` and its `team.sh` wrapper list the bundled roles
  and agents, build task and plan packets and validate task and result JSON.
  With `--output`, they write that JSON to the path you give, replacing an
  existing file there.
- `security/scripts/ceo_security_nvidia.py` is an optional adapter for scanning
  skill packages with NVIDIA SkillSpector. It runs only when you request it, and
  only with Docker and a reviewed, digest-pinned image you have already
  installed, and talks only to the local Docker socket. It copies a read-only
  snapshot of the package into a temporary folder in the workspace you approve,
  then starts the container with no network access, a read-only file system
  and all capabilities dropped. The plugin installs neither Docker nor the
  image.

The bundled scripts make no network requests and send no data to any service.
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
