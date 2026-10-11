# CEO AI

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Not sure how to approach a task? Talk it through with an AI CEO.**

CEO AI helps an AI assistant examine decisions, challenge weak assumptions,
choose an approach, and coordinate work. You bring the goal and constraints.
CEO should explain its reasoning, revise its advice when evidence changes,
and keep the process proportional to the task.

The repository contains instructions and Python utilities. Your AI tool supplies
the model, permissions, and ability to launch subagents.

## What it does

- Discusses alternatives and challenges material errors, including its own.
- Keeps simple requests short; plans work when steps depend on one another.
- Checks available skills and agents. If something is missing, proposes a
  suitable installation or original component within your authorization.
- Assigns bounded tasks and checks evidence before accepting results.
- Uses behavior-first TDD for code and editorial or scenario checks for prose.
- Requests an independent mentor before consequential commitments.

## Try it without installation

Clone the repository. These commands work in macOS, Linux, and WSL:

```bash
mkdir -p "$HOME/proj"
git clone https://github.com/bearatol/ceo-ai.git "$HOME/proj/ceo-ai"
cd "$HOME/proj/ceo-ai"
```

Open that folder in your AI tool and send:

```text
Read CONNECT.md and apply skills/ceo/SKILL.md.
Use this checkout as the ecosystem root.
Help me choose an approach to this task: ...
My constraints and definition of success are: ...
```

For another project, provide the full checkout path and allow your tool to read
it. Opening the repository alone does not register skills or agents.

## Install in Codex, Claude Code, or Cursor

Keep the checkout: it holds the catalog, role prompts, and tools. Copy all seven
folders from `skills/` into **one** destination below, preserving each `SKILL.md`.
Compare existing folders before replacing anything.

| Tool | Personal skills | Skills for one project | Invoke |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/` | `.agents/skills/` | `$ceo` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | `/ceo` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` | `/ceo` in Agent chat |

Paths and invocation were checked on 2026-10-11 against the official
[Codex](https://developers.openai.com/codex/skills/),
[Claude Code](https://code.claude.com/docs/en/skills), and
[Cursor](https://cursor.com/docs/skills) documentation.
Here, Claude means **Claude Code**, not the claude.ai chat interface.

For a personal installation, run exactly one assignment:

```bash
ceo_skill_dir="$HOME/.agents/skills"   # Codex
```

```bash
ceo_skill_dir="$HOME/.claude/skills"   # Claude Code
```

```bash
ceo_skill_dir="$HOME/.cursor/skills"   # Cursor
```

Then run the following block from the `ceo-ai` checkout in the same Bash or Zsh
terminal. It checks all destinations before copying and stops on existing names.

```bash
(
  set -eu
  : "${ceo_skill_dir:?Choose a skill destination first}"
  test -f CONNECT.md
  test -f skills/ceo/SKILL.md
  for ceo_source in skills/*; do
    ceo_name=$(basename "$ceo_source")
    if [ -e "$ceo_skill_dir/$ceo_name" ] || [ -L "$ceo_skill_dir/$ceo_name" ]; then
      printf 'Already exists; compare manually: %s\n' "$ceo_skill_dir/$ceo_name" >&2
      exit 1
    fi
  done
  mkdir -p "$ceo_skill_dir"
  for ceo_source in skills/*; do
    cp -R "$ceo_source" "$ceo_skill_dir/"
  done
)
```

For project scope, set `ceo_skill_dir` to that project's full destination path
from the table instead. On native Windows, clone with Git and copy the same
folders with your file manager. `~` means your user home; project paths start
at the target repository. Avoid duplicate skills across directories your tool scans.

Start a new session. In Codex invoke `$ceo`; in Claude Code or Cursor use `/ceo`.
Then send this request, replacing the path placeholder:

```text
The CEO AI ecosystem root is <full path to the ceo-ai checkout>.
Read its CONNECT.md. Work on the current project.
Our goal is ...; the deadline is ...; success means ...
Challenge assumptions that could change the outcome.
```

Skill copies do not include the catalog. If you move the checkout, supply its new path.

## Use it day to day

For advice: “Compare these approaches. What am I assuming without evidence?”

For implementation: “Fix this bug. First reproduce it with a failing test,
then make the smallest change and check the result.”

For a costly decision: “Review this migration plan. Before we commit, have an
independent mentor examine the assumptions, rollback, and alternatives.”

Expect a recommendation or result, evidence, and material limits. CEO should
respect an informed preference and avoid reopening settled questions without
new evidence. State the budget, deadline, and permissions when they affect the choice.

## Subagents and the independent mentor

Installing skills enables the lead workflow. The four files in `agents/` are
portable prompts; named roles need separate native registration. Start with the
**CEO skill in the main conversation** and register specialists when needed.

| Tool | Project role file | Read-only mentor setting |
| --- | --- | --- |
| Codex | `.codex/agents/decision-mentor.toml` | `sandbox_mode = "read-only"` |
| Claude Code | `.claude/agents/decision-mentor.md` | `tools: Read, Glob, Grep` |
| Cursor | `.cursor/agents/decision-mentor.md` | `readonly: true` |

Create the file in the host's native format with name `decision-mentor`, a short
description, and the body from `agents/decision-mentor.md`. Include the approved
checkout path for reading the catalog, selected skills, and protocol. Codex puts
the body in `developer_instructions`; Claude Code and Cursor use Markdown below
YAML frontmatter. Follow the [Codex](https://developers.openai.com/codex/subagents/),
[Claude Code](https://code.claude.com/docs/en/sub-agents), or
[Cursor](https://cursor.com/docs/subagents) agent format.

Register `engineer` and `qa-reviewer` similarly if needed, granting only tools
required for assigned work and preserving each role's access limits. The separate
CEO **agent** is read-only and delegates writes. The CEO **skill** uses the main
assistant's existing permissions. Verify callable roles and actual restrictions
before delegation; a file's presence is not verification.

These settings are not a complete offline security sandbox. Independent security
review must satisfy your project's enforcement requirements. Mentor and QA cannot
replace it. Without subagents, CEO can advise and do permitted work, but must
disclose missing review and defer commitments that require it.

## Check the bundle

Run from the checkout with Python 3.10 or newer. No third-party packages are needed.

```bash
python3 tools/team/team.py --home . list --type agent
python3 scripts/catalog.py --pack . validate
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check.py
```

Bash users can also run `bash tests/test.sh` and `bash scripts/doctor.sh`.
These checks validate the bundle, not native agent registration or model behavior.

Optional POSIX inventory:

```bash
python3 scripts/ceo_inventory.py --home .
python3 scripts/ceo_inventory.py --home . --refresh
```

The first command reads metadata; the second writes an ignored cache when
authorized. Symlinks and unsupported layouts are refused. Native Windows and
other layouts need the host's approved discovery tools. Discovery does not
install or authorize a capability.

## Update, remove, or troubleshoot

Review upstream changes before using an update. In a clean checkout, run
`git pull --ff-only`, repeat the checks, then compare and update only your
installed skill copies and role definitions. Copies do not update automatically.
To uninstall, remove only those copies and definitions, preserving unrelated
files and local edits. Restart the tool afterward.

If `ceo` is missing, check the destination, `SKILL.md` filename, duplicate names,
and skill settings. If the catalog is missing, supply the checkout path. If a
role is unavailable, check its native registration and effective permissions.

## Contents and limits

Seven skills, four role prompts, task/result contracts, a packet utility, and
an optional inventory. See the [technical guide](docs/CEO_GUIDE.md),
[connection protocol](CONNECT.md), and [source provenance](docs/PROVENANCE.json).

Host permissions and mandatory reviews always apply. This bundle has no automatic
installer for missing capabilities or isolated security reviewer. Instructions
cannot grant access. Native integrations have not been exercised end to end in
all three products.

Selected planning and review practices were informed by Superpowers. Its prompts
are not bundled; comparative quality and cost savings have not been established.
Original source notices are retained in the [MIT license](LICENSE).
